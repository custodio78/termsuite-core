# TMX de Prueba - Múltiples Traducciones

## Archivo: `test_multiple_translations.tmx`

Este archivo TMX de prueba está diseñado para verificar el correcto funcionamiento de la extracción de términos con múltiples traducciones.

## Características

### Idiomas
- **Español (es)** - Idioma origen
- **English (en)** - Idioma destino

### Casos de Prueba Incluidos

#### 1. Términos con 3 traducciones diferentes

**válvula** → `valve | tap | faucet`
- Segmento 1: "La válvula de seguridad..." → "safety valve"
- Segmento 2: "Cierre la válvula principal..." → "main tap"
- Segmento 3: "La válvula hidráulica..." → "hydraulic faucet"

**acoplamiento** → `coupling | connection | joint`
- Segmento 1: "El acoplamiento mecánico..." → "mechanical coupling"
- Segmento 2: "Verifique el acoplamiento..." → "connection"
- Segmento 3: "El acoplamiento flexible..." → "flexible joint"

**ajuste** → `adjustment | setting | tuning`
- Segmento 1: "Realice el ajuste de presión..." → "pressure adjustment"
- Segmento 2: "El ajuste mecánico..." → "mechanical setting"
- Segmento 3: "Después del ajuste inicial..." → "initial tuning"

#### 2. Términos con 2 traducciones (variantes regionales)

**elevador** → `elevator | lift`
- Segmento 1: "El elevador de carga..." → "freight elevator"
- Segmento 2: "...utilice el elevador de pasajeros..." → "passenger lift"
- Segmento 3: "El elevador está fuera..." → "elevator"

**bomba** → `pump | pumping unit`
- Segmento 1: "La bomba hidráulica..." → "hydraulic pump"
- Segmento 2: "Instale la bomba de agua..." → "water pumping unit"

**cilindro** → `cylinder | barrel`
- Segmento 1: "El cilindro hidráulico..." → "hydraulic cylinder"
- Segmento 2: "Reemplace el cilindro dañado..." → "damaged barrel"

**motor** → `motor | engine`
- Segmento 1: "El motor eléctrico..." → "electric motor"
- Segmento 2: "Conecte el motor..." → "engine"

**sistema** → `system | setup`
- Segmento 1: "El sistema hidráulico..." → "hydraulic system"
- Segmento 2: "Configure el sistema de control..." → "control setup"

#### 3. Términos con traducción única (control)

**plataforma** → `platform`
- Todas las ocurrencias se traducen consistentemente como "platform"

#### 4. Términos con bullets (prueba de limpieza)

- `a) Verifique el nivel de aceite...`
- `b) Inspeccione las conexiones...`
- `1. Desconecte la alimentación...`

Estos deben limpiarse automáticamente.

## Frecuencias Esperadas

| Término (es) | Frecuencia | Traducciones (en) | Variantes |
|--------------|------------|-------------------|-----------|
| válvula | 4 | valve \| tap \| faucet | 3 |
| elevador | 4 | elevator \| lift | 2 |
| acoplamiento | 4 | coupling \| connection \| joint | 3 |
| bomba | 3 | pump \| pumping unit | 2 |
| cilindro | 3 | cylinder \| barrel | 2 |
| ajuste | 4 | adjustment \| setting \| tuning | 3 |
| plataforma | 3 | platform | 1 |
| motor | 3 | motor \| engine | 2 |
| sistema | 3 | system \| setup | 2 |

## Cómo Usar

### 1. Subir el TMX
```bash
# Desde la interfaz web
1. Click en "Seleccionar Archivo"
2. Elegir: examples/test_multiple_translations.tmx
3. Click en "Subir TMX"
```

### 2. Configurar Idiomas
```
Idioma origen: Español (es)
Idioma de traducción: English (en)
Click en "Aplicar Idiomas"
```

### 3. Configurar Extracción
```
Frecuencia mínima: 1
Top N términos: [vacío]
Palabras mínimas: 1
Palabras máximas: 5
☑ Incluir traducciones
```

### 4. Extraer y Verificar

El Excel resultante debe mostrar:
- Columna "Traducción" con múltiples valores separados por ` | `
- Columna "Variantes" indicando el número de traducciones
- Términos limpios (sin bullets)

## Pruebas con la Herramienta de Búsqueda

Después de subir el TMX, prueba buscar:

```
Búsqueda: "válvula"
Resultado esperado:
✓ ES: Encontrado (frecuencia: 4)
✗ EN: No encontrado

Búsqueda: "valve"
Resultado esperado:
✗ ES: No encontrado
✓ EN: Encontrado (frecuencia: 1)
```

## Casos de Uso Reales

Este TMX simula situaciones reales:

1. **Polisemia**: Un término con múltiples significados
   - "válvula" puede ser valve, tap o faucet según contexto

2. **Variantes regionales**: Diferencias entre inglés británico/americano
   - "elevador" → elevator (US) / lift (UK)

3. **Terminología técnica**: Sinónimos aceptados
   - "motor" vs "engine" en contextos técnicos

4. **Inconsistencias**: Traducciones no estandarizadas
   - Útil para detectar y corregir inconsistencias

## Verificación de Resultados

### Excel Esperado

```
Número | Término      | Frecuencia | Traducción                    | Variantes
-------|--------------|------------|-------------------------------|----------
1      | válvula      | 4          | valve | tap | faucet          | 3
2      | elevador     | 4          | elevator | lift              | 2
3      | acoplamiento | 4          | coupling | connection | joint | 3
4      | ajuste       | 4          | adjustment | setting | tuning | 3
5      | bomba        | 3          | pump | pumping unit          | 2
6      | cilindro     | 3          | cylinder | barrel            | 2
7      | motor        | 3          | motor | engine               | 2
8      | sistema      | 3          | system | setup               | 2
9      | plataforma   | 3          | platform                      | 1
```

## Troubleshooting

Si no ves las múltiples traducciones:
1. Verifica que seleccionaste el idioma correcto (es → en)
2. Asegúrate de marcar "Incluir traducciones"
3. Revisa que aplicaste los idiomas con "Aplicar Idiomas"
4. Usa la herramienta de búsqueda para verificar

## Script de Diagnóstico

```bash
cd termsuite-api
python debug_tmx.py examples/test_multiple_translations.tmx válvula elevador acoplamiento
```

Esto mostrará información detallada sobre cada término.
