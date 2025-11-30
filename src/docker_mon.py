"""
Módulo de Monitoramento Docker
Monitora containers Docker via Socket API
"""

import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DockerMonitor:
    """Classe responsável por monitorar containers Docker"""
    
    def __init__(self, watch_containers: List[str] = None):
        """
        Inicializa o monitor Docker
        
        Args:
            watch_containers: Lista de nomes de containers para monitoramento prioritário
        """
        self.watch_containers = watch_containers or []
        self.client: Optional[docker.DockerClient] = None
        self._connect()
    
    def _connect(self) -> None:
        """Estabelece conexão com o Docker Socket"""
        try:
            self.client = docker.from_env()
            # Testa a conexão
            self.client.ping()
            logger.info("Conexão com Docker estabelecida com sucesso")
        except DockerException as e:
            logger.error(f"Erro ao conectar com Docker: {e}")
            logger.error("Certifique-se de que o socket Docker está montado: /var/run/docker.sock")
            self.client = None
    
    def is_connected(self) -> bool:
        """Verifica se está conectado ao Docker"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def get_all_containers(self) -> List[Dict[str, Any]]:
        """
        Lista todos os containers (rodando ou não)
        
        Returns:
            Lista de informações dos containers
        """
        if not self.is_connected():
            logger.error("Não conectado ao Docker")
            return []
        
        try:
            containers = self.client.containers.list(all=True)
            container_list = []
            
            for container in containers:
                container_info = {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                    "created": container.attrs.get("Created", ""),
                }
                
                # Verifica health se disponível
                health_status = self._get_health_status(container)
                if health_status:
                    container_info["health"] = health_status
                
                container_list.append(container_info)
            
            logger.debug(f"Listados {len(container_list)} containers")
            return container_list
            
        except APIError as e:
            logger.error(f"Erro na API do Docker ao listar containers: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao listar containers: {e}")
            return []
    
    def get_running_containers(self) -> List[Dict[str, Any]]:
        """
        Lista apenas containers em execução
        
        Returns:
            Lista de containers rodando
        """
        if not self.is_connected():
            return []
        
        try:
            containers = self.client.containers.list(filters={"status": "running"})
            container_list = []
            
            for container in containers:
                container_info = {
                    "id": container.short_id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.short_id,
                }
                
                # Stats básicas (CPU e Memória) - não bloqueante
                try:
                    stats = container.stats(stream=False)
                    container_info["cpu_percent"] = self._calculate_cpu_percent(stats)
                    container_info["memory_mb"] = self._calculate_memory_usage(stats)
                except:
                    pass
                
                container_list.append(container_info)
            
            return container_list
            
        except Exception as e:
            logger.error(f"Erro ao listar containers rodando: {e}")
            return []
    
    def _get_health_status(self, container) -> Optional[str]:
        """
        Obtém o status de health check do container
        
        Args:
            container: Objeto do container Docker
            
        Returns:
            Status do health check ou None
        """
        try:
            health = container.attrs.get("State", {}).get("Health", {})
            if health:
                return health.get("Status", "none")
        except:
            pass
        return None
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calcula percentual de uso de CPU"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_count = stats["cpu_stats"].get("online_cpus", 1)
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
                return round(cpu_percent, 2)
        except (KeyError, ZeroDivisionError):
            pass
        return 0.0
    
    def _calculate_memory_usage(self, stats: Dict) -> float:
        """Calcula uso de memória em MB"""
        try:
            memory_usage = stats["memory_stats"]["usage"]
            return round(memory_usage / (1024 * 1024), 2)
        except KeyError:
            return 0.0
    
    def check_watched_containers(self) -> List[Dict[str, Any]]:
        """
        Verifica o status dos containers prioritários
        
        Returns:
            Lista de alertas para containers com problemas
        """
        if not self.watch_containers:
            logger.debug("Nenhum container configurado para monitoramento prioritário")
            return []
        
        if not self.is_connected():
            return [{
                "type": "DOCKER_CONNECTION_ERROR",
                "severity": "critical",
                "message": "❌ Não foi possível conectar ao Docker",
            }]
        
        alerts = []
        all_containers = self.get_all_containers()
        
        # Cria um mapa de containers por nome
        container_map = {c["name"]: c for c in all_containers}
        
        for watched_name in self.watch_containers:
            if watched_name not in container_map:
                # Container não encontrado
                alerts.append({
                    "type": "CONTAINER_NOT_FOUND",
                    "severity": "critical",
                    "container": watched_name,
                    "message": f"❌ Container '{watched_name}' não encontrado!",
                })
                continue
            
            container = container_map[watched_name]
            
            # Verifica se está rodando
            if container["status"] != "running":
                alerts.append({
                    "type": "CONTAINER_NOT_RUNNING",
                    "severity": "critical",
                    "container": watched_name,
                    "status": container["status"],
                    "message": f"🔴 Container '{watched_name}' está {container['status'].upper()}!",
                })
            
            # Verifica health check se disponível
            if "health" in container and container["health"] == "unhealthy":
                alerts.append({
                    "type": "CONTAINER_UNHEALTHY",
                    "severity": "high",
                    "container": watched_name,
                    "message": f"⚠️ Container '{watched_name}' está UNHEALTHY!",
                })
        
        if alerts:
            logger.warning(f"Detectados {len(alerts)} problemas em containers monitorados")
        
        return alerts
    
    def get_docker_summary(self) -> str:
        """
        Gera um resumo formatado dos containers
        
        Returns:
            String formatada com resumo Docker
        """
        if not self.is_connected():
            return "❌ *Docker:* Não conectado"
        
        try:
            all_containers = self.get_all_containers()
            running = [c for c in all_containers if c["status"] == "running"]
            stopped = [c for c in all_containers if c["status"] != "running"]
            
            summary = f"🐳 *Docker:* {len(running)} rodando / {len(stopped)} parados"
            
            # Se há containers monitorados, detalha
            if self.watch_containers:
                watched_status = []
                for name in self.watch_containers:
                    container = next((c for c in all_containers if c["name"] == name), None)
                    if container:
                        emoji = "🟢" if container["status"] == "running" else "🔴"
                        watched_status.append(f"{emoji} {name}")
                    else:
                        watched_status.append(f"❌ {name}")
                
                if watched_status:
                    summary += "\n\n*Monitorados:*\n" + "\n".join(watched_status)
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo Docker: {e}")
            return f"❌ *Docker:* Erro ao coletar dados"

