# 📜 SCRIPTS TERMSUITE-API

Esta carpeta contiene todos los scripts de automatización, utilidades y herramientas del proyecto.

## 🔧 **SCRIPTS DE DOCKER Y DESPLIEGUE**

### **Docker Management**
- `rebuild-docker.bat` / `rebuild-docker.sh` - Reconstruir container Docker
- `run-docker.sh` - Ejecutar container Docker
- `stop-docker.sh` - Detener container Docker
- `logs-docker.sh` - Ver logs del container

### **Inicio y Parada**
- `start.bat` / `start.sh` - Iniciar aplicación
- `apply-download-fix.bat` / `apply-download-fix.sh` - Aplicar correcciones

---

## 🛠️ **SCRIPTS DE INSTALACIÓN**

### **TreeTagger**
- `install_treetagger.sh` - Instalar TreeTagger automáticamente

---

## 🔍 **SCRIPTS DE VERIFICACIÓN Y UTILIDADES**

### **Verificación de Sistema**
- `verify-changes.py` - Verificar cambios en el código
- `check_excel_content.py` - Verificar contenido de archivos Excel
- `check_progress.py` - Verificar progreso de procesamiento
- `monitor_progress.py` - Monitorear progreso en tiempo real

### **Cliente de Ejemplo**
- `client_example.py` - Ejemplo de cliente para usar la API

---

## 🚀 **CÓMO USAR LOS SCRIPTS**

### **🐳 Gestión de Docker**

#### **Reconstruir Docker (Recomendado después de cambios)**
```bash
# Windows
.\scripts\rebuild-docker.bat

# Linux/Mac
./scripts/rebuild-docker.sh
```

#### **Iniciar/Parar Docker**
```bash
# Iniciar
./scripts/run-docker.sh

# Parar
./scripts/stop-docker.sh

# Ver logs
./scripts/logs-docker.sh
```

### **🔧 Instalación de Dependencias**

#### **Instalar TreeTagger**
```bash
./scripts/install_treetagger.sh
```

### **✅ Verificación y Testing**

#### **Verificar cambios**
```bash
python scripts/verify-changes.py
```

#### **Verificar Excel generado**
```bash
python scripts/check_excel_content.py archivo.xlsx
```

#### **Monitorear progreso**
```bash
python scripts/monitor_progress.py
```

### **📡 Cliente de Ejemplo**
```bash
python scripts/client_example.py
```

---

## 📋 **SCRIPTS POR PLATAFORMA**

### **🪟 Windows (.bat)**
- `rebuild-docker.bat`
- `start.bat`
- `apply-download-fix.bat`

### **🐧 Linux/Mac (.sh)**
- `rebuild-docker.sh`
- `start.sh`
- `apply-download-fix.sh`
- `run-docker.sh`
- `stop-docker.sh`
- `logs-docker.sh`
- `install_treetagger.sh`

### **🐍 Python (.py)**
- `verify-changes.py`
- `check_excel_content.py`
- `check_progress.py`
- `monitor_progress.py`
- `client_example.py`

---

## ⚡ **SCRIPTS MÁS UTILIZADOS**

### **1. Desarrollo Diario**
```bash
# Reconstruir después de cambios
.\scripts\rebuild-docker.bat

# Ver logs en tiempo real
.\scripts\logs-docker.sh
```

### **2. Verificación**
```bash
# Verificar que todo funciona
python scripts/verify-changes.py

# Verificar Excel generado
python scripts/check_excel_content.py test_export.xlsx
```

### **3. Instalación Inicial**
```bash
# Instalar TreeTagger
./scripts/install_treetagger.sh

# Iniciar por primera vez
./scripts/run-docker.sh
```

---

## 🔧 **PERSONALIZACIÓN**

### **Modificar configuración Docker**
Edita las variables en los scripts `.bat` o `.sh`:
```bash
# Ejemplo en rebuild-docker.sh
DOCKER_IMAGE_NAME="termsuite-api"
CONTAINER_NAME="termsuite-api"
PORT="7000"
```

### **Configurar monitoreo**
Modifica `monitor_progress.py` para cambiar:
- Intervalo de verificación
- URL de la API
- Formato de salida

---

## 📊 **LOGS Y SALIDA**

### **Logs de Docker**
```bash
# Ver logs en tiempo real
./scripts/logs-docker.sh

# Ver últimas 50 líneas
docker-compose logs --tail=50 termsuite-api
```

### **Logs de Scripts**
Los scripts generan logs en:
- Consola (stdout)
- Archivos temporales (cuando aplique)

---

**💡 Tip**: Usa `rebuild-docker.bat` después de cualquier cambio en el código para aplicar las modificaciones.