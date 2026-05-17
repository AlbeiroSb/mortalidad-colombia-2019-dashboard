"""
Dashboard de Mortalidad en Colombia 2019
Aplicacion web dinamica con Dash + Plotly.

Despliegue: Render (gunicorn app:server)
"""
import os
from pathlib import Path

import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"

df = pd.read_parquet(DATA_DIR / "mortalidad.parquet")
codigos = pd.read_parquet(DATA_DIR / "codigos.parquet")
divipola = pd.read_parquet(DATA_DIR / "divipola.parquet")
coords = pd.read_parquet(DATA_DIR / "coords.parquet")

# Normalizacion tipos
df["MES"] = df["MES"].astype("Int16")
df["SEXO"] = df["SEXO"].astype("Int16")
df["GRUPO_EDAD1"] = df["GRUPO_EDAD1"].astype("Int16")
df["COD_DEPARTAMENTO"] = df["COD_DEPARTAMENTO"].astype("Int32")
df["COD_MUNICIPIO"] = df["COD_MUNICIPIO"].astype("Int32")
df["COD_MUERTE"] = df["COD_MUERTE"].astype(str).str.strip()

# Diccionario departamento
dep_dict = (
    divipola[["COD_DEPARTAMENTO", "DEPARTAMENTO"]]
    .drop_duplicates()
    .set_index("COD_DEPARTAMENTO")["DEPARTAMENTO"]
    .to_dict()
)

# Diccionario municipio (cod_depto, cod_muni) -> nombre
muni_dict = (
    divipola.set_index(["COD_DEPARTAMENTO", "COD_MUNICIPIO"])["MUNICIPIO"].to_dict()
)

# Codigos CIE-10 a nombre (4 caracteres)
cod4_dict = dict(zip(codigos["COD4"].astype(str), codigos["DESC4"].astype(str)))
cod3_dict = dict(zip(codigos["COD3"].astype(str), codigos["DESC3"].astype(str)))

# Centroides departamento (promedio coordenadas municipios)
dep_coords = (
    coords.dropna(subset=["LAT", "LON"])
    .groupby("COD_DEPARTAMENTO")[["LAT", "LON"]]
    .mean()
    .reset_index()
)

# Nombres de meses
MESES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}
SEXO_MAP = {1: "Hombre", 2: "Mujer", 3: "Indeterminado"}

# Mapeo categorias de edad segun la tabla del enunciado
EDAD_BINS = [
    ("Mortalidad neonatal",    range(0, 5)),
    ("Mortalidad infantil",    range(5, 7)),
    ("Primera infancia",       range(7, 9)),
    ("Niñez",                  range(9, 11)),
    ("Adolescencia",           range(11, 12)),
    ("Juventud",               range(12, 14)),
    ("Adultez temprana",       range(14, 17)),
    ("Adultez intermedia",     range(17, 20)),
    ("Vejez",                  range(20, 25)),
    ("Longevidad / Centenarios", range(25, 29)),
    ("Edad desconocida",       range(29, 30)),
]
EDAD_LOOKUP = {v: lab for lab, rng in EDAD_BINS for v in rng}
EDAD_ORDER = [lab for lab, _ in EDAD_BINS]

# Pre-mapeo categoria edad
df["CAT_EDAD"] = df["GRUPO_EDAD1"].map(EDAD_LOOKUP).fillna("Edad desconocida")
df["DEPARTAMENTO"] = df["COD_DEPARTAMENTO"].map(dep_dict)
df["SEXO_LBL"] = df["SEXO"].map(SEXO_MAP).fillna("Indeterminado")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    title="Mortalidad Colombia 2019",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # expuesto para gunicorn

DEPTO_OPCIONES = [{"label": "Todos", "value": "ALL"}] + [
    {"label": v, "value": int(k)} for k, v in sorted(dep_dict.items(), key=lambda x: x[1])
]
MES_OPCIONES = [{"label": "Todos", "value": "ALL"}] + [
    {"label": v, "value": k} for k, v in MESES.items()
]
SEXO_OPCIONES = [
    {"label": "Todos", "value": "ALL"},
    {"label": "Hombre", "value": 1},
    {"label": "Mujer", "value": 2},
    {"label": "Indeterminado", "value": 3},
]


def kpi_card(title, value, color="#0d6efd"):
    return html.Div(
        [
            html.Div(title, className="kpi-title"),
            html.Div(value, className="kpi-value", style={"color": color}),
        ],
        className="kpi-card",
    )


app.layout = html.Div(
    [
        html.Header(
            [
                html.H1("Mortalidad No Fetal en Colombia · 2019"),
                html.P(
                    "Dashboard interactivo basado en datos del DANE (EEVV 2019). "
                    "Use los filtros para explorar la informacion."
                ),
            ],
            className="header",
        ),
        html.Section(
            [
                html.Div(
                    [
                        html.Label("Departamento"),
                        dcc.Dropdown(id="f-depto", options=DEPTO_OPCIONES, value="ALL", clearable=False),
                    ],
                    className="filter-col",
                ),
                html.Div(
                    [
                        html.Label("Mes"),
                        dcc.Dropdown(id="f-mes", options=MES_OPCIONES, value="ALL", clearable=False),
                    ],
                    className="filter-col",
                ),
                html.Div(
                    [
                        html.Label("Sexo"),
                        dcc.Dropdown(id="f-sexo", options=SEXO_OPCIONES, value="ALL", clearable=False),
                    ],
                    className="filter-col",
                ),
            ],
            className="filters",
        ),
        html.Section(id="kpis", className="kpis"),
        html.Section(
            [
                html.Div(
                    [html.H3("1. Distribución total de muertes por departamento"),
                     dcc.Graph(id="g-mapa")],
                    className="card wide",
                ),
                html.Div(
                    [html.H3("2. Total de muertes por mes"),
                     dcc.Graph(id="g-lineas")],
                    className="card",
                ),
                html.Div(
                    [html.H3("3. Top 5 ciudades más violentas (Homicidios X95)"),
                     dcc.Graph(id="g-violentas")],
                    className="card",
                ),
                html.Div(
                    [html.H3("4. Top 10 ciudades con menor mortalidad"),
                     dcc.Graph(id="g-menores")],
                    className="card",
                ),
                html.Div(
                    [html.H3("6. Muertes por sexo en cada departamento"),
                     dcc.Graph(id="g-sexo-depto")],
                    className="card wide",
                ),
                html.Div(
                    [html.H3("7. Distribución por grupo etario (ciclo de vida)"),
                     dcc.Graph(id="g-edad")],
                    className="card wide",
                ),
                html.Div(
                    [
                        html.H3("5. Top 10 causas de muerte en Colombia"),
                        dash_table.DataTable(
                            id="t-causas",
                            columns=[
                                {"name": "Código", "id": "COD"},
                                {"name": "Causa", "id": "NOMBRE"},
                                {"name": "Total casos", "id": "TOTAL", "type": "numeric"},
                            ],
                            page_size=10,
                            style_cell={
                                "fontFamily": "Inter, system-ui, sans-serif",
                                "fontSize": "14px",
                                "padding": "8px",
                                "textAlign": "left",
                            },
                            style_header={
                                "backgroundColor": "#0d6efd",
                                "color": "white",
                                "fontWeight": "bold",
                            },
                            style_data_conditional=[
                                {"if": {"row_index": "odd"}, "backgroundColor": "#f6f8fb"}
                            ],
                        ),
                    ],
                    className="card wide",
                ),
            ],
            className="grid",
        ),
        html.Footer(
            html.P(
                "Fuente: DANE - Estadísticas Vitales EEVV 2019 · "
                "Visualización: Plotly + Dash · Despliegue: Render"
            )
        ),
    ],
    className="app",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def aplicar_filtros(depto, mes, sexo):
    d = df
    if depto != "ALL":
        d = d[d["COD_DEPARTAMENTO"] == int(depto)]
    if mes != "ALL":
        d = d[d["MES"] == int(mes)]
    if sexo != "ALL":
        d = d[d["SEXO"] == int(sexo)]
    return d


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@app.callback(
    Output("kpis", "children"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_kpis(depto, mes, sexo):
    d = aplicar_filtros(depto, mes, sexo)
    total = len(d)
    hom = (d["MANERA_MUERTE"] == "Homicidio").sum()
    sui = (d["MANERA_MUERTE"] == "Suicidio").sum()
    acc = (d["MANERA_MUERTE"] == "Accidente").sum()
    return [
        kpi_card("Total defunciones", f"{total:,}".replace(",", "."), "#0d6efd"),
        kpi_card("Homicidios", f"{hom:,}".replace(",", "."), "#dc3545"),
        kpi_card("Suicidios", f"{sui:,}".replace(",", "."), "#6f42c1"),
        kpi_card("Accidentes", f"{acc:,}".replace(",", "."), "#fd7e14"),
    ]


@app.callback(
    Output("g-mapa", "figure"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_mapa(depto, mes, sexo):
    d = aplicar_filtros(depto, mes, sexo)
    agg = d.groupby("COD_DEPARTAMENTO").size().reset_index(name="MUERTES")
    agg = agg.merge(dep_coords, on="COD_DEPARTAMENTO", how="left")
    agg["DEPARTAMENTO"] = agg["COD_DEPARTAMENTO"].map(dep_dict)
    fig = px.scatter_mapbox(
        agg.dropna(subset=["LAT", "LON"]),
        lat="LAT",
        lon="LON",
        size="MUERTES",
        color="MUERTES",
        hover_name="DEPARTAMENTO",
        hover_data={"MUERTES": ":,d", "LAT": False, "LON": False},
        color_continuous_scale="OrRd",
        size_max=55,
        zoom=4.2,
        center={"lat": 4.6, "lon": -74.1},
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        height=520,
    )
    return fig


@app.callback(
    Output("g-lineas", "figure"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_lineas(depto, mes, sexo):
    # Para el grafico de meses ignoramos el filtro de mes para mostrar la serie completa
    d = aplicar_filtros(depto, "ALL", sexo)
    serie = d.groupby("MES").size().reindex(range(1, 13), fill_value=0).reset_index(name="MUERTES")
    serie["MES_LBL"] = serie["MES"].map(MESES)
    fig = px.line(
        serie, x="MES_LBL", y="MUERTES", markers=True,
        labels={"MES_LBL": "Mes", "MUERTES": "Defunciones"},
    )
    fig.update_traces(line=dict(color="#0d6efd", width=3), marker=dict(size=10))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380)
    return fig


@app.callback(
    Output("g-violentas", "figure"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_violentas(depto, mes, sexo):
    d = aplicar_filtros(depto, mes, sexo)
    # Homicidios con COD_MUERTE X95* (incluye no especificadas X958/X959)
    d = d[d["MANERA_MUERTE"] == "Homicidio"]
    d = d[d["COD_MUERTE"].str.startswith("X95", na=False)]
    if d.empty:
        return px.bar(title="Sin datos para el filtro seleccionado")
    agg = (
        d.groupby(["COD_DEPARTAMENTO", "COD_MUNICIPIO"])
        .size()
        .reset_index(name="MUERTES")
        .sort_values("MUERTES", ascending=False)
        .head(5)
    )
    agg["MUNICIPIO"] = agg.apply(
        lambda r: muni_dict.get((int(r["COD_DEPARTAMENTO"]), int(r["COD_MUNICIPIO"])), "N/D"),
        axis=1,
    )
    fig = px.bar(
        agg.sort_values("MUERTES"),
        x="MUERTES", y="MUNICIPIO",
        orientation="h",
        text="MUERTES",
        color="MUERTES",
        color_continuous_scale="Reds",
        labels={"MUERTES": "Homicidios X95", "MUNICIPIO": ""},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380, coloraxis_showscale=False)
    return fig


@app.callback(
    Output("g-menores", "figure"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_menores(depto, mes, sexo):
    d = aplicar_filtros(depto, mes, sexo)
    agg = (
        d.groupby(["COD_DEPARTAMENTO", "COD_MUNICIPIO"])
        .size()
        .reset_index(name="MUERTES")
    )
    agg = agg[agg["MUERTES"] > 0].sort_values(["MUERTES", "COD_MUNICIPIO"]).head(10)
    agg["MUNICIPIO"] = agg.apply(
        lambda r: muni_dict.get((int(r["COD_DEPARTAMENTO"]), int(r["COD_MUNICIPIO"])), "N/D"),
        axis=1,
    )
    fig = px.pie(
        agg, names="MUNICIPIO", values="MUERTES", hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380, showlegend=False)
    return fig


@app.callback(
    Output("g-sexo-depto", "figure"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
)
def update_sexo_depto(depto, mes):
    d = aplicar_filtros(depto, mes, "ALL")
    agg = (
        d.groupby(["DEPARTAMENTO", "SEXO_LBL"])
        .size()
        .reset_index(name="MUERTES")
    )
    # Ordenar por total para legibilidad
    order = (
        agg.groupby("DEPARTAMENTO")["MUERTES"].sum()
        .sort_values(ascending=True).index.tolist()
    )
    fig = px.bar(
        agg, x="MUERTES", y="DEPARTAMENTO", color="SEXO_LBL",
        orientation="h", barmode="stack",
        category_orders={"DEPARTAMENTO": order, "SEXO_LBL": ["Hombre", "Mujer", "Indeterminado"]},
        color_discrete_map={"Hombre": "#0d6efd", "Mujer": "#e83e8c", "Indeterminado": "#adb5bd"},
        labels={"MUERTES": "Defunciones", "DEPARTAMENTO": "", "SEXO_LBL": "Sexo"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=620, legend_title_text="Sexo")
    return fig


@app.callback(
    Output("g-edad", "figure"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_edad(depto, mes, sexo):
    d = aplicar_filtros(depto, mes, sexo)
    agg = d.groupby("CAT_EDAD").size().reindex(EDAD_ORDER, fill_value=0).reset_index(name="MUERTES")
    fig = px.bar(
        agg, x="CAT_EDAD", y="MUERTES",
        text="MUERTES", color="MUERTES",
        color_continuous_scale="Blues",
        labels={"CAT_EDAD": "Categoría etaria", "MUERTES": "Defunciones"},
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=80),
        height=420,
        coloraxis_showscale=False,
        xaxis_tickangle=-30,
    )
    return fig


@app.callback(
    Output("t-causas", "data"),
    Input("f-depto", "value"),
    Input("f-mes", "value"),
    Input("f-sexo", "value"),
)
def update_tabla(depto, mes, sexo):
    d = aplicar_filtros(depto, mes, sexo)
    agg = (
        d.groupby("COD_MUERTE").size().reset_index(name="TOTAL")
        .sort_values("TOTAL", ascending=False).head(10)
    )
    agg["NOMBRE"] = agg["COD_MUERTE"].map(cod4_dict)
    # fallback: probar 3 caracteres
    mask = agg["NOMBRE"].isna()
    agg.loc[mask, "NOMBRE"] = agg.loc[mask, "COD_MUERTE"].str[:3].map(cod3_dict)
    agg["NOMBRE"] = agg["NOMBRE"].fillna("Sin descripción")
    agg = agg.rename(columns={"COD_MUERTE": "COD"})
    return agg[["COD", "NOMBRE", "TOTAL"]].to_dict("records")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
