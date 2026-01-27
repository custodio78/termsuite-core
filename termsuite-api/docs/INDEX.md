# 📑 Índice de Documentación - TermSuite API

## 🚀 Para Empezar

1. **[QUICKSTART.md](QUICKSTART.md)** - Guía de inicio rápido (5 minutos)
   - Instalación básica
   - Primer uso
   - Ejemplos rápidos

2. **[HOW_TO_GET_JAR.md](HOW_TO_GET_JAR.md)** - Cómo obtener el JAR de TermSuite
   - Compilar desde código fuente
   - Descargar desde Maven
   - Solución de problemas

## 📖 Documentación Principal

3. **[README.md](README.md)** - Documentación completa
   - Descripción del proyecto
   - Instalación detallada
   - Todos los endpoints
   - Ejemplos de uso
   - Troubleshooting

4. **[TMX_USAGE.md](TMX_USAGE.md)** - Guía de uso de memorias TMX
   - Extracción por idioma
   - Códigos de idioma soportados
   - Casos de uso
   - Integración con herramientas CAT

5. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura técnica
   - Estructura del proyecto
   - Flujo de trabajo
   - Componentes
   - Escalabilidad

## 💻 Código y Ejemplos

5. **[client_example.py](client_example.py)** - Cliente Python de ejemplo
   - Clase TermSuiteClient
   - Ejemplo completo de uso
   - Listo para usar

6. **[test_api.py](test_api.py)** - Script de pruebas
   - Tests automatizados
   - Validación de endpoints
   - Uso: `python test_api.py corpus.txt`

## 📁 Archivos de Configuración

7. **[docker-compose.yml](docker-compose.yml)** - Configuración Docker
   - Servicios
   - Volúmenes
   - Variables de entorno

8. **[Dockerfile](Dockerfile)** - Imagen Docker
   - Base Python + Java
   - Dependencias
   - Configuración

9. **[requirements.txt](requirements.txt)** - Dependencias Python
   - FastAPI
   - Pandas
   - OpenPyXL
   - etc.

10. **[.env.example](.env.example)** - Variables de entorno
    - Configuración de ejemplo
    - Copiar a `.env` para personalizar

## 🎯 Archivos de Ejemplo

11. **[examples/sample_corpus.txt](examples/sample_corpus.txt)**
    - Corpus de ejemplo en inglés
    - Tema: Machine Learning e IA

12. **[examples/sample_memory.tmx](examples/sample_memory.tmx)**
    - Memoria TMX de ejemplo
    - Términos técnicos EN-ES

## 🛠️ Scripts de Utilidad

13. **[start.sh](start.sh)** - Script de inicio (Linux/Mac)
    - Verificaciones automáticas
    - Inicio de servicios

14. **[start.bat](start.bat)** - Script de inicio (Windows)
    - Verificaciones automáticas
    - Inicio de servicios

## 📂 Estructura de Directorios

```
termsuite-api/
├── 📄 Documentación
│   ├── INDEX.md              ← Estás aquí
│   ├── QUICKSTART.md         ← Empieza aquí
│   ├── README.md
│   ├── ARCHITECTURE.md
│   └── HOW_TO_GET_JAR.md
│
├── 🐳 Docker
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── 🐍 Aplicación Python
│   ├── app/
│   │   ├── main.py           ← API endpoints
│   │   ├── models.py         ← Modelos de datos
│   │   ├── services/         ← Lógica de negocio
│   │   └── utils/            ← Utilidades
│   └── requirements.txt
│
├── 🧪 Testing y Ejemplos
│   ├── test_api.py           ← Tests automatizados
│   ├── client_example.py     ← Cliente Python
│   └── examples/
│       ├── sample_corpus.txt
│       └── sample_memory.tmx
│
├── 🚀 Scripts de Inicio
│   ├── start.sh              ← Linux/Mac
│   └── start.bat             ← Windows
│
├── ⚙️ Configuración
│   ├── .env.example
│   └── .gitignore
│
├── 📦 TermSuite JAR (colocar aquí)
│   └── termsuite/
│       └── termsuite-core-3.0.10.jar
│
└── 💾 Datos (generado automáticamente)
    └── data/
        ├── uploads/
        ├── corpus/
        └── outputs/
```

## 🎓 Flujo de Aprendizaje Recomendado

### Nivel 1: Usuario Básico
1. Lee [QUICKSTART.md](QUICKSTART.md)
2. Obtén el JAR siguiendo [HOW_TO_GET_JAR.md](HOW_TO_GET_JAR.md)
3. Ejecuta `start.sh` o `start.bat`
4. Prueba con los ejemplos en `examples/`

### Nivel 2: Usuario Avanzado
1. Lee [README.md](README.md) completo
2. Ejecuta [test_api.py](test_api.py)
3. Usa [client_example.py](client_example.py) como base
4. Integra en tu proyecto

### Nivel 3: Desarrollador
1. Estudia [ARCHITECTURE.md](ARCHITECTURE.md)
2. Revisa el código en `app/`
3. Modifica y extiende según necesites
4. Contribuye mejoras

## 🔗 Enlaces Útiles

- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **TermSuite GitHub:** https://github.com/termsuite/termsuite-core
- **TermSuite Docs:** https://termsuite.github.io/

## ❓ ¿Necesitas Ayuda?

1. **Problemas de instalación:** Ver [HOW_TO_GET_JAR.md](HOW_TO_GET_JAR.md)
2. **Problemas de uso:** Ver [README.md](README.md) sección Troubleshooting
3. **Dudas técnicas:** Ver [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Inicio rápido:** Ver [QUICKSTART.md](QUICKSTART.md)

## 📝 Notas

- Todos los archivos `.md` están en formato Markdown
- Los scripts `.sh` son para Linux/Mac
- Los scripts `.bat` son para Windows
- La documentación está en español e inglés según el contexto
