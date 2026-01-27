#!/usr/bin/env python3
"""
Script para verificar que la reorganización de archivos se completó correctamente
"""

import os
import sys
from pathlib import Path

def check_directory_structure():
    """Verificar que la estructura de directorios es correcta"""
    print("🔍 Verificando estructura de directorios...")
    
    expected_dirs = [
        "docs",
        "tests", 
        "scripts",
        "debug",
        "app",
        "examples",
        "treetagger"
    ]
    
    missing_dirs = []
    for dir_name in expected_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Directorios faltantes: {', '.join(missing_dirs)}")
        return False
    else:
        print("✅ Estructura de directorios correcta")
        return True

def check_docs_folder():
    """Verificar contenido de la carpeta docs"""
    print("\n🔍 Verificando carpeta docs/...")
    
    docs_path = Path("docs")
    if not docs_path.exists():
        print("❌ Carpeta docs/ no existe")
        return False
    
    md_files = list(docs_path.glob("*.md"))
    if len(md_files) < 20:  # Esperamos al menos 20 archivos .md
        print(f"⚠️  Solo {len(md_files)} archivos .md encontrados en docs/")
        return False
    
    # Verificar archivos clave
    key_files = [
        "README.md",
        "QUICKSTART.md", 
        "ARCHITECTURE.md",
        "OPTIMIZACION_UNIFICADA_OLLAMA.md",
        "IMPLEMENTACION_OPTIMIZACION.md"
    ]
    
    missing_files = []
    for file_name in key_files:
        if not (docs_path / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Archivos clave faltantes en docs/: {', '.join(missing_files)}")
        return False
    
    print(f"✅ Carpeta docs/ correcta ({len(md_files)} archivos .md)")
    return True

def check_tests_folder():
    """Verificar contenido de la carpeta tests"""
    print("\n🔍 Verificando carpeta tests/...")
    
    tests_path = Path("tests")
    if not tests_path.exists():
        print("❌ Carpeta tests/ no existe")
        return False
    
    test_files = list(tests_path.glob("test_*.py"))
    if len(test_files) < 20:  # Esperamos al menos 20 archivos de test
        print(f"⚠️  Solo {len(test_files)} archivos test_*.py encontrados")
        return False
    
    # Verificar archivos clave
    key_tests = [
        "test_final_verification.py",
        "test_domain_classification.py",
        "test_ollama_integration.py",
        "test_api.py"
    ]
    
    missing_tests = []
    for test_name in key_tests:
        if not (tests_path / test_name).exists():
            missing_tests.append(test_name)
    
    if missing_tests:
        print(f"❌ Tests clave faltantes: {', '.join(missing_tests)}")
        return False
    
    print(f"✅ Carpeta tests/ correcta ({len(test_files)} archivos de test)")
    return True

def check_scripts_folder():
    """Verificar contenido de la carpeta scripts"""
    print("\n🔍 Verificando carpeta scripts/...")
    
    scripts_path = Path("scripts")
    if not scripts_path.exists():
        print("❌ Carpeta scripts/ no existe")
        return False
    
    # Verificar scripts clave
    key_scripts = [
        "rebuild-docker.bat",
        "rebuild-docker.sh", 
        "verify-changes.py",
        "client_example.py"
    ]
    
    missing_scripts = []
    for script_name in key_scripts:
        if not (scripts_path / script_name).exists():
            missing_scripts.append(script_name)
    
    if missing_scripts:
        print(f"❌ Scripts clave faltantes: {', '.join(missing_scripts)}")
        return False
    
    script_files = list(scripts_path.glob("*"))
    print(f"✅ Carpeta scripts/ correcta ({len(script_files)} archivos)")
    return True

def check_debug_folder():
    """Verificar contenido de la carpeta debug"""
    print("\n🔍 Verificando carpeta debug/...")
    
    debug_path = Path("debug")
    if not debug_path.exists():
        print("❌ Carpeta debug/ no existe")
        return False
    
    debug_files = list(debug_path.glob("debug_*.py"))
    if len(debug_files) < 3:  # Esperamos al menos 3 archivos de debug
        print(f"⚠️  Solo {len(debug_files)} archivos debug_*.py encontrados")
    
    all_files = list(debug_path.glob("*"))
    print(f"✅ Carpeta debug/ correcta ({len(all_files)} archivos)")
    return True

def check_root_cleanliness():
    """Verificar que el directorio raíz está limpio"""
    print("\n🔍 Verificando limpieza del directorio raíz...")
    
    # Archivos que DEBERÍAN estar en la raíz
    expected_root_files = [
        "docker-compose.yml",
        "Dockerfile", 
        "requirements.txt",
        ".env.example",
        ".gitignore",
        ".dockerignore"
    ]
    
    # Archivos que NO deberían estar en la raíz
    unwanted_patterns = [
        "test_*.py",
        "debug_*.py", 
        "*.md",
        "*.bat",
        "*.sh"
    ]
    
    root_files = [f for f in os.listdir(".") if os.path.isfile(f)]
    
    # Verificar archivos no deseados
    unwanted_found = []
    for pattern in unwanted_patterns:
        if "*" in pattern:
            import fnmatch
            matches = [f for f in root_files if fnmatch.fnmatch(f, pattern)]
            unwanted_found.extend(matches)
        else:
            if pattern in root_files:
                unwanted_found.append(pattern)
    
    if unwanted_found:
        print(f"⚠️  Archivos que deberían estar en subcarpetas: {', '.join(unwanted_found)}")
        return False
    
    print("✅ Directorio raíz limpio")
    return True

def check_readme_files():
    """Verificar que existen los README en cada carpeta"""
    print("\n🔍 Verificando archivos README...")
    
    expected_readmes = [
        "docs/README_DOCS.md",
        "tests/README_TESTS.md",
        "scripts/README_SCRIPTS.md", 
        "debug/README_DEBUG.md"
    ]
    
    missing_readmes = []
    for readme_path in expected_readmes:
        if not Path(readme_path).exists():
            missing_readmes.append(readme_path)
    
    if missing_readmes:
        print(f"❌ READMEs faltantes: {', '.join(missing_readmes)}")
        return False
    
    print("✅ Todos los archivos README presentes")
    return True

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DE REORGANIZACIÓN DE ARCHIVOS")
    print("=" * 60)
    
    # Cambiar al directorio del proyecto
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)
    
    print(f"📁 Directorio de trabajo: {project_dir.absolute()}")
    
    checks = [
        ("Estructura de directorios", check_directory_structure),
        ("Carpeta docs/", check_docs_folder),
        ("Carpeta tests/", check_tests_folder), 
        ("Carpeta scripts/", check_scripts_folder),
        ("Carpeta debug/", check_debug_folder),
        ("Limpieza directorio raíz", check_root_cleanliness),
        ("Archivos README", check_readme_files)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {str(e)}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:25} {status}")
    
    print(f"\nResultado: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("\n🎉 ¡REORGANIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("\n📁 Nueva estructura:")
        print("   📚 docs/     - Toda la documentación")
        print("   🧪 tests/    - Todos los archivos de testing")
        print("   📜 scripts/  - Scripts de automatización")
        print("   🔍 debug/    - Archivos de debug y temporales")
        print("   🏗️ app/      - Código fuente principal")
        print("   📁 examples/ - Ejemplos y archivos de muestra")
        print("\n💡 Próximos pasos:")
        print("   1. Ejecutar: python scripts/verify-changes.py")
        print("   2. Probar: python tests/test_final_verification.py")
        print("   3. Reconstruir Docker: scripts/rebuild-docker.bat")
        
        return 0
    else:
        print(f"\n⚠️  {total - passed} verificaciones fallaron")
        print("Revisa los mensajes arriba para identificar problemas")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)