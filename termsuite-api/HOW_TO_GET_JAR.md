# 📦 Cómo Obtener el JAR de TermSuite

El JAR de TermSuite es necesario para que la API funcione. Tienes varias opciones:

## Opción 1: Compilar desde el Código Fuente (Recomendado)

Si ya tienes el código fuente de TermSuite en tu máquina:

### Paso 1: Instalar Gradle

**Windows (con Chocolatey):**
```cmd
choco install gradle
```

**Windows (Manual):**
1. Descarga Gradle desde: https://gradle.org/releases/
2. Extrae en `C:\Gradle`
3. Agrega `C:\Gradle\bin` al PATH

**Linux:**
```bash
sudo apt install gradle
# o
sudo snap install gradle --classic
```

**Mac:**
```bash
brew install gradle
```

### Paso 2: Compilar TermSuite

```bash
# Navegar al directorio de TermSuite
cd /ruta/a/termsuite-core

# Compilar
gradle clean jar

# El JAR se generará en:
# build/libs/termsuite-core-3.0.10.jar
```

### Paso 3: Copiar el JAR

```bash
# Copiar a la carpeta de la API
cp build/libs/termsuite-core-3.0.10.jar /ruta/a/termsuite-api/termsuite/
```

## Opción 2: Descargar desde Maven Central

Si TermSuite está publicado en Maven Central:

```bash
# Descargar con wget
wget https://repo1.maven.org/maven2/fr/univ-nantes/termsuite/termsuite-core/3.0.10/termsuite-core-3.0.10.jar

# O con curl
curl -O https://repo1.maven.org/maven2/fr/univ-nantes/termsuite/termsuite-core/3.0.10/termsuite-core-3.0.10.jar

# Mover a la carpeta correcta
mv termsuite-core-3.0.10.jar termsuite-api/termsuite/
```

## Opción 3: Usar Maven para Descargar

Si tienes Maven instalado:

```bash
mvn dependency:get \
  -DgroupId=fr.univ-nantes.termsuite \
  -DartifactId=termsuite-core \
  -Dversion=3.0.10 \
  -Dpackaging=jar \
  -Ddest=termsuite-api/termsuite/termsuite-core-3.0.10.jar
```

## Opción 4: Crear un Fat JAR Manualmente

Si tienes el proyecto pero Gradle no funciona:

### Usando el proyecto actual

Desde el directorio raíz del proyecto TermSuite original:

```bash
# Windows
cd /d %~dp0
gradle clean jar
copy build\libs\termsuite-core-3.0.10.jar ..\termsuite-api\termsuite\

# Linux/Mac
cd "$(dirname "$0")"
gradle clean jar
cp build/libs/termsuite-core-3.0.10.jar ../termsuite-api/termsuite/
```

## Verificar el JAR

Una vez que tengas el JAR, verifica que funciona:

```bash
# Verificar que existe
ls -la termsuite-api/termsuite/termsuite-core-3.0.10.jar

# Probar ejecución
java -jar termsuite-api/termsuite/termsuite-core-3.0.10.jar --help
```

Deberías ver la ayuda de TermSuite.

## Estructura Final

```
termsuite-api/
├── termsuite/
│   └── termsuite-core-3.0.10.jar  ← Debe estar aquí
├── app/
├── data/
└── ...
```

## Problemas Comunes

### "JAR not found"
- Verifica que el archivo esté en `termsuite-api/termsuite/`
- Verifica que el nombre sea exactamente `termsuite-core-3.0.10.jar`

### "Could not find or load main class"
- El JAR puede estar corrupto
- Recompila o descarga nuevamente

### "UnsupportedClassVersionError"
- Necesitas Java 8 o superior
- Verifica: `java -version`

### Gradle no compila
- Verifica que tengas Java 8 instalado
- Intenta: `gradle clean build --refresh-dependencies`

## Alternativa: Usar Versión Diferente

Si tienes una versión diferente de TermSuite:

1. Edita `docker-compose.yml`:
```yaml
environment:
  - TERMSUITE_JAR=/app/termsuite/termsuite-core-TU-VERSION.jar
```

2. Coloca tu JAR en `termsuite/` con el nombre correcto

3. Actualiza `termsuite.py` si es necesario

## Ayuda Adicional

Si tienes problemas:

1. Verifica los logs de Docker:
   ```bash
   docker-compose logs -f
   ```

2. Prueba el JAR directamente:
   ```bash
   java -jar termsuite/termsuite-core-3.0.10.jar -c corpus/ -l en --json output.json
   ```

3. Consulta la documentación oficial de TermSuite:
   - https://termsuite.github.io/
   - https://github.com/termsuite/termsuite-core
