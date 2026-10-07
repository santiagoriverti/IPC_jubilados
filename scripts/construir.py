"""Corre el analisis completo y exporta:

- data/processed/*.csv   (series y tablas, versionadas)
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

from src import exportar, pipeline  # noqa: E402

PROC = RAIZ / 'data' / 'processed'
OUT = RAIZ / 'output'


def main():
    matplotlib.use('Agg')
    ap = argparse.ArgumentParser()
    ap.add_argument('--refrescar', action='store_true')
    ap.add_argument('--bootstrap', type=int, default=500)
    a = ap.parse_args()
    R = pipeline.calcular(refrescar=a.refrescar, n_bootstrap=a.bootstrap)
    exportar.exportar(R, OUT, PROC)
    print('Listo:', OUT / 'IIJP_resultados.xlsx')


if __name__ == '__main__':
    main()
