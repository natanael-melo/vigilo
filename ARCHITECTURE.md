# 🏗️ Vigilo - Arquitetura Técnica

## 📊 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                     OMNIWATCH AGENT                         │
│                    (Docker Container)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Host VPS   │    │   Containers │    │   External   │
│ CPU/RAM/DISK │    │    Docker    │    │   Services   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Alert Logic  │
                    │   Threshold   │
                    │    Checking   │
                    └───────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │  WhatsApp    │        │  n8n Webhook │
        │ (Evolution)  │        │  (Heartbeat) │
        └──────────────┘        └──────────────┘
```

---

## 🔄 Fluxo de Execução

### 1. Inicialização

```python
main.py
  ├─► Carrega config.py (variáveis de ambiente)
  ├─► Inicializa SystemMonitor (system_mon.py)
  ├─► Inicializa DockerMonitor (docker_mon.py)
  ├─► Inicializa Notifier (notifier.py)
  ├─► Inicializa Heartbeat (heartbeat.py)
  ├─► Testa todas as conexões
  └─► Envia notificação de startup
```

### 2. Loop de Monitoramento

```
┌─────────────────────────────────────────────────┐
│              CICLO DE CHECAGEM                  │
│                                                 │
│  1. Coleta métricas do sistema (psutil)        │
│     ├─► CPU %                                   │
│     ├─► RAM %                                   │
│     ├─► Disk %                                  │
│     └─► Uptime                                  │
│                                                 │
│  2. Verifica limiares                          │
│     ├─► CPU > 85%? → Alerta                    │
│     ├─► RAM > 90%? → Alerta                    │
│     └─► Disk > 90%? → Alerta                   │
│                                                 │
│  3. Verifica containers Docker                 │
│     ├─► Container rodando?                     │
│     └─► Health check OK?                       │
│                                                 │
│  4. Processa alertas                           │
│     ├─► Verifica cooldown                      │
│     └─► Envia via WhatsApp                     │
│                                                 │
│  5. Envia heartbeat para n8n                   │
│     └─► Payload com métricas                   │
│                                                 │
│  6. Relatório periódico? (a cada X horas)      │
│     └─► Envia resumo completo                  │
│                                                 │
│  7. Sleep (CHECK_INTERVAL)                     │
│     └─► Aguarda próximo ciclo                  │
└─────────────────────────────────────────────────┘
           │
           └──► REPETE (while True)
```

---

## 📦 Módulos e Responsabilidades

### `src/config.py`
**Responsabilidade:** Gestão centralizada de configurações

- ✅ Carrega variáveis de ambiente
- ✅ Valida configurações obrigatórias
- ✅ Fornece valores default seguros
- ✅ Expõe configuração via instância global

**Dependências:**
- `os`, `dotenv`

**Expõe:**
- `config` (instância global da classe Config)

---

### `src/system_mon.py`
**Responsabilidade:** Monitoramento de recursos do host

**Métricas coletadas:**
- CPU % (média dos últimos segundos)
- RAM % e GB usados/total
- Disco % e GB usados/total
- Uptime (tempo desde boot)
- Número de processos

**Funções principais:**
- `get_system_stats()` → Dict com métricas
- `check_thresholds(stats)` → Lista de alertas
- `get_formatted_report(stats)` → String formatada

**Dependências:**
- `psutil`

---

### `src/docker_mon.py`
**Responsabilidade:** Monitoramento de containers Docker

**Funcionalidades:**
- Lista todos os containers
- Lista containers rodando
- Monitora containers específicos (`WATCH_CONTAINERS`)
- Verifica health checks
- Coleta estatísticas básicas (CPU/RAM por container)

**Funções principais:**
- `get_all_containers()` → Lista de containers
- `get_running_containers()` → Lista de containers rodando
- `check_watched_containers()` → Lista de alertas
- `get_docker_summary()` → String formatada

**Dependências:**
- `docker` (Docker SDK)

**Requer:**
- Volume `/var/run/docker.sock` montado

---

### `src/notifier.py`
**Responsabilidade:** Envio de notificações via WhatsApp

**Funcionalidades:**
- Envia mensagens via Evolution API
- Sistema de cooldown (anti-spam)
- Envia alertas individuais ou em lote
- Envia relatórios periódicos
- Testa conexão com API

**Sistema Anti-Spam:**
```python
# Exemplo: Alerta "CPU_CRITICAL"
if alerta_tipo == "CPU_CRITICAL":
    if tempo_desde_ultimo_envio < 1800s:
        # NÃO ENVIA (cooldown ativo)
        return False
    else:
        # ENVIA e registra timestamp
        return True
```

**Funções principais:**
- `send_message(msg, force, alert_type)` → Bool
- `send_alert(alert_dict)` → Bool
- `send_alerts(list_alerts)` → Int (enviados)
- `send_report(report_text)` → Bool (sempre envia)
- `test_connection()` → Bool

**Dependências:**
- `requests`

---

### `src/heartbeat.py`
**Responsabilidade:** Envio de sinais de vida para n8n

**Funcionalidades:**
- Envia heartbeat a cada ciclo
- Inclui métricas resumidas no payload
- Envia eventos especiais (startup, shutdown, alertas)
- Tolera falhas (não para o agente)
- Rastreia estatísticas de envio

**Payload de exemplo:**
```json
{
  "agent_name": "minha-vps",
  "status": "alive",
  "timestamp": 1701368400,
  "stats": {
    "cpu_percent": 45.2,
    "ram_percent": 65.8,
    "disk_percent": 72.1,
    "uptime_seconds": 1324990
  },
  "consecutive_failures": 0,
  "total_sent": 1445,
  "total_failed": 2
}
```

**Funções principais:**
- `send(stats, extra_data)` → Bool
- `send_event(event_type, event_data)` → Bool
- `send_startup_event()` → Bool
- `send_alert_event(count, types)` → Bool
- `test_connection()` → Bool
- `get_stats()` → Dict

**Dependências:**
- `requests`, `socket`

---

### `src/main.py`
**Responsabilidade:** Loop principal e orquestração

**Classe Principal:**
```python
class VigiloAgent:
    def __init__(self):
        # Inicializa todos os monitores
        pass
    
    def run(self):
        # Loop infinito de monitoramento
        while self.running:
            self._perform_check()
            time.sleep(CHECK_INTERVAL)
```

**Funcionalidades:**
- Orquestra todos os módulos
- Loop robusto (captura exceções)
- Shutdown gracioso (SIGINT/SIGTERM)
- Controla timing de relatórios
- Logging estruturado

**Tratamento de Erros:**
```python
try:
    # Executa checagem
    self._perform_check()
except Exception as e:
    # Loga erro
    logger.error(f"Erro: {e}")
    # NÃO PARA - apenas dorme e continua
    time.sleep(30)
    continue
```

---

## 🔐 Segurança

### Princípios Aplicados

1. **Least Privilege**
   - Socket Docker montado como **read-only** (`:ro`)
   - Sem exposição de portas

2. **Secrets Management**
   - Tokens via variáveis de ambiente
   - Nunca logados em texto plano
   - Não commitados no Git (`.gitignore`)

3. **Error Handling**
   - Exceções capturadas
   - Logs sem informações sensíveis
   - Falhas não param o agente

4. **Resource Limits**
   - Opcional via Docker Compose
   - Previne consumo excessivo

---

## 🐳 Containerização

### Dockerfile Multi-stage

```dockerfile
# Stage 1: Builder
FROM python:3.9-slim AS builder
# Instala dependências com gcc

# Stage 2: Runtime
FROM python:3.9-slim
# Copia apenas dependências compiladas
# Imagem final mais leve
```

**Benefícios:**
- ✅ Imagem final menor (~150MB)
- ✅ Sem ferramentas de build desnecessárias
- ✅ Mais rápida para deploy

### Volumes Necessários

| Volume | Modo | Propósito |
|--------|------|-----------|
| `/var/run/docker.sock` | `ro` | Acesso à API Docker |
| `/etc/localtime` | `ro` | Sincronizar timezone |
| `/etc/timezone` | `ro` | Sincronizar timezone |

---

## 📈 Escalabilidade

### Limitações Atuais

- ❌ Monitora apenas 1 host (onde está rodando)
- ❌ Sem persistência de métricas históricas
- ❌ Sem dashboard visual

### Possíveis Expansões

1. **Múltiplos Agentes**
   - Executar em várias VPS
   - Centralizar dados no n8n

2. **Persistência**
   - Integrar com Prometheus
   - Armazenar métricas em banco

3. **Dashboard**
   - Grafana para visualização
   - Interface web própria

4. **Auto-correção**
   - Reiniciar containers automaticamente
   - Executar scripts de recuperação

---

## 🧪 Testes

### Testes Unitários (Futuro)

```python
# test_system_mon.py
def test_get_system_stats():
    monitor = SystemMonitor()
    stats = monitor.get_system_stats()
    assert "cpu_percent" in stats
    assert 0 <= stats["cpu_percent"] <= 100
```

### Testes de Integração

```bash
# Teste manual do agente
docker-compose up

# Em outro terminal, force um alerta
stress-ng --cpu 8 --timeout 60s

# Verifique se alerta chega no WhatsApp
```

---

## 📊 Métricas e Observabilidade

### Logs

O agente gera logs estruturados em `stdout`:

```
2025-11-30 14:30:00 - main - INFO - 🚀 Iniciando Vigilo Agent
2025-11-30 14:30:01 - config - INFO - Configuração carregada
2025-11-30 14:30:02 - docker_mon - INFO - Conexão com Docker estabelecida
2025-11-30 14:30:03 - notifier - INFO - ✅ Evolution API: Conectado
2025-11-30 14:30:04 - heartbeat - INFO - ✅ n8n Webhook: Conectado
2025-11-30 14:30:05 - main - INFO - ✅ Vigilo Agent iniciado
2025-11-30 14:30:06 - main - INFO - 🔍 Checagem #1
2025-11-30 14:30:07 - system_mon - DEBUG - CPU=45%, RAM=68%, Disk=72%
2025-11-30 14:30:08 - main - INFO - ✅ Sistema OK
```

### Métricas Expostas

O heartbeat envia para n8n:
- CPU/RAM/Disk % atuais
- Uptime do host
- Número de checagens realizadas
- Taxa de sucesso de heartbeats

---

## 🔧 Manutenção

### Atualizações

```bash
# Pull da nova versão
git pull

# Rebuild da imagem
docker-compose build

# Restart do agente
docker-compose down && docker-compose up -d
```

### Monitoramento do Agente

Configure no n8n um workflow:

```
[Webhook] → [Aguarda Heartbeat (60s)] → [Se não receber] → [Alerta "Agente Offline"]
```

---

**Arquitetura desenhada para ser simples, robusta e extensível.**

