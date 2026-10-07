"""Compara un ZIP generado en Colab (celda final de cada notebook) con la corrida local.

Uso:  python scripts/comparar_zip.py <ruta al ZIP> [<otro ZIP> ...]

Compara hoja por hoja el Excel del ZIP con output/IIJP_resultados.xlsx y cada CSV de datos/ con
data/processed/. Antes conviene correr `python scripts/construir.py` para que la referencia local
este al dia. Diferencias esperadas: las hojas de bootstrap (Colab usa 300 replicas y construir.py
500) y la hoja Notas (commit y cantidad de replicas). Cualquier otra diferencia > 1e-6 indica que el
ZIP se genero con otra version del codigo o con otros datos: mirar la linea "Version del codigo" del
LEEME.txt (ver CLAUDE.md, "Colab reutiliza sesiones").
"""
from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ESPERADAS = {'Notas', 'Bootstrap_brechas', 'Bootstrap_pond', 'bootstrap_brechas.csv', 'bootstrap_ponderaciones.csv'}


def _max_dif(a: pd.DataFrame, b: pd.DataFrame) -> float:
    na = a.select_dtypes('number')
    if na.empty:
        return 0.0
    d = (na - b[na.columns]).abs().values
    return float(np.nanmax(d)) if np.isfinite(d).any() else 0.0


def comparar(ruta_zip: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        with zipfile.ZipFile(ruta_zip) as z:
            nombres = z.namelist()
            z.extractall(dest)
        print(f'\n=== {ruta_zip.name}: {sum(n.endswith(".png") for n in nombres)} png, '
              f'{sum(n.endswith(".csv") for n in nombres)} csv')
        leeme = dest / 'LEEME.txt'
        if leeme.exists():
            for linea in leeme.read_text(encoding='utf-8').splitlines()[1:3]:
                print('   ', linea)

        problemas = 0
        loc = pd.read_excel(RAIZ / 'output' / 'IIJP_resultados.xlsx', sheet_name=None)
        col = pd.read_excel(dest / 'IIJP_resultados.xlsx', sheet_name=None)
        for hoja, a in col.items():
            b = loc.get(hoja)
            if b is None or a.shape != b.shape:
                estado, m = 'falta en local' if b is None else f'forma distinta {a.shape} vs {b.shape}', np.nan
            else:
                m = _max_dif(a, b)
                estado = 'ok' if m <= 1e-6 else f'dif max {m:.3g}'
            esperada = hoja in ESPERADAS
            if estado != 'ok' and not esperada:
                problemas += 1
            print(f'    {hoja:22s} {estado}' + ('  (esperable)' if esperada and estado != 'ok' else ''))
        for c in sorted((dest / 'datos').glob('*.csv')):
            ref = RAIZ / 'data' / 'processed' / c.name
            if not ref.exists():
                print(f'    {c.name:30s} no existe en data/processed')
                continue
            a, b = pd.read_csv(c), pd.read_csv(ref)
            m = _max_dif(a, b) if a.shape == b.shape else np.inf
            if m > 1e-6 and c.name not in ESPERADAS:
                problemas += 1
                print(f'    {c.name:30s} dif max {m:.3g}')
        print(f'    -> {problemas} diferencia(s) no esperada(s)')
        return problemas


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    total = sum(comparar(Path(p)) for p in sys.argv[1:])
    sys.exit(1 if total else 0)
