# Usa Python 3.11 com sistema base Debian
FROM python:3.11-slim

# Evita interações durante instalação
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza o sistema e instala dependências C necessárias
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libc-dev \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia o projeto
COPY . .

# Instala as dependências Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Comando para iniciar o app
CMD ["python", "app.py"]
