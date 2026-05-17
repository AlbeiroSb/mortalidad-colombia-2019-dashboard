"""
Script de preparación de datos.
Convierte los .xlsx originales del DANE a archivos .parquet ligeros que
consume la aplicación (carpeta data/).

Ejecutar solo si se desean regenerar los parquet desde los Excel fuente:
    python prep_data.py
"""
import os
from pathlib import Path
import pandas as pd

SRC = Path(__file__).parent / "fuentes"   # carpeta opcional con los xlsx originales
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)


def main():
    # 1. Mortalidad No fetal 2019
    df = pd.read_excel(
        SRC / "Anexo1.NoFetal2019_CE_15-03-23.xlsx",
        sheet_name="No_Fetales_2019",
        engine="calamine",
    )
    keep = ["COD_DEPARTAMENTO", "COD_MUNICIPIO", "MES", "SEXO",
            "GRUPO_EDAD1", "MANERA_MUERTE", "COD_MUERTE"]
    out = df[keep].copy()
    for c in ["COD_DEPARTAMENTO", "COD_MUNICIPIO", "MES", "SEXO", "GRUPO_EDAD1"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").astype("Int32")
    out["MANERA_MUERTE"] = out["MANERA_MUERTE"].astype("string")
    out["COD_MUERTE"] = out["COD_MUERTE"].astype("string")
    out.to_parquet(OUT / "mortalidad.parquet", index=False)

    # 2. Codigos CIE-10
    cod = pd.read_excel(
        SRC / "Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx",
        sheet_name="Final", header=8, engine="calamine",
    )
    cod = cod.rename(columns={
        "Capítulo": "CAPITULO",
        "Nombre capítulo": "NOMBRE_CAPITULO",
        "Código de la CIE-10 tres caracteres": "COD3",
        "Descripción  de códigos mortalidad a tres caracteres": "DESC3",
        "Código de la CIE-10 cuatro caracteres": "COD4",
        "Descripcion  de códigos mortalidad a cuatro caracteres": "DESC4",
    })
    cod.to_parquet(OUT / "codigos.parquet", index=False)

    # 3. Divipola
    dv1 = pd.read_excel(SRC / "Divipola_CE_.xlsx", sheet_name="Hoja1", engine="calamine")
    dv1.to_parquet(OUT / "divipola.parquet", index=False)

    dv3 = pd.read_excel(SRC / "Divipola_CE_.xlsx", sheet_name="Hoja3", header=1, engine="calamine")
    dv3.columns = ["COD_DEPARTAMENTO", "DEPARTAMENTO", "COD_MUNICIPIO",
                   "MUNICIPIO", "TIPO", "LON", "LAT"]
    def num(x):
        try: return float(str(x).replace(",", "."))
        except: return None
    dv3["LON"] = dv3["LON"].apply(num)
    dv3["LAT"] = dv3["LAT"].apply(num)
    dv3["COD_DEPARTAMENTO"] = pd.to_numeric(dv3["COD_DEPARTAMENTO"], errors="coerce").astype("Int32")
    dv3["COD_MUNICIPIO"] = pd.to_numeric(dv3["COD_MUNICIPIO"], errors="coerce").astype("Int32")
    dv3.to_parquet(OUT / "coords.parquet", index=False)

    print("OK - parquets generados en", OUT)


if __name__ == "__main__":
    main()
