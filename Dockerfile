# Multi-stage build otimizado para Vigilo
FROM python:3.9-slim AS builder

# Define variáveis de ambiente para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --user -r requirements.txt


# Stage final - imagem mínima
FROM python:3.9-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Instala apenas dependências de runtime necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root (opcional, mas boa prática)
# Comentado pois precisa acessar docker socket
# RUN useradd -m -u 1000 vigilo
# USER vigilo

# Define diretório de trabalho
WORKDIR /app

# Copia dependências Python do builder
COPY --from=builder /root/.local /root/.local

# Copia código da aplicação
COPY src/ ./src/

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Define entrypoint
CMD ["python", "-u", "src/main.py"]

