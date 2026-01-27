FROM python:3.11-slim-bookworm

# Instalar Java 17, Perl y dependencias (Perl necesario para TreeTagger)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    wget \
    perl \
    && rm -rf /var/lib/apt/lists/*

# Descargar JAXB para compatibilidad con TermSuite (requiere Java 8 APIs)
RUN mkdir -p /app/lib && cd /app/lib && \
    wget https://repo1.maven.org/maven2/javax/xml/bind/jaxb-api/2.3.1/jaxb-api-2.3.1.jar && \
    wget https://repo1.maven.org/maven2/com/sun/xml/bind/jaxb-impl/2.3.1/jaxb-impl-2.3.1.jar && \
    wget https://repo1.maven.org/maven2/com/sun/xml/bind/jaxb-core/2.3.0.1/jaxb-core-2.3.0.1.jar && \
    wget https://repo1.maven.org/maven2/javax/activation/activation/1.1.1/activation-1.1.1.jar

# Configurar variables de entorno de Java para compatibilidad con TermSuite
ENV JAVA_TOOL_OPTIONS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.security=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED"
ENV CLASSPATH="/app/lib/*"

# Crear directorios de trabajo
WORKDIR /app

# Instalar TreeTagger (si los archivos están disponibles)
# Los archivos deben estar en termsuite-api/treetagger/ antes de build
# Si no existe el directorio, se creará vacío
COPY --chown=root:root treetagger /tmp/treetagger

RUN if [ -f /tmp/treetagger/tree-tagger-linux-3.2.5.tar.gz ] || [ -f /tmp/treetagger/tree-tagger-linux-3.2.4.tar.gz ]; then \
        echo "========================================"; \
        echo "Instalando TreeTagger..."; \
        echo "========================================"; \
        mkdir -p /app/treetagger && cd /app/treetagger && \
        if [ -f /tmp/treetagger/tree-tagger-linux-3.2.5.tar.gz ]; then \
            tar -xzf /tmp/treetagger/tree-tagger-linux-3.2.5.tar.gz; \
        else \
            tar -xzf /tmp/treetagger/tree-tagger-linux-3.2.4.tar.gz; \
        fi && \
        if [ -f /tmp/treetagger/tagger-scripts.tar.gz ]; then \
            tar -xzf /tmp/treetagger/tagger-scripts.tar.gz; \
        fi && \
        chmod +x bin/* cmd/* 2>/dev/null || true && \
        mkdir -p models && \
        if [ -d /tmp/treetagger/models ]; then \
            echo "Copiando modelos..."; \
            cd models && \
            for file in /tmp/treetagger/models/*.par.gz; do \
                if [ -f "$file" ]; then \
                    echo "Instalando modelo comprimido: $(basename $file)"; \
                    gunzip -c "$file" > $(basename "$file" .gz | sed 's/-utf8//'); \
                fi; \
            done; \
            for file in /tmp/treetagger/models/*.par; do \
                if [ -f "$file" ]; then \
                    echo "Copiando modelo: $(basename $file)"; \
                    cp "$file" .; \
                fi; \
            done; \
            echo "Descomprimiendo todos los modelos .gz restantes..."; \
            for file in *.par.gz; do \
                if [ -f "$file" ]; then \
                    echo "Descomprimiendo: $file"; \
                    gunzip "$file"; \
                fi; \
            done; \
        fi && \
        echo "✓ TreeTagger instalado correctamente"; \
        echo "Modelos instalados:"; \
        ls -la /app/treetagger/models/; \
    else \
        echo "========================================"; \
        echo "⚠ TreeTagger no disponible"; \
        echo "La extracción con TermSuite no funcionará"; \
        echo "Ver INSTALL_TREETAGGER.md para instrucciones"; \
        echo "========================================"; \
    fi

# Limpiar archivos temporales
RUN rm -rf /tmp/treetagger

# Configurar variable de entorno para TreeTagger
ENV TREETAGGER_HOME=/app/treetagger

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
