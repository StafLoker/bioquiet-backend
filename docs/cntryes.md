# Dataset CNTRYES: preparación y funcionamiento

## Qué es CNTRYES

CNTRYES es la base de datos del Formulario Normalizado de Datos (FND) de la
Red Natura 2000 en España. Mientras que el shapefile del ministerio solo
contiene geometrías e identificadores, CNTRYES contiene toda la información
ecológica y descriptiva de cada espacio: hábitats, especies, amenazas,
organismo gestor, etc.

La publica el Ministerio para la Transición Ecológica (MITECO) en formato
Microsoft Access (`.accdb`). Está compilada a partir de los datos que España
remite a la Comisión Europea a través de la Agencia Europea de Medio Ambiente
(AEMA/EEA).

## Descarga

A diferencia del shapefile, este fichero sí se puede descargar con `curl`:

```bash
curl -L -o raw-data/cntryes.zip \
  "https://www.miteco.gob.es/content/dam/miteco/es/biodiversidad/servicios/banco-datos-naturaleza/informacion-disponible/cntryes/Natura2000_end2023_ES_20250423.zip"
```

El ZIP pesa ~9 MB y contiene un único fichero:
`Natura2000_end2023_ES_20250423.accdb` (96 MB descomprimido).

```bash
cd raw-data
unzip cntryes.zip
cd ..
```

## Herramientas necesarias

**mdbtools** permite leer ficheros Access desde la línea de comandos sin
necesitar Microsoft Office ni Wine.

```bash
brew install mdbtools
```

## Estructura de la base de datos

La base de datos tiene 26 tablas. Las que usa el backend son:

```
NATURA2000SITES  ← información general de cada espacio (área, fechas, descripción)
HABITATS         ← hábitats del Anexo I de la Directiva Hábitat presentes en el espacio
SPECIES          ← especies de los Anexos I/II (aves, mamíferos, plantas, invertebrados...)
IMPACT           ← amenazas y presiones sobre el espacio
MANAGEMENT       ← organismo gestor y planes de gestión
```

Hay otras tablas auxiliares (taxonomía, bioregiones, tipos de propiedad) que
no se usan por ahora.

### Inspeccionar la base de datos

```bash
# Listar todas las tablas
mdb-tables raw-data/Natura2000_end2023_ES_20250423.accdb

# Ver las primeras filas de una tabla
mdb-export raw-data/Natura2000_end2023_ES_20250423.accdb NATURA2000SITES | head -3
```

### Campos relevantes de cada tabla

**NATURA2000SITES**

```
SITECODE         ← código oficial (ES0000001), clave de unión con el GeoJSON
SITENAME         ← nombre del espacio
SITETYPE         ← A = solo ZEPA, B = ZEPA+LIC, C = solo LIC/ZEC
AREAHA           ← superficie en hectáreas
LONGITUDE        ← longitud del centroide (WGS84)
LATITUDE         ← latitud del centroide (WGS84)
DATE_SPA         ← fecha de declaración como ZEPA
SPA_LEGAL_REFERENCE ← referencia al acto legal de declaración
DOCUMENTATION    ← descripción ecológica del espacio (texto libre)
QUALITY          ← calidad de los datos
OTHERCHARACT     ← otras características del espacio
```

**HABITATS**

```
SITECODE         ← clave de unión
HABITATCODE      ← código Natura 2000 del hábitat (ej: 3260)
DESCRIPTION      ← nombre del hábitat en inglés
HABITAT_PRIORITY ← 1 si es hábitat prioritario (*)
COVER_HA         ← superficie cubierta en hectáreas
REPRESENTATIVITY ← representatividad: A (excelente), B (buena), C (significativa)
CONSERVATION     ← estado de conservación: A, B, C
GLOBAL_ASSESSMENT← evaluación global: A, B, C
```

**SPECIES**

```
SITECODE         ← clave de unión
SPECIESCODE      ← código de la especie (ej: A136 = Charadrius dubius)
SPECIESNAME      ← nombre científico
SPGROUP          ← grupo taxonómico (Birds, Mammals, Plants, Invertebrates...)
POPULATION_TYPE  ← tipo de presencia: p=permanente, r=reproductora, c=concentración, w=invernante
ABUNDANCE_CATEGORY ← abundancia: C (común), R (rara), V (muy rara), P (presente)
CONSERVATION     ← estado de conservación: A, B, C
GLOBAL           ← evaluación global: A, B, C
```

**IMPACT**

```
SITECODE         ← clave de unión
IMPACTCODE       ← código de la amenaza (ej: D01.04 = líneas de ferrocarril)
DESCRIPTION      ← descripción en inglés
INTENSITY        ← intensidad: HIGH, MEDIUM, LOW
OCCURRENCE       ← ubicación: IN (dentro), OUT (fuera), BOTH
IMPACT_TYPE      ← tipo: N (negativo), P (positivo), NP (neutro)
```

**MANAGEMENT**

```
SITECODE         ← clave de unión
ORG_NAME         ← nombre del organismo gestor
ORG_EMAIL        ← email de contacto
MANAG_PLAN_URL   ← URL del plan de gestión
MANAG_CONSERV_MEASURES ← descripción de las medidas de conservación
```

## Relación con el shapefile

El campo `SITECODE` de CNTRYES es el mismo que `localId` en el shapefile y
en el GeoJSON. Es la clave que permite unir ambas fuentes:

```
zepa_simplified.geojson  →  localId = "ES0000001"
CNTRYES NATURA2000SITES  →  SITECODE = "ES0000001"
```

Los 602 espacios ZEPA del GeoJSON están todos presentes en CNTRYES.

## La errata en SITETYPE

CNTRYES usa `SITETYPE` para clasificar los espacios:

```
A → solo ZEPA (Special Protection Area)
B → ZEPA + LIC/ZEC (ambas figuras)
C → solo LIC/ZEC (sin ZEPA)
```

La base de datos tiene 387 espacios tipo A y 1202 tipo B (total 1589 con
figura ZEPA). El número es mayor que los 602 del GeoJSON porque CNTRYES
incluye datos hasta fin de 2023 de toda la Red Natura 2000 europea remitida
por España, mientras que el shapefile del ministerio solo incluye los espacios
del territorio nacional con polígono cartografiado.

## Extracción a JSON

El script `scripts/extract_cntryes.py` lee la base de datos Access con
`mdbtools` y genera cinco ficheros JSON en `src/data/`, uno por tabla:

```bash
python scripts/extract_cntryes.py
```

El script filtra automáticamente para quedarse solo con los 602 ZEPA que
están en `zepa_simplified.geojson`, descartando el resto de espacios Natura
2000 (LIC/ZEC sin figura ZEPA).

```
raw-data/
└── Natura2000_end2023_ES_20250423.accdb   ← base de datos Access (96 MB)

src/data/
├── zepa_simplified.geojson   ← 602 ZEPA, geometrías simplificadas (~12 MB)
├── zepa_sites.json           ← área, fechas, descripción por espacio (~2.2 MB)
├── zepa_habitats.json        ← hábitats Anexo I por espacio (~1 MB)
├── zepa_species.json         ← especies por espacio (~4.5 MB)
├── zepa_impacts.json         ← amenazas y presiones por espacio (~0.7 MB)
└── zepa_management.json      ← organismo gestor por espacio (~0.5 MB)
```

Solo los ficheros de `src/data/` son usados por el backend. El `.accdb`
puede añadirse al `.gitignore`.

## Cómo usa el backend estos ficheros

Al arrancar, el backend carga los seis ficheros en memoria RAM. Cuando llega
una petición con un `bbox`, además de la geometría devuelve los metadatos
ecológicos completos de cada ZEPA que intersecta:

```json
{
  "id": "ES3000009",
  "name": "Cortados y cantiles de los ríos Jarama y Manzanares",
  "ccaa": "Comunidad de Madrid",
  "area_ha": 27983.0,
  "date_spa": "1993-12-01",
  "spa_legal_ref": null,
  "description": "Descripción ecológica del espacio...",
  "quality": "G",
  "habitats": [
    { "code": "6220", "description": "Pseudo-steppe with grasses...", "priority": true, "cover_ha": 120.5, "representativity": "B", "conservation": "B", "global_assessment": "B" }
  ],
  "species": [
    { "code": "A136", "name": "Charadrius dubius", "group": "Birds", "population_type": "c", "abundance": "P", "conservation": "C", "global": "C" }
  ],
  "impacts": [
    { "code": "D01.04", "description": "railway lines, TGV", "intensity": "MEDIUM", "occurrence": "IN", "type": "N" }
  ],
  "management": [
    { "org_name": "Comunidad de Madrid...", "org_email": "...", "plan_url": null, "measures": "..." }
  ],
  "noise_thresholds": { "db_safe": 45, "db_warning": 60 },
  "geometry": { "type": "MultiPolygon", "coordinates": ["..."] }
}
```

## Fuente y licencia

Base de datos CNTRYES, actualización fin de 2023.
Fuente: © Ministerio para la Transición Ecológica y Reto Demográfico (MITECO).
Licencia: CC BY 4.0.
URL: https://www.miteco.gob.es/es/biodiversidad/servicios/banco-datos-naturaleza/informacion-disponible/bdn_cntryes.html
