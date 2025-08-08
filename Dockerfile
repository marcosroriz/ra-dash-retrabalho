FROM python:3.11-slim

# Define um diretório de trabalho temporário
WORKDIR /

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    build-essential \
    libpq-dev \
    gcc \
    g++ \
    curl \
    gnupg2 \
    libsqlite3-mod-spatialite \
  && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos do host para o container
COPY . .

# Muda o diretório de trabalho para /src
WORKDIR /src

# Comando de inicialização
CMD ["python", "app.py"]
