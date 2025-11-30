#!/usr/bin/env python3
"""
Script de Teste de Configuração do Vigilo
Valida se todas as variáveis de ambiente estão configuradas corretamente
"""

import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header(text):
    """Imprime um cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"❌ {text}")

def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"⚠️  {text}")

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print_header("Testando Importações")
    
    modules = [
        'psutil',
        'docker',
        'requests',
        'dotenv'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print_success(f"Módulo '{module}' importado com sucesso")
        except ImportError as e:
            print_error(f"Erro ao importar '{module}': {e}")
            all_ok = False
    
    return all_ok

def test_config():
    """Testa se a configuração pode ser carregada"""
    print_header("Testando Configuração")
    
    try:
        from config import config
        print_success("Configuração carregada com sucesso")
        
        # Mostra configuração (sem expor tokens)
        print(f"\n📋 Configuração:")
        print(f"   CHECK_INTERVAL: {config.CHECK_INTERVAL}s")
        print(f"   REPORT_HOURS: {config.REPORT_HOURS}h")
        print(f"   ALERT_COOLDOWN: {config.ALERT_COOLDOWN}s")
        print(f"   TZ: {config.TZ}")
        print(f"   WATCH_CONTAINERS: {config.WATCH_CONTAINERS or 'Nenhum'}")
        print(f"   CPU_THRESHOLD: {config.CPU_THRESHOLD}%")
        print(f"   RAM_THRESHOLD: {config.RAM_THRESHOLD}%")
        print(f"   DISK_THRESHOLD: {config.DISK_THRESHOLD}%")
        print(f"   LOG_LEVEL: {config.LOG_LEVEL}")
        
        return True
    except ValueError as e:
        print_error(f"Erro na configuração: {e}")
        return False
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        return False

def test_system_monitor():
    """Testa o monitor de sistema"""
    print_header("Testando Monitor de Sistema")
    
    try:
        from system_mon import SystemMonitor
        from config import config
        
        monitor = SystemMonitor(
            cpu_threshold=config.CPU_THRESHOLD,
            ram_threshold=config.RAM_THRESHOLD,
            disk_threshold=config.DISK_THRESHOLD
        )
        
        print_success("SystemMonitor inicializado")
        
        # Coleta métricas
        stats = monitor.get_system_stats()
        
        if "error" in stats:
            print_error(f"Erro ao coletar métricas: {stats['error']}")
            return False
        
        print_success("Métricas coletadas:")
        print(f"   CPU: {stats['cpu_percent']}%")
        print(f"   RAM: {stats['ram_percent']}% ({stats['ram_used_gb']}GB / {stats['ram_total_gb']}GB)")
        print(f"   Disco: {stats['disk_percent']}% ({stats['disk_used_gb']}GB / {stats['disk_total_gb']}GB)")
        print(f"   Uptime: {stats['uptime']}")
        
        # Verifica alertas
        alerts = monitor.check_thresholds(stats)
        if alerts:
            print_warning(f"{len(alerts)} alertas detectados:")
            for alert in alerts:
                print(f"      - {alert['message']}")
        else:
            print_success("Nenhum alerta detectado")
        
        return True
        
    except Exception as e:
        print_error(f"Erro ao testar SystemMonitor: {e}")
        return False

def test_docker_monitor():
    """Testa o monitor Docker"""
    print_header("Testando Monitor Docker")
    
    try:
        from docker_mon import DockerMonitor
        from config import config
        
        monitor = DockerMonitor(watch_containers=config.WATCH_CONTAINERS)
        
        if not monitor.is_connected():
            print_error("Não conectado ao Docker")
            print_warning("Verifique se o Docker está rodando e o socket está acessível")
            return False
        
        print_success("Conectado ao Docker")
        
        # Lista containers
        containers = monitor.get_all_containers()
        print_success(f"Total de containers: {len(containers)}")
        
        running = [c for c in containers if c['status'] == 'running']
        print(f"   Rodando: {len(running)}")
        
        if config.WATCH_CONTAINERS:
            print(f"\n📋 Containers monitorados:")
            for name in config.WATCH_CONTAINERS:
                container = next((c for c in containers if c['name'] == name), None)
                if container:
                    status_emoji = "🟢" if container['status'] == 'running' else "🔴"
                    print(f"   {status_emoji} {name}: {container['status']}")
                else:
                    print(f"   ❌ {name}: NÃO ENCONTRADO")
            
            # Verifica alertas
            alerts = monitor.check_watched_containers()
            if alerts:
                print_warning(f"\n{len(alerts)} alertas detectados:")
                for alert in alerts:
                    print(f"      - {alert['message']}")
        
        return True
        
    except Exception as e:
        print_error(f"Erro ao testar DockerMonitor: {e}")
        return False

def test_notifier():
    """Testa o notificador (sem enviar mensagem real)"""
    print_header("Testando Notificador")
    
    try:
        from notifier import Notifier
        from config import config
        
        notifier = Notifier(
            evolution_url=config.EVOLUTION_URL,
            evolution_token=config.EVOLUTION_TOKEN,
            evolution_instance=config.EVOLUTION_INSTANCE,
            notify_number=config.NOTIFY_NUMBER,
            cooldown_seconds=config.ALERT_COOLDOWN
        )
        
        print_success("Notifier inicializado")
        print(f"   URL: {config.EVOLUTION_URL}")
        print(f"   Instância: {config.EVOLUTION_INSTANCE}")
        print(f"   Número: {config.NOTIFY_NUMBER}")
        print(f"   Cooldown: {config.ALERT_COOLDOWN}s")
        
        # Teste de conexão
        print("\n🔍 Testando conexão com Evolution API...")
        if notifier.test_connection():
            print_success("Conexão OK")
            return True
        else:
            print_warning("Falha na conexão (verifique URL, token e instância)")
            return False
        
    except Exception as e:
        print_error(f"Erro ao testar Notifier: {e}")
        return False

def test_heartbeat():
    """Testa o heartbeat (sem enviar payload real)"""
    print_header("Testando Heartbeat")
    
    try:
        from heartbeat import Heartbeat
        from config import config
        
        heartbeat = Heartbeat(webhook_url=config.N8N_HEARTBEAT_URL)
        
        print_success("Heartbeat inicializado")
        print(f"   URL: {config.N8N_HEARTBEAT_URL}")
        print(f"   Hostname: {heartbeat.hostname}")
        
        # Teste de conexão
        print("\n🔍 Testando conexão com n8n webhook...")
        if heartbeat.test_connection():
            print_success("Conexão OK")
            return True
        else:
            print_warning("Falha na conexão (verifique URL do webhook)")
            return False
        
    except Exception as e:
        print_error(f"Erro ao testar Heartbeat: {e}")
        return False

def main():
    """Função principal"""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║          VIGILO - TESTE DE CONFIGURAÇÃO               ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    results = {
        "Importações": test_imports(),
        "Configuração": test_config(),
        "Monitor Sistema": test_system_monitor(),
        "Monitor Docker": test_docker_monitor(),
        "Notificador": test_notifier(),
        "Heartbeat": test_heartbeat()
    }
    
    # Resumo
    print_header("Resumo dos Testes")
    
    all_passed = True
    for test_name, passed in results.items():
        if passed:
            print_success(f"{test_name}: PASSOU")
        else:
            print_error(f"{test_name}: FALHOU")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O Vigilo está pronto para ser executado.")
        print("\nPara iniciar:")
        print("  docker-compose up -d")
        print("\nPara ver logs:")
        print("  docker-compose logs -f")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("⚠️  Corrija os problemas antes de executar o agente.")
    print("=" * 60 + "\n")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

