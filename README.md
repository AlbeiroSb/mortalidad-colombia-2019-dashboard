# Mortalidad No Fetal en Colombia · 2019

Dashboard interactivo desarrollado con **Python + Dash + Plotly** para el análisis de la mortalidad no fetal en Colombia durante el año 2019, con datos oficiales del DANE (EEVV 2019).

## Integrantes del grupo

- _(Completar nombres del grupo de máximo 4 estudiantes)_

## Enlaces de la entrega

- **Aplicación desplegada (Render):** `https://<nombre-servicio>.onrender.com`
- **Repositorio GitHub:** `https://github.com/<usuario>/<repo>`

---

## 1. Introducción del proyecto

Esta aplicación web dinámica transforma microdatos del DANE sobre defunciones no fetales en Colombia (2019) en visualizaciones interactivas. Permite a usuarios no técnicos identificar patrones demográficos, geográficos y de violencia mediante filtros por departamento, mes y sexo, soportando análisis exploratorio en tiempo real.

## 2. Objetivo

Proveer una herramienta accesible y reproducible que responda a preguntas clave:

- ¿Cómo se distribuyen las defunciones por departamento y a lo largo del año?
- ¿Qué ciudades presentan mayor índice de homicidios por arma de fuego?
- ¿Qué grupos etarios concentran la mortalidad?
- ¿Existen diferencias significativas por sexo entre departamentos?
- ¿Cuáles son las principales causas de muerte según la CIE-10?

## 3. Estructura del proyecto

```
proyecto/
├── app.py                  # Aplicación Dash (layout + callbacks)
├── prep_data.py            # Script opcional para regenerar parquets desde XLSX
├── requirements.txt        # Dependencias Python
├── Procfile                # Comando de inicio para Render/Heroku
├── runtime.txt             # Versión Python (3.11.9)
├── render.yaml             # Definición Infrastructure-as-Code para Render
├── .gitignore
├── assets/
│   └── styles.css          # Estilos del dashboard
├── data/                   # Datasets ligeros consumidos por la app
│   ├── mortalidad.parquet  # Microdatos depurados de defunciones 2019
│   ├── codigos.parquet     # Catálogo CIE-10 (códigos de muerte)
│   ├── divipola.parquet    # Divipola DANE (depto/municipio)
│   └── coords.parquet      # Coordenadas geográficas de municipios
└── README.md
```

## 4. Requisitos

| Paquete   | Versión  | Propósito                              |
|-----------|----------|----------------------------------------|
| Python    | 3.11.9   | Runtime                                |
| dash      | 2.17.1   | Framework de aplicaciones web reactivo |
| plotly    | 5.24.1   | Gráficos interactivos                  |
| pandas    | 2.2.3    | Procesamiento de datos                 |
| pyarrow   | 17.0.0   | Lectura de archivos Parquet            |
| gunicorn  | 22.0.0   | WSGI server para producción            |

> Las versiones están fijadas en `requirements.txt` para builds reproducibles.

## 5. Despliegue en Render (PaaS)

1. Crear cuenta en [Render](https://render.com) y conectar GitHub.
2. **New +** → **Web Service** → seleccionar el repositorio.
3. Configurar:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server --workers 2 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT`
   - **Plan:** Free
4. Render detecta automáticamente `Procfile` y `render.yaml`; se puede omitir la configuración manual si se usa Blueprint.
5. Al completar el deploy, Render entrega una URL pública (`https://<servicio>.onrender.com`).

Notas:

- El plan free de Render duerme tras 15 min de inactividad; el primer request tras el sueño tarda ~30 s.
- Los parquets viajan en el repositorio (peso total ≈ 1.6 MB), por lo que no se requiere almacenamiento externo.

## 6. Software / Stack

- **Lenguaje:** Python 3.11
- **Frontend reactivo:** Dash 2.17 (React.js bajo el capó)
- **Visualización:** Plotly Express + Plotly Graph Objects
- **Datos:** Pandas + PyArrow (Parquet)
- **Mapas:** `scatter_mapbox` con tiles de OpenStreetMap (sin token requerido)
- **Despliegue:** Render (gunicorn como WSGI server)
- **Fuente de datos:** DANE — Estadísticas Vitales EEVV 2019  
  https://microdatos.dane.gov.co/index.php/catalog/696

## 7. Instalación local

Clonar y ejecutar:

```bash
git clone https://github.com/<usuario>/<repo>.git
cd <repo>
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

La app queda disponible en `http://127.0.0.1:8050`.

Regenerar los parquets desde los XLSX del DANE (opcional):

```bash
# Colocar Anexo1.NoFetal2019_CE_15-03-23.xlsx,
#          Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx,
#          Divipola_CE_.xlsx  dentro de la carpeta fuentes/
python prep_data.py
```

## 8. Visualizaciones y hallazgos

> Capturas: ubicar los PNG en `docs/img/` y reemplazar los placeholders.

### 8.1. Mapa de muertes por departamento
`scatter_mapbox` con burbujas proporcionales al total de defunciones, centradas en el centroide de cada departamento.

- **Hallazgo:** Bogotá D.C. (≈38.7k), Antioquia (≈34.5k) y Valle del Cauca (≈28.4k) concentran el mayor volumen absoluto, alineado con su tamaño poblacional.

### 8.2. Total de muertes por mes (línea)
Serie temporal de defunciones por mes.

- **Hallazgo:** La curva es relativamente estable a lo largo del año, con picos leves en enero (≈21.3k) y diciembre (≈21.7k); el mínimo ocurre en febrero (≈18.0k), consistente con el menor número de días del mes.

### 8.3. Top 5 ciudades más violentas (barras)
Homicidios filtrados por CIE-10 `X95*` (agresión con arma de fuego y no especificadas).

- **Hallazgo (sin filtro):** Cali (971), Bogotá D.C. (601), Medellín (428), Barranquilla (260) y Cúcuta (206) lideran. Cali registra prácticamente el doble que Bogotá pese a tener un cuarto de la población — indicador relevante para política pública.

### 8.4. Top 10 ciudades con menor mortalidad (circular)
Pie donut con los 10 municipios con menor cantidad de defunciones registradas (>0).

- **Hallazgo:** Predominan municipios pequeños del Amazonas, Vaupés y Guainía. Útil para contextualizar el peso relativo en el agregado nacional.

### 8.5. Top 10 causas de muerte (tabla)
Conteo por `COD_MUERTE` (4 caracteres CIE-10) cruzado con catálogo oficial.

- **Hallazgo:** El **Infarto agudo del miocardio (I219)** lidera con ~35.1k casos, seguido por **EPOC no especificada (J449)** ~7.2k y **EPOC con infección aguda (J440)** ~6.4k — patrón clásico de transición epidemiológica.

### 8.6. Muertes por sexo y departamento (barras apiladas)
Comparación hombre/mujer/indeterminado por departamento.

- **Hallazgo:** Predominio masculino en todos los departamentos. La brecha es mayor en zonas con alta mortalidad violenta (Valle, Antioquia).

### 8.7. Distribución por categoría etaria (histograma)
Agrupación de `GRUPO_EDAD1` según la tabla del enunciado: Mortalidad neonatal → Longevidad.

- **Hallazgo:** La categoría **Vejez (60–84)** concentra la mayor parte de las defunciones, seguida por **Longevidad/Centenarios (85+)**. Mortalidad neonatal e infantil siguen siendo relevantes en términos absolutos.

## 9. Filtros interactivos

Todos los gráficos (excepto la línea de meses, que muestra siempre la serie completa) reaccionan a:

- **Departamento** (todos los departamentos DANE)
- **Mes** (1–12)
- **Sexo** (Hombre / Mujer / Indeterminado)

Los KPI superiores (Total, Homicidios, Suicidios, Accidentes) también se actualizan en tiempo real vía callbacks de Dash.

---

**Fuente de datos:** DANE — Estadísticas Vitales (EEVV) 2019.  
**Licencia datos:** Datos abiertos DANE.  
**Licencia código:** MIT (sugerida).
