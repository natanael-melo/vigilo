"""
Módulo de Monitoramento de Sistema (Host)
Monitora CPU, RAM, Disco e Uptime da VPS
"""

import psutil
import time
from typing import Dict, Any, List, Tuple
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Classe responsável por monitorar recursos do host"""
    
    def __init__(self, cpu_threshold: float = 85.0, 
                 ram_threshold: float = 90.0, 
                 disk_threshold: float = 90.0):
        """
        Inicializa o monitor de sistema
        
        Args:
            cpu_threshold: Limiar de CPU em % para alertas
            ram_threshold: Limiar de RAM em % para alertas
            disk_threshold: Limiar de Disco em % para alertas
        """
        self.CPU_THRESHOLD = cpu_threshold
        self.RAM_THRESHOLD = ram_threshold
        self.DISK_THRESHOLD = disk_threshold
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Coleta estatísticas atuais do sistema
        
        Returns:
            Dicionário com métricas do sistema
        """
        try:
            # CPU (percentual médio dos últimos segundos)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memória RAM
            memory = psutil.virtual_memory()
            ram_percent = memory.percent
            ram_used_gb = memory.used / (1024 ** 3)
            ram_total_gb = memory.total / (1024 ** 3)
            
            # Disco (partição raiz)
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))
            
            # Contagem de processos
            process_count = len(psutil.pids())
            
            stats = {
                "cpu_percent": round(cpu_percent, 2),
                "ram_percent": round(ram_percent, 2),
                "ram_used_gb": round(ram_used_gb, 2),
                "ram_total_gb": round(ram_total_gb, 2),
                "disk_percent": round(disk_percent, 2),
                "disk_used_gb": round(disk_used_gb, 2),
                "disk_total_gb": round(disk_total_gb, 2),
                "uptime": uptime_str,
                "uptime_seconds": int(uptime_seconds),
                "process_count": process_count,
                "timestamp": int(time.time())
            }
            
            logger.debug(f"Estatísticas do sistema coletadas: CPU={cpu_percent}%, RAM={ram_percent}%, Disk={disk_percent}%")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao coletar estatísticas do sistema: {e}")
            return {
                "error": str(e),
                "timestamp": int(time.time())
            }
    
    def check_thresholds(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Verifica se algum recurso ultrapassou o limiar
        
        Args:
            stats: Estatísticas do sistema
            
        Returns:
            Lista de alertas críticos detectados
        """
        alerts = []
        
        # Verifica se há erro nas stats
        if "error" in stats:
            return alerts
        
        # Alerta de CPU
        if stats["cpu_percent"] > self.CPU_THRESHOLD:
            alerts.append({
                "type": "CPU_CRITICAL",
                "severity": "high",
                "message": f"🔴 CPU em {stats['cpu_percent']}% (limite: {self.CPU_THRESHOLD}%)",
                "value": stats["cpu_percent"],
                "threshold": self.CPU_THRESHOLD
            })
        
        # Alerta de RAM
        if stats["ram_percent"] > self.RAM_THRESHOLD:
            alerts.append({
                "type": "RAM_CRITICAL",
                "severity": "high",
                "message": f"🔴 RAM em {stats['ram_percent']}% (limite: {self.RAM_THRESHOLD}%)",
                "value": stats["ram_percent"],
                "threshold": self.RAM_THRESHOLD,
                "details": f"{stats['ram_used_gb']}GB / {stats['ram_total_gb']}GB"
            })
        
        # Alerta de Disco
        if stats["disk_percent"] > self.DISK_THRESHOLD:
            alerts.append({
                "type": "DISK_CRITICAL",
                "severity": "critical",
                "message": f"🔴 DISCO em {stats['disk_percent']}% (limite: {self.DISK_THRESHOLD}%)",
                "value": stats["disk_percent"],
                "threshold": self.DISK_THRESHOLD,
                "details": f"{stats['disk_used_gb']}GB / {stats['disk_total_gb']}GB"
            })
        
        if alerts:
            logger.warning(f"Detectados {len(alerts)} alertas críticos de sistema")
        
        return alerts
    
    def get_formatted_report(self, stats: Dict[str, Any]) -> str:
        """
        Gera um relatório formatado das estatísticas
        
        Args:
            stats: Estatísticas do sistema
            
        Returns:
            String formatada para envio
        """
        if "error" in stats:
            return f"❌ Erro ao coletar dados do sistema: {stats['error']}"
        
        # Emojis baseados nos níveis
        cpu_emoji = "🟢" if stats["cpu_percent"] < self.CPU_THRESHOLD else "🔴"
        ram_emoji = "🟢" if stats["ram_percent"] < self.RAM_THRESHOLD else "🔴"
        disk_emoji = "🟢" if stats["disk_percent"] < self.DISK_THRESHOLD else "🔴"
        
        report = f"""📊 *Relatório do Sistema*

{cpu_emoji} *CPU:* {stats['cpu_percent']}%
{ram_emoji} *RAM:* {stats['ram_percent']}% ({stats['ram_used_gb']}GB / {stats['ram_total_gb']}GB)
{disk_emoji} *Disco:* {stats['disk_percent']}% ({stats['disk_used_gb']}GB / {stats['disk_total_gb']}GB)

⏱️ *Uptime:* {stats['uptime']}
🔢 *Processos:* {stats['process_count']}
"""
        
        return report.strip()

