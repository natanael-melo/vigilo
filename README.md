# 🔍 Vigilo - Lightweight Monitoring Agent

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)

**Vigilo** é um agente de monitoramento leve projetado para rodar em containers Docker. Ele monitora a saúde da VPS (Host) e dos Containers vizinhos, enviando alertas via WhatsApp (Evolution API) e sinais de vida (Heartbeat) para um webhook externo (n8n).

---

## 📋 Funcionalidades

- ✅ **Monitoramento de Host**: CPU, RAM, Disco e Uptime
- 🐳 **Monitoramento Docker**: Status e saúde de containers
- 📱 **Alertas WhatsApp**: Via Evolution API com sistema anti-spam
- 💓 **Heartbeat**: Sinais de vida para n8n
- 🔔 **Relatórios Periódicos**: Resumos agendados do sistema
- 🛡️ **Robusto**: Loop resistente a falhas de rede
- 📦 **Fácil Deploy**: Pronto para Portainer

---

## 🏗️ Arquitetura

```
vigilo/
├── src/
│   ├── __init__.py          # Inicializador do pacote
│   ├── main.py              # Entrypoint e Loop Principal
│   ├── config.py            # Gestão de Variáveis de Ambiente
│   ├── system_mon.py        # Monitoramento de Host (CPU/RAM/Disk)
│   ├── docker_mon.py        # Monitoramento de Containers
│   ├── notifier.py          # Integração com Evolution API
│   └── heartbeat.py         # Integração com n8n
├── Dockerfile               # Multi-stage build otimizado
├── docker-compose.yml       # Stack para Portainer
├── requirements.txt         # Dependências fixadas
└── README.md                # Esta documentação
```

---

## 🚀 Quick Start

### Pré-requisitos

- Docker instalado
- Evolution API configurada (WhatsApp)
- Webhook n8n configurado

### 1. Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# Evolution API (WhatsApp)
EVOLUTION_URL=https://sua-evolution-api.com
EVOLUTION_TOKEN=seu_token_aqui
EVOLUTION_INSTANCE=nome_da_instancia
NOTIFY_NUMBER=5511999999999

# n8n Webhook
N8N_HEARTBEAT_URL=https://seu-n8n.com/webhook/vigilo

# Configurações de Tempo (opcional)
CHECK_INTERVAL=60          # Intervalo de checagem em segundos (padrão: 60)
REPORT_HOURS=4             # Intervalo de relatórios em horas (padrão: 4)
ALERT_COOLDOWN=1800        # Cooldown de alertas em segundos (padrão: 1800 = 30min)

# Timezone (opcional)
TZ=America/Sao_Paulo

# Containers para Monitorar (separados por vírgula)
WATCH_CONTAINERS=postgres,api_prod,nginx

# Limiares de Alerta (opcional)
CPU_THRESHOLD=85.0
RAM_THRESHOLD=90.0
DISK_THRESHOLD=90.0

# Log Level (opcional)
LOG_LEVEL=INFO
```

### 2. Deploy via Docker Compose

```bash
# Build da imagem
docker-compose build

# Iniciar o agente
docker-compose up -d

# Ver logs
docker-compose logs -f vigilo
```

### 3. Deploy via Portainer

1. Acesse Portainer → **Stacks**
2. Clique em **Add Stack**
3. Cole o conteúdo do `docker-compose.yml`
4. Configure as variáveis de ambiente
5. Clique em **Deploy the stack**

---

## ⚙️ Configuração Detalhada

### Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `EVOLUTION_URL` | URL base da Evolution API | `https://api.evolution.com` |
| `EVOLUTION_TOKEN` | Token de autenticação | `seu_token_secreto` |
| `EVOLUTION_INSTANCE` | Nome da instância WhatsApp | `minha_instancia` |
| `NOTIFY_NUMBER` | Número para receber alertas | `5511999999999` |
| `N8N_HEARTBEAT_URL` | URL do webhook n8n | `https://n8n.com/webhook/hb` |

### Variáveis Opcionais

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CHECK_INTERVAL` | `60` | Intervalo de checagem (segundos) |
| `REPORT_HOURS` | `4` | Intervalo de relatórios (horas) |
| `ALERT_COOLDOWN` | `1800` | Cooldown de alertas (segundos) |
| `TZ` | `America/Sao_Paulo` | Timezone do sistema |
| `WATCH_CONTAINERS` | `""` | Containers prioritários (separados por vírgula) |
| `CPU_THRESHOLD` | `85.0` | Limiar de CPU para alerta (%) |
| `RAM_THRESHOLD` | `90.0` | Limiar de RAM para alerta (%) |
| `DISK_THRESHOLD` | `90.0` | Limiar de Disco para alerta (%) |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |

---

## 📊 Funcionamento

### Ciclo de Monitoramento

1. **Coleta de Métricas**: CPU, RAM, Disco, Uptime
2. **Verificação de Limiares**: Detecta situações críticas
3. **Monitoramento Docker**: Verifica containers prioritários
4. **Envio de Alertas**: WhatsApp via Evolution API (com cooldown)
5. **Heartbeat**: Envia sinal de vida para n8n
6. **Relatórios Periódicos**: Resumo completo a cada X horas

### Sistema Anti-Spam

O Vigilo implementa um sistema de **cooldown** para evitar spam de alertas:

- Um alerta do mesmo tipo só é reenviado após o tempo de cooldown
- Relatórios periódicos sempre são enviados (sem cooldown)
- Alertas críticos novos são enviados imediatamente

### Monitoramento Docker

Containers listados em `WATCH_CONTAINERS` são verificados quanto a:

- ✅ Status `running`
- ✅ Health check (se configurado no container)

**Exemplos de alertas:**
- ❌ Container não encontrado
- 🔴 Container parado/reiniciando
- ⚠️ Health check `unhealthy`

---

## 🔧 Desenvolvimento Local

### Executar sem Docker

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Edite o .env com suas configurações

# Executar
python src/main.py
```

### Testar Conexões

```bash
# Verificar se o Docker está acessível
docker ps

# Testar Evolution API
curl -H "apikey: SEU_TOKEN" https://sua-api.com/instance/connectionState/INSTANCIA

# Testar n8n Webhook
curl -X POST https://seu-n8n.com/webhook/vigilo \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

---

## 📱 Exemplos de Mensagens

### Alerta de CPU

```
⚠️ ALERTA OMNIWATCH ⚠️

🔴 CPU em 92.5% (limite: 85.0%)

🕒 30/11/2025 14:35:22
```

### Relatório Periódico

```
📊 RELATÓRIO OMNIWATCH

📊 Relatório do Sistema

🟢 CPU: 45.2%
🟢 RAM: 65.8% (5.2GB / 8.0GB)
🟢 Disco: 72.1% (350.5GB / 486.0GB)

⏱️ Uptime: 15 days, 4:23:10
🔢 Processos: 187

🐳 Docker: 8 rodando / 2 parados

Monitorados:
🟢 postgres
🟢 api_prod
🔴 nginx

📡 Status do Agente
✅ Checagens realizadas: 1445
📤 Heartbeats enviados: 1443
❌ Falhas heartbeat: 2
📊 Taxa de sucesso: 99.86%

🕒 30/11/2025 16:00:05
```

---

## 🛡️ Segurança

### Boas Práticas

- ✅ Socket Docker montado como **read-only** (`:ro`)
- ✅ Tokens sensíveis via variáveis de ambiente
- ✅ Sem exposição de portas desnecessárias
- ✅ Logs estruturados (não expõem tokens)
- ✅ Health check configurado

### Permissões Docker

O container precisa acessar `/var/run/docker.sock` para monitorar containers. Isso é seguro quando montado como read-only.

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs vigilo

# Verificar variáveis de ambiente
docker-compose config
```

### "Erro ao conectar com Docker"

- Verifique se o socket está montado: `-v /var/run/docker.sock:/var/run/docker.sock:ro`
- Verifique permissões do Docker no host

### "Timeout ao enviar mensagem"

- Verifique conectividade com Evolution API
- Confirme se o token e instância estão corretos
- Teste manualmente com `curl`

### Alertas não chegam

- Verifique se o número está no formato correto: `5511999999999`
- Confirme se o cooldown não está bloqueando: logs mostram `"em cooldown"`
- Verifique logs de erro no container

---

## 📈 Monitoramento do Próprio Agente

O Vigilo envia heartbeats para o n8n. Configure um workflow para:

1. Receber heartbeats a cada `CHECK_INTERVAL` segundos
2. Alertar se não receber heartbeat por X minutos (agente pode estar offline)
3. Armazenar métricas históricas

**Exemplo de payload de heartbeat:**

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

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Add: Minha Feature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🆘 Suporte

- 📧 Email: suporte@vigilo.com
- 💬 Discord: [Link do Discord]
- 📚 Docs: [docs.vigilo.com]

---

## ✨ Roadmap

- [ ] Dashboard Web
- [ ] Métricas históricas (Prometheus/Grafana)
- [ ] Suporte a múltiplos canais de notificação
- [ ] Auto-correção de problemas detectados
- [ ] Integração com Slack/Telegram
- [ ] Monitoramento de rede e latência

---

**Feito com ❤️ pela equipe Vigilo**

