"""Exportacion de resultados: CSV (datos), Excel y graficos PNG.

- `exportar(R, dir_salida, dir_datos)`: escribe IIJP_resultados.xlsx y graficos/ en dir_salida y los
  CSV en dir_datos. scripts/construir.py lo usa con output/ y data/processed/ (versionados).
- `zip_resultados(R, nombre)`: lo que llaman los notebooks al final. Exporta todo a
  _descargas/<nombre>/ (ignorado por git, no toca los archivos versionados) y lo comprime en
  _descargas/<nombre>.zip.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import fuentes, graficos

DESCARGAS = fuentes.RAIZ / '_descargas'


def _sin_period(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.astype(str)
    return df


def tablas_csv(R: dict) -> dict[str, tuple[pd.DataFrame, bool]]:
    """{archivo: (tabla, escribir_indice)}"""
    t = {
        'ponderaciones.csv': (R['ponderaciones'], True),
        'ponderaciones_democraticas.csv': (R['ponderaciones_democraticas'], True),
        'poblaciones.csv': (R['poblaciones'], False),
        'indices_niveles.csv': (R['niveles'], True),
        'indices_var_mensual.csv': (R['var_mensual'], True),
        'brecha_periodos.csv': (R['periodos'], False),
        'brecha_estadistica.csv': (R['brecha_estadistica'], False),
        'haberes.csv': (R['haberes'], True),
        'fiscal_mensual.csv': (R['fiscal_mensual'], True),
        'fiscal_anual.csv': (R['fiscal_anual'], True),
    }
    for k, d in R['descomposicion'].items():
        t[f'descomposicion_{k}.csv'] = (d, True)
    if 'bootstrap_brechas' in R:
        t['bootstrap_brechas.csv'] = (R['bootstrap_brechas'], False)
        t['bootstrap_ponderaciones.csv'] = (R['bootstrap_ponderaciones'], True)
    return t


def hojas_excel(R: dict) -> dict[str, pd.DataFrame]:
    h = {
        'Ponderaciones': R['ponderaciones'],
        'Pond_democraticas': R['ponderaciones_democraticas'],
        'Poblaciones': R['poblaciones'],
        'Indices_niveles': R['niveles'],
        'Var_mensual_%': R['var_mensual'],
        'Var_interanual_%': R['var_interanual'],
        'Brecha_periodos': R['periodos'],
        'Brecha_estadistica': R['brecha_estadistica'],
        'Descomp_nov23': R['descomposicion']['nov23_ultimo'],
        'Descomp_dic16': R['descomposicion']['dic16_ultimo'],
        'Pond_efectiva_IIJP': R['pond_efectiva_iijp'],
        'Haberes': R['haberes'],
        'Regla_movilidad': R['regla_movilidad'],
        'Fiscal_mensual': R['fiscal_mensual'],
        'Fiscal_anual': R['fiscal_anual'],
        'Desvio_permanente': R['fiscal_desvio_permanente'],
        'Validacion_IPC': R['validacion'],
    }
    if 'bootstrap_brechas' in R:
        h['Bootstrap_brechas'] = R['bootstrap_brechas']
        h['Bootstrap_pond'] = R['bootstrap_ponderaciones']
    return h


def version_repo() -> str:
    """Commit del repo con que se genero la salida (para saber si un ZIP es de una version vieja)."""
    try:
        r = subprocess.run(['git', '-C', str(fuentes.RAIZ), 'log', '-1', '--format=%h (%ad)', '--date=short'],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or 'desconocida'
    except (OSError, subprocess.SubprocessError):
        return 'desconocida'


def notas(R: dict) -> list[str]:
    m = R['meta']
    return [
        'IIJP: Indice de Inflacion de Jubilados y Pensionados (canasta fija ENGHo 2017/18, hogares jubilados).',
        f'Version del codigo (commit): {version_repo()}',
        f'Ultimo IPC: {m["ultimo_ipc"]} | ultimo haber: {m["ultimo_haber"]} | ultima IMIG: {m["ultimo_imig"]}'
        f' | replicas bootstrap: {m["n_bootstrap"]}',
        'Niveles base dic-2016 = 100. Variaciones en %. Brechas: (1 + infl. A) / (1 + infl. B) - 1, en %.',
        'Montos fiscales en millones de pesos corrientes. Metodologia: README y docs/ del repo '
        'github.com/santiagoriverti/IPC_jubilados.',
    ]


def exportar(R: dict, dir_salida: Path, dir_datos: Path) -> None:
    dir_salida, dir_datos = Path(dir_salida), Path(dir_datos)
    dir_datos.mkdir(parents=True, exist_ok=True)
    (dir_salida / 'graficos').mkdir(parents=True, exist_ok=True)

    for archivo, (df, con_indice) in tablas_csv(R).items():
        _sin_period(df).to_csv(dir_datos / archivo, index=con_indice, float_format='%.6f', lineterminator='\n')

    with pd.ExcelWriter(dir_salida / 'IIJP_resultados.xlsx', engine='openpyxl') as xw:
        pd.DataFrame({'nota': notas(R)}).to_excel(xw, sheet_name='Notas', index=False)
        for nombre, df in hojas_excel(R).items():
            _sin_period(df).to_excel(xw, sheet_name=nombre[:31])

    for nombre, f in graficos.GRAFICOS.items():
        fig = f(R)
        fig.savefig(dir_salida / 'graficos' / f'{nombre}.png')
        plt.close(fig)


def zip_resultados(R: dict, nombre: str) -> str:
    """Exporta Excel, graficos y CSV a _descargas/<nombre>/ y devuelve la ruta del ZIP."""
    carpeta = DESCARGAS / nombre
    if carpeta.exists():
        shutil.rmtree(carpeta)
    exportar(R, carpeta, carpeta / 'datos')
    (carpeta / 'LEEME.txt').write_text(
        '\n'.join(notas(R) + ['', 'Contenido:', '  IIJP_resultados.xlsx  todas las tablas (una hoja por tabla)',
                              '  graficos/             graficos en PNG', '  datos/                las mismas tablas en CSV']) + '\n',
        encoding='utf-8')
    return shutil.make_archive(str(carpeta), 'zip', carpeta)
