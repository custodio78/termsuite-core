FROM python:3.9-slim

# Instalar Java (necesario para TermSuite)
RUN apt-get update && apt-get install -y \
    openjdk-11-jre-headless \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY app/ ./app/

# Crear directorios para datos
RUN mkdir -p /app/data/uploads /app/data/corpus /app/data/outputs /app/termsuite

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
