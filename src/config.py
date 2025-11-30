"""
Módulo de Configuração do Vigilo
Gerencia variáveis de ambiente com validação
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()


class Config:
    """Classe centralizada para gerenciar configurações do Vigilo"""
    
    def __init__(self):
        # Configurações da Evolution API (WhatsApp)
        self.EVOLUTION_URL: str = self._get_required_env("EVOLUTION_URL")
        self.EVOLUTION_TOKEN: str = self._get_required_env("EVOLUTION_TOKEN")
        self.EVOLUTION_INSTANCE: str = self._get_required_env("EVOLUTION_INSTANCE")
        self.NOTIFY_NUMBER: str = self._get_required_env("NOTIFY_NUMBER")
        
        # Configuração do n8n Heartbeat
        self.N8N_HEARTBEAT_URL: str = self._get_required_env("N8N_HEARTBEAT_URL")
        
        # Configurações de Temporização
        self.CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "60"))
        self.REPORT_HOURS: int = int(os.getenv("REPORT_HOURS", "4"))
        
        # Timezone
        self.TZ: str = os.getenv("TZ", "America/Sao_Paulo")
        
        # Containers para monitoramento prioritário
        watch_containers_str: str = os.getenv("WATCH_CONTAINERS", "")
        self.WATCH_CONTAINERS: List[str] = [
            c.strip() for c in watch_containers_str.split(",") if c.strip()
        ]
        
        # Limiares de alerta para recursos do host
        self.CPU_THRESHOLD: float = float(os.getenv("CPU_THRESHOLD", "85.0"))
        self.RAM_THRESHOLD: float = float(os.getenv("RAM_THRESHOLD", "90.0"))
        self.DISK_THRESHOLD: float = float(os.getenv("DISK_THRESHOLD", "90.0"))
        
        # Configuração de Cooldown para anti-spam (em segundos)
        self.ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", "1800"))  # 30 minutos
        
        # Log Level
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """
        Obtém uma variável de ambiente obrigatória
        
        Args:
            key: Nome da variável de ambiente
            
        Returns:
            Valor da variável
            
        Raises:
            ValueError: Se a variável não estiver definida
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Variável de ambiente obrigatória '{key}' não está definida. "
                f"Por favor, configure-a no arquivo .env ou nas variáveis de ambiente do container."
            )
        return value
    
    def _validate_config(self) -> None:
        """Valida as configurações carregadas"""
        # Valida URL do n8n
        if not self.N8N_HEARTBEAT_URL.startswith(("http://", "https://")):
            raise ValueError("N8N_HEARTBEAT_URL deve começar com http:// ou https://")
        
        # Valida URL da Evolution API
        if not self.EVOLUTION_URL.startswith(("http://", "https://")):
            raise ValueError("EVOLUTION_URL deve começar com http:// ou https://")
        
        # Valida intervalos
        if self.CHECK_INTERVAL < 10:
            raise ValueError("CHECK_INTERVAL deve ser no mínimo 10 segundos")
        
        if self.REPORT_HOURS < 1:
            raise ValueError("REPORT_HOURS deve ser no mínimo 1 hora")
        
        # Valida limiares
        if not (0 < self.CPU_THRESHOLD <= 100):
            raise ValueError("CPU_THRESHOLD deve estar entre 0 e 100")
        
        if not (0 < self.RAM_THRESHOLD <= 100):
            raise ValueError("RAM_THRESHOLD deve estar entre 0 e 100")
        
        if not (0 < self.DISK_THRESHOLD <= 100):
            raise ValueError("DISK_THRESHOLD deve estar entre 0 e 100")
    
    def get_report_interval(self) -> int:
        """Retorna o intervalo de relatório em segundos"""
        return self.REPORT_HOURS * 3600
    
    def __repr__(self) -> str:
        """Representação segura da configuração (sem expor tokens)"""
        return (
            f"Config(CHECK_INTERVAL={self.CHECK_INTERVAL}, "
            f"REPORT_HOURS={self.REPORT_HOURS}, "
            f"WATCH_CONTAINERS={self.WATCH_CONTAINERS}, "
            f"TZ={self.TZ})"
        )


# Instância global de configuração
config = Config()

