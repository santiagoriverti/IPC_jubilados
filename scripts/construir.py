"""Corre el analisis completo y exporta:

- data/processed/*.csv   (series y tablas, versionadas: los notebooks pueden leerlas sin recalcular)
- output/IIJP_resultados.xlsx
- output/graficos/*.png

Uso:  python scripts/construir.py [--refrescar] [--bootstrap N]
  --refrescar   vuelve a descargar IPC, ENGHo, haber minimo y PIB (si no, usa data/cache/)
  --bootstrap   replicas para la incertidumbre muestral de la ENGHo (default 500; 0 = no)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import matplotlib  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src import graficos, pipeline  # noqa: E402

PROC = RAIZ / 'data' / 'processed'
OUT = RAIZ / 'output'


def _csv(df: pd.DataFrame, nombre: str, index=True):
    df = df.copy()
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.astype(str)
    df.to_csv(PROC / nombre, index=index, float_format='%.6f', lineterminator='\n')


def exportar(R: dict) -> None:
    PROC.mkdir(parents=True, exist_ok=True)
    (OUT / 'graficos').mkdir(parents=True, exist_ok=True)

    _csv(R['ponderaciones'], 'ponderaciones.csv')
    _csv(R['ponderaciones_democraticas'], 'ponderaciones_democraticas.csv')
    _csv(R['poblaciones'], 'poblaciones.csv', index=False)
    _csv(R['niveles'], 'indices_niveles.csv')
    _csv(R['var_mensual'], 'indices_var_mensual.csv')
    _csv(R['periodos'], 'brecha_periodos.csv', index=False)
    _csv(R['brecha_estadistica'], 'brecha_estadistica.csv', index=False)
    for k, t in R['descomposicion'].items():
        _csv(t, f'descomposicion_{k}.csv')
    _csv(R['haberes'], 'haberes.csv')
    _csv(R['fiscal_mensual'], 'fiscal_mensual.csv')
    _csv(R['fiscal_anual'], 'fiscal_anual.csv')
    if 'bootstrap_brechas' in R:
        _csv(R['bootstrap_brechas'], 'bootstrap_brechas.csv', index=False)
        _csv(R['bootstrap_ponderaciones'], 'bootstrap_ponderaciones.csv')

    hojas = {
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
        hojas['Bootstrap_brechas'] = R['bootstrap_brechas']
        hojas['Bootstrap_pond'] = R['bootstrap_ponderaciones']
    with pd.ExcelWriter(OUT / 'IIJP_resultados.xlsx', engine='openpyxl') as xw:
        notas = pd.DataFrame({'nota': [
            'IIJP: Indice de Inflacion de Jubilados y Pensionados (canasta fija ENGHo 2017/18, hogares jubilados).',
            f'Ultimo IPC: {R["meta"]["ultimo_ipc"]} | ultimo haber: {R["meta"]["ultimo_haber"]} | ultima IMIG: {R["meta"]["ultimo_imig"]}',
            'Niveles base dic-2016 = 100. Variaciones en %. Brechas: (1 + infl. A) / (1 + infl. B) - 1, en %.',
            'Montos fiscales en millones de pesos corrientes. Ver README y docs/ para la metodologia.',
        ]})
        notas.to_excel(xw, sheet_name='Notas', index=False)
        for nombre, df in hojas.items():
            df = df.copy()
            if isinstance(df.index, pd.PeriodIndex):
                df.index = df.index.astype(str)
            df.to_excel(xw, sheet_name=nombre[:31])

    for nombre, f in graficos.GRAFICOS.items():
        fig = f(R)
        fig.savefig(OUT / 'graficos' / f'{nombre}.png')
        plt.close(fig)


def main():
    matplotlib.use('Agg')
    ap = argparse.ArgumentParser()
    ap.add_argument('--refrescar', action='store_true')
    ap.add_argument('--bootstrap', type=int, default=500)
    a = ap.parse_args()
    R = pipeline.calcular(refrescar=a.refrescar, n_bootstrap=a.bootstrap)
    exportar(R)
    print('Listo:', OUT / 'IIJP_resultados.xlsx')


if __name__ == '__main__':
    main()
