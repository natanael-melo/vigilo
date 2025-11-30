"""
Módulo de Notificações via Evolution API (WhatsApp)
Implementa envio de alertas com sistema anti-spam (cooldown)
"""

import requests
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """Classe para gerenciar envio de notificações via Evolution API"""
    
    def __init__(self, evolution_url: str, evolution_token: str, 
                 evolution_instance: str, notify_number: str,
                 cooldown_seconds: int = 1800):
        """
        Inicializa o notificador
        
        Args:
            evolution_url: URL base da Evolution API
            evolution_token: Token de autenticação
            evolution_instance: Nome da instância
            notify_number: Número do WhatsApp para receber alertas
            cooldown_seconds: Tempo de cooldown em segundos (padrão: 1800 = 30 min)
        """
        self.evolution_url = evolution_url.rstrip('/')
        self.evolution_token = evolution_token
        self.evolution_instance = evolution_instance
        self.notify_number = notify_number
        self.cooldown_seconds = cooldown_seconds
        
        # Dicionário para rastrear últimos envios de cada tipo de alerta
        # Formato: {"alert_type": timestamp_ultimo_envio}
        self._last_alert_sent: Dict[str, float] = {}
        
        logger.info(f"Notificador iniciado para {notify_number} via instância {evolution_instance}")
    
    def _build_headers(self) -> Dict[str, str]:
        """Constrói headers para requisição à Evolution API"""
        return {
            "Content-Type": "application/json",
            "apikey": self.evolution_token
        }
    
    def _build_payload(self, message: str) -> Dict[str, Any]:
        """
        Constrói payload para envio de mensagem
        
        Args:
            message: Texto da mensagem
            
        Returns:
            Payload formatado para Evolution API
        """
        return {
            "number": self.notify_number,
            "text": message,
            "options": {
                "delay": 1200,  # Delay de 1.2s para simular digitação
                "presence": "composing"  # Mostra "digitando..."
            }
        }
    
    def _can_send_alert(self, alert_type: str) -> bool:
        """
        Verifica se pode enviar alerta baseado no cooldown
        
        Args:
            alert_type: Tipo do alerta (ex: "CPU_CRITICAL", "CONTAINER_DOWN")
            
        Returns:
            True se pode enviar, False se está em cooldown
        """
        current_time = time.time()
        
        if alert_type not in self._last_alert_sent:
            return True
        
        time_since_last = current_time - self._last_alert_sent[alert_type]
        
        if time_since_last >= self.cooldown_seconds:
            return True
        
        remaining = int(self.cooldown_seconds - time_since_last)
        logger.info(f"Alerta '{alert_type}' em cooldown. Faltam {remaining}s")
        return False
    
    def _mark_alert_sent(self, alert_type: str) -> None:
        """
        Marca um alerta como enviado
        
        Args:
            alert_type: Tipo do alerta
        """
        self._last_alert_sent[alert_type] = time.time()
    
    def send_message(self, message: str, force: bool = False, 
                     alert_type: Optional[str] = None) -> bool:
        """
        Envia uma mensagem via Evolution API
        
        Args:
            message: Texto da mensagem
            force: Se True, ignora o cooldown
            alert_type: Tipo do alerta (para controle de cooldown)
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        # Verifica cooldown se não for forçado e se tiver tipo de alerta
        if not force and alert_type:
            if not self._can_send_alert(alert_type):
                logger.debug(f"Mensagem não enviada (cooldown): {alert_type}")
                return False
        
        try:
            url = f"{self.evolution_url}/message/sendText/{self.evolution_instance}"
            headers = self._build_headers()
            payload = self._build_payload(message)
            
            logger.debug(f"Enviando mensagem para {self.notify_number}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Mensagem enviada com sucesso: {alert_type or 'generic'}")
                
                # Marca como enviado apenas se houver tipo de alerta
                if alert_type:
                    self._mark_alert_sent(alert_type)
                
                return True
            else:
                logger.error(f"Erro ao enviar mensagem. Status: {response.status_code}, Resposta: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout ao enviar mensagem para Evolution API")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Erro de conexão com Evolution API")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem: {e}")
            return False
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Envia um alerta específico
        
        Args:
            alert: Dicionário com informações do alerta
            
        Returns:
            True se enviado, False caso contrário
        """
        alert_type = alert.get("type", "UNKNOWN")
        message = alert.get("message", "Alerta sem mensagem")
        
        # Adiciona timestamp ao alerta
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        formatted_message = f"⚠️ *ALERTA VIGILO* ⚠️\n\n{message}\n\n🕒 {timestamp}"
        
        return self.send_message(formatted_message, alert_type=alert_type)
    
    def send_alerts(self, alerts: list) -> int:
        """
        Envia múltiplos alertas
        
        Args:
            alerts: Lista de alertas
            
        Returns:
            Número de alertas enviados com sucesso
        """
        sent_count = 0
        
        for alert in alerts:
            if self.send_alert(alert):
                sent_count += 1
                # Pequeno delay entre mensagens para não sobrecarregar
                time.sleep(1)
        
        return sent_count
    
    def send_report(self, report_text: str) -> bool:
        """
        Envia um relatório periódico (sempre envia, sem cooldown)
        
        Args:
            report_text: Texto do relatório
            
        Returns:
            True se enviado, False caso contrário
        """
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        formatted_message = f"📊 *RELATÓRIO VIGILO*\n\n{report_text}\n\n🕒 {timestamp}"
        
        # Relatórios são sempre enviados (force=True)
        return self.send_message(formatted_message, force=True)
    
    def send_startup_notification(self, hostname: str) -> bool:
        """
        Envia notificação de inicialização do agente
        
        Args:
            hostname: Nome do host
            
        Returns:
            True se enviado, False caso contrário
        """
        message = f"✅ *Vigilo Iniciado*\n\n🖥️ Host: {hostname}\n🕒 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        return self.send_message(message, force=True)
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com a Evolution API
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            # Tenta fazer uma requisição simples para verificar conectividade
            url = f"{self.evolution_url}/instance/connectionState/{self.evolution_instance}"
            headers = self._build_headers()
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                logger.info("Conexão com Evolution API OK")
                return True
            else:
                logger.warning(f"Evolution API respondeu com status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão com Evolution API: {e}")
            return False
    
    def get_cooldown_status(self) -> Dict[str, str]:
        """
        Retorna o status de cooldown de todos os alertas
        
        Returns:
            Dicionário com tempo restante de cooldown para cada tipo
        """
        current_time = time.time()
        status = {}
        
        for alert_type, last_sent in self._last_alert_sent.items():
            time_since = current_time - last_sent
            
            if time_since < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - time_since)
                status[alert_type] = f"{remaining}s restantes"
            else:
                status[alert_type] = "Pronto para enviar"
        
        return status

