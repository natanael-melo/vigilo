# 🚀 Vigilo - Quick Start Guide

Este guia rápido vai te ajudar a colocar o Vigilo rodando em poucos minutos.

---

## ⚡ Método 1: Docker Compose (Recomendado)

### Passo 1: Clone ou copie o projeto

```bash
git clone <repo-url>
cd vigilo
```

### Passo 2: Configure as variáveis

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas configurações
nano .env
```

**Variáveis OBRIGATÓRIAS:**
- `EVOLUTION_URL` → URL da sua Evolution API
- `EVOLUTION_TOKEN` → Token de autenticação
- `EVOLUTION_INSTANCE` → Nome da instância
- `NOTIFY_NUMBER` → Número do WhatsApp (ex: 5511999999999)
- `N8N_HEARTBEAT_URL` → URL do webhook n8n

### Passo 3: Build e Start

```bash
# Build da imagem
docker-compose build

# Iniciar o agente
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f
```

### Passo 4: Verificar

Você deve receber uma mensagem no WhatsApp:
```
✅ Vigilo Iniciado

🖥️ Host: seu-servidor
🕒 30/11/2025 14:30:00
```

---

## 📦 Método 2: Portainer Stack

### Passo 1: Acesse Portainer

1. Abra seu Portainer
2. Vá em **Stacks** → **Add Stack**
3. Dê um nome: `vigilo`

### Passo 2: Cole a Stack

1. Abra o arquivo `portainer-stack.yml`
2. Copie todo o conteúdo
3. Cole no editor do Portainer

### Passo 3: Configure as Variáveis

Edite diretamente no Portainer as linhas com suas configurações:

```yaml
- EVOLUTION_URL=https://sua-evolution-api.com  # ← EDITE AQUI
- EVOLUTION_TOKEN=seu_token_aqui              # ← EDITE AQUI
- EVOLUTION_INSTANCE=nome_da_instancia        # ← EDITE AQUI
- NOTIFY_NUMBER=5511999999999                 # ← EDITE AQUI
- N8N_HEARTBEAT_URL=https://seu-n8n.com/webhook/vigilo  # ← EDITE AQUI
```

### Passo 4: Deploy

1. Clique em **Deploy the stack**
2. Aguarde o build da imagem
3. Verifique os logs em **Containers** → `vigilo-agent`

---

## 🔧 Método 3: Build Manual

### Passo 1: Build da Imagem

```bash
cd vigilo
docker build -t vigilo:latest .
```

### Passo 2: Execute o Container

```bash
docker run -d \
  --name vigilo-agent \
  --restart unless-stopped \
  -e EVOLUTION_URL="https://sua-api.com" \
  -e EVOLUTION_TOKEN="seu_token" \
  -e EVOLUTION_INSTANCE="instancia" \
  -e NOTIFY_NUMBER="5511999999999" \
  -e N8N_HEARTBEAT_URL="https://n8n.com/webhook/hb" \
  -e WATCH_CONTAINERS="postgres,nginx" \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc/localtime:/etc/localtime:ro \
  vigilo:latest
```

---

## ✅ Verificações Pós-Instalação

### 1. Verificar se está rodando

```bash
docker ps | grep vigilo
```

### 2. Ver logs

```bash
docker logs -f vigilo-agent
```

**O que você deve ver:**
```
INFO - 🚀 Iniciando Vigilo Agent
INFO - Conexão com Docker estabelecida com sucesso
INFO - ✅ Evolution API: Conectado
INFO - ✅ n8n Webhook: Conectado
INFO - ✅ Docker: Conectado
INFO - ✅ Vigilo Agent iniciado
```

### 3. Verificar WhatsApp

Você deve receber:
- ✅ Mensagem de inicialização
- 📊 Primeiro relatório após X horas
- ⚠️ Alertas se houver problemas

### 4. Verificar n8n

O webhook deve receber heartbeats a cada 60 segundos (ou seu `CHECK_INTERVAL`).

---

## 🐛 Problemas Comuns

### "Erro ao conectar com Docker"

**Solução:** Verifique se o volume está montado:
```bash
docker inspect vigilo-agent | grep docker.sock
```

Deve mostrar: `/var/run/docker.sock:/var/run/docker.sock:ro`

### "Variável de ambiente obrigatória não está definida"

**Solução:** Verifique se todas as variáveis OBRIGATÓRIAS estão no `.env` ou no comando docker run.

### "Timeout ao enviar mensagem"

**Solução 1:** Teste a Evolution API manualmente:
```bash
curl -H "apikey: SEU_TOKEN" \
  https://sua-api.com/instance/connectionState/INSTANCIA
```

**Solução 2:** Verifique firewall/conectividade da VPS com a API.

### Alertas não chegam

**Motivos possíveis:**
1. Número incorreto (formato: `5511999999999` sem + ou espaços)
2. Cooldown ativo (aguarde 30 minutos)
3. Evolution API offline
4. Instância não conectada

**Debug:**
```bash
docker logs vigilo-agent | grep -i "alert\|erro\|warning"
```

---

## 📱 Teste de Funcionalidade

### Forçar um alerta de teste

```bash
# Simule CPU alta (Linux)
stress-ng --cpu 8 --timeout 120s

# Ou pare um container monitorado
docker stop nome_container_monitorado
```

Você deve receber um alerta no WhatsApp em até 1 minuto.

---

## 🎯 Próximos Passos

1. ✅ Configure o workflow n8n para monitorar heartbeats
2. ✅ Adicione containers importantes no `WATCH_CONTAINERS`
3. ✅ Ajuste os limiares de alerta conforme sua VPS
4. ✅ Configure o `REPORT_HOURS` para o intervalo desejado

---

## 🆘 Precisa de Ajuda?

- 📖 Leia o [README.md](README.md) completo
- 🐛 Veja os logs: `docker logs -f vigilo-agent`
- 💬 Abra uma issue no GitHub

---

**Pronto! Seu Vigilo está funcionando! 🎉**

