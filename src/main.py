"""
Vigilo - Loop Principal
Agente de monitoramento leve para VPS e Containers Docker
"""

import time
import logging
import sys
import signal
from datetime import datetime
from typing import Optional

from config import config
from system_mon import SystemMonitor
from docker_mon import DockerMonitor
from notifier import Notifier
from heartbeat import Heartbeat


# Configuração de logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class VigiloAgent:
    """Classe principal do agente Vigilo"""
    
    def __init__(self):
        """Inicializa o agente com todos os monitores"""
        logger.info("=" * 60)
        logger.info("🚀 Iniciando Vigilo Agent")
        logger.info("=" * 60)
        
        # Inicializa monitores
        self.system_monitor = SystemMonitor(
            cpu_threshold=config.CPU_THRESHOLD,
            ram_threshold=config.RAM_THRESHOLD,
            disk_threshold=config.DISK_THRESHOLD
        )
        
        self.docker_monitor = DockerMonitor(
            watch_containers=config.WATCH_CONTAINERS
        )
        
        self.notifier = Notifier(
            evolution_url=config.EVOLUTION_URL,
            evolution_token=config.EVOLUTION_TOKEN,
            evolution_instance=config.EVOLUTION_INSTANCE,
            notify_number=config.NOTIFY_NUMBER,
            cooldown_seconds=config.ALERT_COOLDOWN
        )
        
        self.heartbeat = Heartbeat(
            webhook_url=config.N8N_HEARTBEAT_URL
        )
        
        # Controle de execução
        self.running = True
        self.last_report_time = time.time()
        self.check_count = 0
        
        # Registra handlers para shutdown gracioso
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Configuração: Checagem a cada {config.CHECK_INTERVAL}s")
        logger.info(f"Relatórios a cada {config.REPORT_HOURS}h")
        logger.info(f"Containers monitorados: {config.WATCH_CONTAINERS or 'Nenhum'}")
        
        # Testa conexões
        self._test_connections()
        
        # Envia notificação de startup
        self._send_startup_notifications()
    
    def _signal_handler(self, signum, frame):
        """
        Handler para sinais de interrupção (Ctrl+C, SIGTERM)
        
        Args:
            signum: Número do sinal
            frame: Frame atual
        """
        logger.info(f"\n⚠️ Sinal {signum} recebido. Encerrando graciosamente...")
        self.running = False
    
    def _test_connections(self) -> None:
        """Testa todas as conexões externas"""
        logger.info("Testando conexões...")
        
        # Testa Evolution API
        if self.notifier.test_connection():
            logger.info("✅ Evolution API: Conectado")
        else:
            logger.warning("⚠️ Evolution API: Falha na conexão")
        
        # Testa n8n Webhook
        if self.heartbeat.test_connection():
            logger.info("✅ n8n Webhook: Conectado")
        else:
            logger.warning("⚠️ n8n Webhook: Falha na conexão")
        
        # Testa Docker
        if self.docker_monitor.is_connected():
            logger.info("✅ Docker: Conectado")
        else:
            logger.error("❌ Docker: NÃO conectado - Verifique o socket!")
    
    def _send_startup_notifications(self) -> None:
        """Envia notificações de inicialização"""
        hostname = self.heartbeat.hostname
        
        # Notifica via WhatsApp
        self.notifier.send_startup_notification(hostname)
        
        # Envia evento de startup para n8n
        self.heartbeat.send_startup_event()
    
    def _should_send_report(self) -> bool:
        """
        Verifica se é hora de enviar relatório periódico
        
        Returns:
            True se deve enviar relatório
        """
        current_time = time.time()
        time_since_last_report = current_time - self.last_report_time
        report_interval = config.get_report_interval()
        
        return time_since_last_report >= report_interval
    
    def _generate_full_report(self, system_stats: dict) -> str:
        """
        Gera um relatório completo do sistema
        
        Args:
            system_stats: Estatísticas do sistema
            
        Returns:
            Relatório formatado
        """
        # Relatório do sistema
        system_report = self.system_monitor.get_formatted_report(system_stats)
        
        # Relatório do Docker
        docker_report = self.docker_monitor.get_docker_summary()
        
        # Estatísticas do agente
        heartbeat_stats = self.heartbeat.get_stats()
        agent_info = f"""
📡 *Status do Agente*
✅ Checagens realizadas: {self.check_count}
📤 Heartbeats enviados: {heartbeat_stats['total_sent']}
❌ Falhas heartbeat: {heartbeat_stats['total_failed']}
📊 Taxa de sucesso: {heartbeat_stats['success_rate']}%
"""
        
        full_report = f"{system_report}\n\n{docker_report}\n{agent_info}"
        
        return full_report
    
    def _process_alerts(self, system_alerts: list, docker_alerts: list) -> None:
        """
        Processa e envia alertas detectados
        
        Args:
            system_alerts: Lista de alertas do sistema
            docker_alerts: Lista de alertas do Docker
        """
        all_alerts = system_alerts + docker_alerts
        
        if not all_alerts:
            return
        
        logger.warning(f"⚠️ Detectados {len(all_alerts)} alertas")
        
        # Envia alertas via WhatsApp
        sent_count = self.notifier.send_alerts(all_alerts)
        logger.info(f"📱 {sent_count}/{len(all_alerts)} alertas enviados via WhatsApp")
        
        # Notifica n8n sobre os alertas
        alert_types = [alert.get("type", "UNKNOWN") for alert in all_alerts]
        self.heartbeat.send_alert_event(len(all_alerts), alert_types)
    
    def _perform_check(self) -> None:
        """Realiza uma checagem completa do sistema"""
        try:
            self.check_count += 1
            logger.info(f"🔍 Checagem #{self.check_count}")
            
            # 1. Coleta estatísticas do sistema
            system_stats = self.system_monitor.get_system_stats()
            
            # 2. Verifica limiares do sistema
            system_alerts = self.system_monitor.check_thresholds(system_stats)
            
            # 3. Verifica containers Docker
            docker_alerts = self.docker_monitor.check_watched_containers()
            
            # 4. Processa alertas
            if system_alerts or docker_alerts:
                self._process_alerts(system_alerts, docker_alerts)
            else:
                logger.info("✅ Sistema OK - Nenhum alerta")
            
            # 5. Envia heartbeat para n8n
            self.heartbeat.send(stats=system_stats)
            
            # 6. Verifica se deve enviar relatório periódico
            if self._should_send_report():
                logger.info("📊 Enviando relatório periódico...")
                report = self._generate_full_report(system_stats)
                
                if self.notifier.send_report(report):
                    logger.info("✅ Relatório enviado com sucesso")
                    self.last_report_time = time.time()
                else:
                    logger.warning("⚠️ Falha ao enviar relatório")
            
        except Exception as e:
            logger.error(f"❌ Erro durante checagem: {e}", exc_info=True)
    
    def run(self) -> None:
        """Loop principal do agente"""
        logger.info("✅ Vigilo Agent iniciado. Entrando no loop de monitoramento...")
        logger.info("Pressione Ctrl+C para encerrar")
        logger.info("=" * 60)
        
        while self.running:
            try:
                # Realiza checagem
                self._perform_check()
                
                # Aguarda próximo ciclo
                logger.debug(f"⏳ Aguardando {config.CHECK_INTERVAL}s até próxima checagem...")
                time.sleep(config.CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                # Já tratado pelo signal handler
                break
                
            except Exception as e:
                # Qualquer erro não esperado: loga e continua
                logger.error(f"❌ Erro crítico no loop principal: {e}", exc_info=True)
                logger.info("🔄 Tentando continuar após 30 segundos...")
                time.sleep(30)
        
        self._shutdown()
    
    def _shutdown(self) -> None:
        """Procedimento de shutdown gracioso"""
        logger.info("=" * 60)
        logger.info("🛑 Encerrando Vigilo Agent")
        logger.info("=" * 60)
        
        try:
            # Envia notificação de shutdown
            hostname = self.heartbeat.hostname
            shutdown_msg = f"🛑 *Vigilo Encerrado*\n\n🖥️ Host: {hostname}\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n📊 Checagens realizadas: {self.check_count}"
            self.notifier.send_message(shutdown_msg, force=True)
            
            # Envia evento para n8n
            self.heartbeat.send_event("shutdown", {
                "message": "Vigilo Agent encerrado",
                "checks_performed": self.check_count
            })
            
        except Exception as e:
            logger.error(f"Erro durante shutdown: {e}")
        
        logger.info("👋 Shutdown completo. Até logo!")


def main():
    """Função principal"""
    try:
        agent = VigiloAgent()
        agent.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"❌ Erro fatal ao iniciar agente: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

