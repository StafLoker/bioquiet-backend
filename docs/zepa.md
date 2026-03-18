# Dataset ZEPA: preparación y funcionamiento

## Requisitos previos

Necesitas tener instalado [Homebrew](https://brew.sh) en macOS. Si no lo tienes,
sigue las instrucciones de su web antes de continuar.

## Herramientas necesarias

Dos herramientas de línea de comandos:

**GDAL** es una librería para leer y convertir ficheros geográficos. Soporta más
de 200 formatos distintos (SHP, GeoJSON, GML, KML...). La usamos a través del
comando `ogr2ogr` para filtrar y convertir el shapefile del ministerio.

**mapshaper** es una herramienta para simplificar geometrías geográficas. Los
polígonos oficiales tienen una precisión altísima (miles de puntos por polígono)
pensada para mapas impresos en papel A0. Para una app móvil es completamente
innecesaria y hace los ficheros muy pesados. mapshaper los adelgaza manteniendo
la forma reconocible.

```bash
brew install gdal
npm install -g mapshaper
```

Si no tienes Node.js instalado:

```bash
brew install node
npm install -g mapshaper
```

## Estructura de carpetas

```bash
mkdir -p raw-data data
```

Los datos originales del ministerio van en `raw-data/`. El fichero final que
usa el backend va en `data/`. Esta separación permite añadir `raw-data/` al
`.gitignore` y no subir ~400 MB al repositorio.

## Descarga del shapefile

La cartografía oficial de la Red Natura 2000 la publica el Ministerio para la
Transición Ecológica (MITECO). Está actualizada a diciembre de 2024 y tiene
licencia CC BY 4.0 — se puede usar libremente citando la fuente.

El servidor del ministerio bloquea descargas con `curl` o `wget` (devuelve una
página HTML de error en lugar del fichero). Hay que descargarlo con el navegador:

1. Abre esta URL en Safari o Chrome:
   ```
   https://www.mapama.gob.es/app/descargas/descargafichero.aspx?f=rn2000.zip
   ```
2. El fichero `rn2000.zip` (143 MB) se descarga automáticamente.
3. Muévelo a la carpeta de trabajo:
   ```bash
   mv ~/Downloads/rn2000.zip raw-data/
   ```

## Extracción

```bash
cd raw-data
unzip rn2000.zip
cd ..
```

Se extraen estos ficheros:

```
raw-data/
├── PS.RNATURA2000_2024_P.shp      ← polígonos (el que usamos)
├── PS.RNATURA2000_2024_P.dbf      ← tabla de atributos
├── PS.RNATURA2000_2024_P.prj      ← sistema de coordenadas
├── PS.RNATURA2000_2024_P.shx      ← índice
├── PS.RNATURA2000_2024_P.cpg      ← codificación de texto
├── PS.RNATURA2000_2024_P.shp.xml  ← metadatos
├── PS.RNATURA2000_2024_C.shp      ← líneas costeras (no lo usamos)
├── PS.RNATURA2000_2024_C.*        ← ficheros auxiliares del anterior
└── Rnatura2024_ATOM_dd.xlsx       ← tabla de metadatos en Excel
```

Un Shapefile no es un único fichero sino un conjunto de 6 que funcionan juntos.
El `.shp` guarda las geometrías (los polígonos dibujados), el `.dbf` guarda los
atributos de cada polígono (nombre, código, tipo de espacio...), y el `.prj`
indica en qué sistema de coordenadas están expresadas las geometrías. Sin el
`.prj` no se sabe si las coordenadas son metros o grados.

## Qué contiene el shapefile

Antes de filtrar conviene inspeccionar qué hay dentro. El comando `ogrinfo` con
los flags `-al -so` muestra un resumen de la capa: cuántos registros tiene,
en qué sistema de coordenadas está, y qué campos tiene cada registro.

```bash
ogrinfo -al -so "raw-data/PS.RNATURA2000_2024_P.shp"
```

Salida real:

```
Layer name: PS.RNATURA2000_2024_P
Geometry: Polygon
Feature Count: 1636
Extent: (-271621.38, 3892006.15) - (1132649.81, 4896810.47)
Layer SRS WKT: PROJCRS["ETRS89 / UTM zone 30N" ...]

gml_id     : String   ← identificador técnico INSPIRE (ej: ES.IEPNB.PS_NATURA2000.ES0000001)
localId    : String   ← código oficial Red Natura 2000 (ej: ES0000058)
versionId  : String   ← versión del dato (ej: Dic2024)
desigSch0  : String   ← URL del esquema de clasificación
desig0     : String   ← tipo de espacio protegido (LIC, ZEC o ZEPA)
percentag0 : String   ← porcentaje del espacio con esta figura
legalFDat0 : String   ← fecha de declaración legal
legalFDoc0 : String   ← URL del documento legal (BOE, etc.)
desigSch1  : String   ← igual que los anteriores para una segunda figura
desig1     : String
percentag1 : String
legalFDat1 : String
legalFDoc1 : String
desigSch2  : String   ← igual para una tercera figura
desig2     : String
percentag2 : String
legalFDat2 : String
legalFDoc2 : String
language   : String   ← idioma de los metadatos (spa)
SOName     : String   ← nombre del espacio (ej: "Sierras de Guadarrama")
siteProtec : String   ← clasificación general de protección
```

`Feature Count: 1636` significa que hay 1636 espacios protegidos en el fichero,
pero no todos son ZEPA. El dataset mezcla LIC (Lugares de Importancia Comunitaria),
ZEC (Zonas Especiales de Conservación) y ZEPA (Zonas de Especial Protección para
las Aves).

Un mismo espacio puede tener varias figuras de protección a la vez. Por eso el
tipo se guarda en tres campos (`desig0`, `desig1`, `desig2`): un espacio puede
ser LIC + ZEC + ZEPA simultáneamente. El ejemplo real de las Illas Cíes:

```
OGRFeature(PS.RNATURA2000_2024_P):0
  localId    = ES0000001
  desig0     = .../SiteOfCommunityImportance    ← LIC desde 2004
  desig1     = .../SpecialAreaOfConservation    ← ZEC desde 2014
  desig2     = .../SpecialProtectionArea        ← ZEPA desde 1988
  SOName     = Illas Cíes
  MULTIPOLYGON (((11599.39 4694703.73, ...)))   ← coordenadas en metros
```

Las coordenadas están en metros (sistema UTM), no en grados. Hay que convertirlas
a WGS84 (grados decimales) para que el GPS del móvil las entienda.

## La errata en los datos del ministerio

Al analizar los valores distintos que tiene el campo `desig` aparece un problema:

```bash
ogrinfo -al "raw-data/PS.RNATURA2000_2024_P.shp" \
  | grep "desig0\|desig1\|desig2" \
  | grep -v "desigSch\|percentag\|legalF" \
  | sort | uniq -c | sort -rn
```

Resultado:

```
1376   desig2 = (null)
1294   desig1 = ...SpecialAreaOfConservation
1294   desig0 = ...SiteOfCommunityImportance
 342   desig0 = ...SpecialProtecionArea        ← falta la 't'
 260   desig2 = ...SpecialProtectionArea       ← correcto
```

El dataset oficial del ministerio tiene una errata tipográfica: 342 registros
escriben `SpecialProtecionArea` en lugar de `SpecialProtectionArea` (falta la
`t` en "Protection"). Son dos valores distintos en el mismo campo del mismo
fichero oficial.

```
SpecialProtectionArea   → 260 registros  (correcto)
SpecialProtecionArea    → 342 registros  (errata)
```

El total real de ZEPA es 602 (260 + 342). Si se filtra solo por la grafía
correcta se pierden 342 zonas y el mapa queda claramente incompleto comparado
con la vista previa oficial del ministerio.

El filtro correcto usa el comodín `%` de SQL para capturar ambas variantes a
la vez. `%SpecialProte%Area%` significa "cualquier cadena que contenga
`SpecialProte` seguido en algún punto de `Area`", lo que captura tanto
`SpecialProtectionArea` como `SpecialProtecionArea`.

## Conversión a GeoJSON

`ogr2ogr` hace tres cosas en un solo comando: filtra los registros que son ZEPA,
convierte las coordenadas de metros UTM a grados WGS84 (`-t_srs EPSG:4326`), y
exporta el resultado a GeoJSON.

```bash
ogr2ogr \
  -f GeoJSON \
  -t_srs EPSG:4326 \
  -where "desig0 LIKE '%SpecialProte%Area%' OR desig1 LIKE '%SpecialProte%Area%' OR desig2 LIKE '%SpecialProte%Area%'" \
  raw-data/zepa_full.geojson \
  "raw-data/PS.RNATURA2000_2024_P.shp"
```

Verificar que el resultado tiene 602 features:

```bash
ogrinfo -al -so raw-data/zepa_full.geojson
# Feature Count: 602
```

El fichero resultante pesa 90 MB porque cada polígono conserva la precisión
original del ministerio (escala 1:50.000, miles de puntos por polígono).

## Simplificación

Para una app móvil no necesitamos esa precisión. `mapshaper -simplify 5%`
mantiene el 5% de los puntos de cada polígono, lo que reduce el fichero de 90
MB a 5 MB sin diferencia visible en pantalla de móvil.

```bash
mapshaper raw-data/zepa_full.geojson -simplify 5% -o data/zepa_simplified.geojson
```

Verificar el tamaño final:

```bash
ls -lh data/zepa_simplified.geojson
# ~5 MB
```

El aviso `461 intersections could not be repaired` que puede aparecer es normal:
son artefactos en los bordes entre comunidades autónomas del dataset original,
no afectan al funcionamiento del point-in-polygon en la app.

## Resultado final

```
raw-data/
├── rn2000.zip                       ← ZIP original (143 MB)
├── PS.RNATURA2000_2024_P.shp        ← 1636 espacios Natura 2000, UTM (192 MB)
├── PS.RNATURA2000_2024_P.dbf
├── PS.RNATURA2000_2024_P.prj
├── PS.RNATURA2000_2024_P.shx
├── PS.RNATURA2000_2024_P.cpg
├── PS.RNATURA2000_2024_P.shp.xml
├── PS.RNATURA2000_2024_C.*
├── Rnatura2024_ATOM_dd.xlsx
└── zepa_full.geojson                ← 602 ZEPA, WGS84, sin simplificar (90 MB)

data/
└── zepa_simplified.geojson          ← 602 ZEPA, WGS84, simplificado (~5 MB) ✓
```

Solo `data/zepa_simplified.geojson` es usado por el backend. Todo lo demás
puede añadirse a `.gitignore`.

## Cómo usa el backend este fichero

Al arrancar, el backend carga `zepa_simplified.geojson` en memoria RAM una sola
vez. Las peticiones de la app llegan con un `bbox` (rectángulo que representa
el área visible en el mapa) y el backend devuelve solo las ZEPA que intersectan
ese rectángulo:

```
GET /api/v1/zepa?lonWest=-3.72&latSouth=40.38&lonEast=-3.68&latNorth=40.42
```

Si el usuario está en una zona sin ZEPA:

```json
{
  "status": "success",
  "message": "No ZEPA zones found in the requested area.",
  "data": [],
  "metadata": { "count": 0 }
}
```

Si está dentro de una ZEPA, la app recibe el polígono y puede hacer el cálculo
de point-in-polygon para mostrar la advertencia de ruido:

```json
{
  "status": "success",
  "message": "1 ZEPA zone found in the requested area.",
  "data": [
    {
      "id": "ES3000009",
      "name": "Cortados y cantiles de los ríos Jarama y Manzanares",
      "noise_thresholds": { "db_safe": 45, "db_warning": 60 },
      "area_ha": 27983.0,
      "date_spa": "1993-12-01",
      "spa_legal_ref": null,
      "description": "Descripción ecológica...",
      "quality": "G",
      "habitats": [...],
      "species": [...],
      "impacts": [...],
      "management": [...],
      "geometry": { "type": "MultiPolygon", "coordinates": [...] }
    }
  ],
  "metadata": { "count": 1 }
}
```

## Fuente y licencia

Cartografía de la Red Natura 2000, actualización diciembre 2024.
Fuente: © Ministerio para la Transición Ecológica y Reto Demográfico (MITECO).
Licencia: CC BY 4.0.
URL: https://www.miteco.gob.es/es/cartografia-y-sig/ide/descargas/biodiversidad/rn2000.html
URL: https://www.mapama.gob.es/ide/metadatos/srv/api/records/0d427e21-be52-4723-b78e-8b00a43319cb?language=all
