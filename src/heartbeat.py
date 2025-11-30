"""
Módulo de Heartbeat (Sinal de Vida)
Envia sinais periódicos para n8n para garantir que o agente está vivo
"""

import requests
import time
import socket
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Heartbeat:
    """Classe para gerenciar envio de heartbeats para n8n"""
    
    def __init__(self, webhook_url: str, timeout: int = 10):
        """
        Inicializa o sistema de heartbeat
        
        Args:
            webhook_url: URL do webhook n8n
            timeout: Timeout para requisições em segundos
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.hostname = self._get_hostname()
        self.consecutive_failures = 0
        self.total_sent = 0
        self.total_failed = 0
        
        logger.info(f"Heartbeat configurado para {webhook_url}")
    
    def _get_hostname(self) -> str:
        """
        Obtém o hostname da máquina
        
        Returns:
            Nome do host
        """
        try:
            return socket.gethostname()
        except:
            return "unknown_host"
    
    def _build_payload(self, stats: Optional[Dict[str, Any]] = None, 
                       extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Constrói o payload do heartbeat
        
        Args:
            stats: Estatísticas do sistema (opcional)
            extra_data: Dados adicionais para incluir (opcional)
            
        Returns:
            Payload formatado para n8n
        """
        payload = {
            "agent_name": self.hostname,
            "status": "alive",
            "timestamp": int(time.time()),
            "consecutive_failures": self.consecutive_failures,
            "total_sent": self.total_sent,
            "total_failed": self.total_failed
        }
        
        # Adiciona estatísticas se fornecidas
        if stats:
            # Extrai apenas informações resumidas
            payload["stats"] = {
                "cpu_percent": stats.get("cpu_percent", 0),
                "ram_percent": stats.get("ram_percent", 0),
                "disk_percent": stats.get("disk_percent", 0),
                "uptime_seconds": stats.get("uptime_seconds", 0)
            }
        
        # Adiciona dados extras se fornecidos
        if extra_data:
            payload.update(extra_data)
        
        return payload
    
    def send(self, stats: Optional[Dict[str, Any]] = None, 
             extra_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envia um heartbeat para o n8n
        
        Args:
            stats: Estatísticas do sistema (opcional)
            extra_data: Dados adicionais (opcional)
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            payload = self._build_payload(stats, extra_data)
            
            logger.debug(f"Enviando heartbeat para n8n: {self.hostname}")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201, 204]:
                logger.debug("Heartbeat enviado com sucesso")
                self.total_sent += 1
                self.consecutive_failures = 0
                return True
            else:
                logger.warning(
                    f"Heartbeat retornou status {response.status_code}: {response.text[:100]}"
                )
                self._handle_failure()
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout ao enviar heartbeat para n8n (>{self.timeout}s)")
            self._handle_failure()
            return False
            
        except requests.exceptions.ConnectionError:
            logger.warning("Erro de conexão ao enviar heartbeat para n8n")
            self._handle_failure()
            return False
            
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar heartbeat: {e}")
            self._handle_failure()
            return False
    
    def _handle_failure(self) -> None:
        """Registra uma falha no envio de heartbeat"""
        self.consecutive_failures += 1
        self.total_failed += 1
        
        # Log mais visível se muitas falhas consecutivas
        if self.consecutive_failures >= 5:
            logger.error(
                f"⚠️ {self.consecutive_failures} falhas consecutivas ao enviar heartbeat!"
            )
        elif self.consecutive_failures >= 3:
            logger.warning(
                f"⚠️ {self.consecutive_failures} falhas consecutivas ao enviar heartbeat"
            )
    
    def send_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Envia um evento específico para o n8n
        
        Args:
            event_type: Tipo do evento (ex: "startup", "shutdown", "alert")
            event_data: Dados do evento
            
        Returns:
            True se enviado com sucesso
        """
        extra_data = {
            "event_type": event_type,
            "event_data": event_data
        }
        
        return self.send(extra_data=extra_data)
    
    def send_startup_event(self) -> bool:
        """
        Envia evento de inicialização do agente
        
        Returns:
            True se enviado com sucesso
        """
        return self.send_event("startup", {
            "message": "Vigilo Agent iniciado",
            "hostname": self.hostname
        })
    
    def send_alert_event(self, alert_count: int, alert_types: list) -> bool:
        """
        Envia evento quando alertas são gerados
        
        Args:
            alert_count: Número de alertas
            alert_types: Lista de tipos de alerta
            
        Returns:
            True se enviado com sucesso
        """
        return self.send_event("alerts_generated", {
            "alert_count": alert_count,
            "alert_types": alert_types
        })
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o webhook n8n
        
        Returns:
            True se conectado, False caso contrário
        """
        test_payload = {
            "agent_name": self.hostname,
            "status": "test",
            "timestamp": int(time.time())
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info("Conexão com n8n webhook OK")
                return True
            else:
                logger.warning(f"n8n webhook respondeu com status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão com n8n: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do heartbeat
        
        Returns:
            Dicionário com estatísticas
        """
        success_rate = 0
        total_attempts = self.total_sent + self.total_failed
        
        if total_attempts > 0:
            success_rate = (self.total_sent / total_attempts) * 100
        
        return {
            "hostname": self.hostname,
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": round(success_rate, 2)
        }

