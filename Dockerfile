# Fixado em bookworm (Debian 12) para compatibilidade com msodbcsql17
# Platform amd64: Microsoft ODBC Driver não tem builds para arm64
FROM --platform=linux/amd64 python:3.11-slim-bookworm

WORKDIR /app

# Instalar dependências do sistema + Microsoft ODBC Driver 17 (Debian 12 / Bookworm / amd64)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gnupg2 \
    apt-transport-https \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
       | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
       > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação (secrets.toml excluído via .dockerignore)
COPY App/ ./App/

EXPOSE 8501

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app/App
CMD ["streamlit", "run", "1🏠Home.py"]
