FROM python:3.11-slim-bookworm

# Instalar Java 17 (necesario para TermSuite)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno de Java para compatibilidad con TermSuite
ENV JAVA_TOOL_OPTIONS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.security=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED"

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
