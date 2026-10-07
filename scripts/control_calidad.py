"""Controles de calidad antes de publicar o commitear resultados nuevos.

Uso:  python scripts/control_calidad.py
Imprime OK / ALERTA por control y termina con codigo 1 si hay alertas.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import pandas as pd  # noqa: E402

from src import pipeline, ponderaciones as pond  # noqa: E402


def main() -> int:
    R = pipeline.calcular(n_bootstrap=0, verbose=False)
    alertas = 0

    def chequear(ok: bool, texto: str):
        nonlocal alertas
        alertas += not ok
        print(('OK      ' if ok else 'ALERTA  ') + texto)

    err = R['validacion']['error_pct'].abs().max()
    chequear(err < 0.2, f'Replica del IPC oficial con sus ponderaciones: error maximo {err:.3f}% (< 0,2%)')

    W = R['ponderaciones']
    dif = (W['tp'] - W['tp_original']).abs().max()
    chequear(dif < 0.0015, f'La ENGHo reproduce la canasta del TP: diferencia maxima {dif:.4f} (< 0,0015)')
    sumas = W.drop(columns='division').sum()
    chequear(bool(((sumas - 1).abs() < 1e-6).all()), 'Todas las canastas suman 1')
    chequear(abs(R['peso_tp_1_mayor'] - 0.69) < 0.005,
             f'Peso de hogares con un solo mayor = {R["peso_tp_1_mayor"]:.4f} (TP usa 0,69)')

    regla = R['regla_movilidad']
    chequear(bool(regla['ok'].all()), f'El haber minimo sigue la regla IPC(t-2) en {regla["ok"].sum()}/{len(regla)} meses')
    h = R['haberes'].dropna(subset=['haber_cf_ipc'])
    d = ((h['haber_cf_ipc'] / h['haber_minimo'] - 1).abs().max()) * 100
    chequear(d < 0.01, f'El contrafactual por IPC reproduce el haber efectivo: desvio maximo {d:.4f}% (< 0,01%)')

    bono = h['bono']
    chequear(bool(bono.notna().all()), f'Bono cargado para todos los meses del haber (ultimo {h.index.max()})')

    m = R['fiscal_mensual']
    fin = min(R['haberes']['factor_iijp'].dropna().index.max(), pd.Period(R['meta']['ultimo_imig'], 'M'))
    esperado = pd.period_range('2024-04', fin, freq='M')
    faltan = [str(p) for p in esperado if p not in m.index]
    chequear(not faltan, 'IMIG sin huecos en la ventana fiscal' + (f' (faltan {faltan})' if faltan else ''))

    meta = R['meta']
    print(f'\nUltimo IPC {meta["ultimo_ipc"]} | ultimo haber {meta["ultimo_haber"]} | ultima IMIG {meta["ultimo_imig"]}')
    ult = R['var_mensual'].iloc[-1]
    print(f'Ultimo mes: IPC oficial {ult["IPC oficial"]:.2f}% | IIJP {ult["IIJP"]:.2f}% | '
          f'IPC ENGHo 17/18 {ult["IPC ENGHo 17/18"]:.2f}%')
    print(f'\n{alertas} ALERTA(S)')
    return 1 if alertas else 0


if __name__ == '__main__':
    sys.exit(main())
