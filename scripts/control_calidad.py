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

from src import estructura as estr  # noqa: E402
from src import fuentes, pipeline  # noqa: E402


def main() -> int:
    R = pipeline.calcular(n_bootstrap=0, verbose=False)
    alertas = 0

    def chequear(ok: bool, texto: str):
        nonlocal alertas
        alertas += not ok
        print(('OK      ' if ok else 'ALERTA  ') + texto)

    # ---------------------------------------------------------------- estructura de precios
    val = R['validacion']
    err = val['error_pct'].abs().max()
    chequear(err < 0.2, f'Con las ponderaciones oficiales, la estructura de aperturas replica el IPC nacional: '
                        f'error maximo {err:.3f}% (< 0,2%)')
    err_r = val[[c for c in val.columns if c.startswith('error_pct_')]].abs().max()
    chequear(bool((err_r < 0.5).all()), f'... y el nivel general de cada region: error maximo {err_r.max():.3f}% '
                                        f'({err_r.idxmax()[10:]}) (< 0,5%)')

    # Agregados que sus hijos publicados cubren por completo: la agregacion de Laspeyres los reproduce
    ap = fuentes.leer_ipc_aperturas()
    ap = ap[ap['periodo'] <= pd.Period(R['meta']['ultimo_ipc'], 'M')]
    W = fuentes.leer_ponderadores_ipc()
    peor = 0.0
    for r in fuentes.REGIONES:
        P, _ = estr.completar_huecos(ap[ap['region'] == r].pivot(index='periodo', columns='codigo', values='indice'))
        pub = set(P.columns) - {'0'}
        for p in sorted(pub - {c for c in pub if not any(o.startswith(c + '.') for o in pub)}):
            hijos = estr.hijos_publicados(p, pub)
            w = [float(W.loc[estr.ALIAS_PONDERADOR.get(c, c), r]) for c in hijos]
            if abs(float(W.loc[p, r]) - sum(w)) > 1e-4:
                continue
            rec = sum(wi * P[c] for wi, c in zip(w, hijos)) / sum(w)
            peor = max(peor, float(((rec / P[p] - 1) * 100).abs().max()))
    chequear(peor < 0.1, f'Agregados completos reproducidos con las ponderaciones oficiales: error maximo '
                         f'{peor:.3f}% (< 0,1%)')

    s = R['sensibilidad_restos']
    chequear(bool((s['dispersion_p5_p95_%'] < 10).all()),
             f'Restos derivados estables ante el redondeo de las ponderaciones: dispersion maxima '
             f'{s["dispersion_p5_p95_%"].max():.1f}% (< 10%)')
    chequear(abs(R['meta']['cobertura_gasto'] - 1) < 1e-6,
             f'Todo el gasto de la ENGHo queda asignado a un nodo: {R["meta"]["cobertura_gasto"] * 100:.4f}%')
    imp = R['imputaciones']
    if len(imp):
        g = imp.groupby(['codigo', 'meses'])['region'].apply(lambda s: 'todas' if len(s) == 6 else ', '.join(s))
        print('        Aperturas sin publicar completadas con su agregado: ' +
              '; '.join(f'{c} [{m}] regiones: {r}' for (c, m), r in g.items()))

    # ---------------------------------------------------------------- canastas
    N = R['ponderaciones_nodos']
    sumas = N[[c for c in N.columns if c not in ('descripcion', 'division', 'tipo')]].sum()
    chequear(bool(((sumas - 1).abs() < 1e-6).all()), 'Todas las canastas por nodo suman 1')
    W_div = R['ponderaciones'].drop(columns='division').sum()
    chequear(bool(((W_div - 1).abs() < 1e-6).all()), 'Todas las canastas por division suman 1')
    pob = R['poblaciones'].set_index('poblacion')
    sh = pob.loc['jub_minimo', 'hogares_expandidos'] / pob.loc['jubilados', 'hogares_expandidos']
    chequear(0.2 < sh < 0.6, f'Hogares de haber minimo: {sh * 100:.1f}% de los hogares jubilados (entre 20% y 60%)')
    cob = R['cobertura_precios']
    aprox = float(cob.loc['resto = indice del agregado', 'jubilados']) if 'resto = indice del agregado' in cob.index else 0.0
    chequear(aprox < 0.02, f'Canasta de jubilados valorizada con el indice del agregado (aproximacion): '
                           f'{aprox * 100:.2f}% (< 2%)')

    tp = R['revision_tp']
    dif = (tp['ponderaciones']['tp'] - tp['ponderaciones']['tp_original']).abs().max()
    chequear(dif < 0.0015, f'Revision del TP: la ENGHo reproduce la canasta del TP, diferencia maxima {dif:.4f} (< 0,0015)')
    chequear(abs(tp['peso_tp_1_mayor'] - 0.69) < 0.005,
             f'Revision del TP: peso de hogares con un solo mayor = {tp["peso_tp_1_mayor"]:.4f} (TP usa 0,69)')

    # ---------------------------------------------------------------- haberes y fiscal
    regla = R['regla_movilidad']
    chequear(bool(regla['ok'].all()), f'El haber minimo sigue la regla IPC(t-2) en {regla["ok"].sum()}/{len(regla)} meses')
    h = R['haberes'].dropna(subset=['haber_cf_ipc'])
    d = ((h['haber_cf_ipc'] / h['haber_minimo'] - 1).abs().max()) * 100
    chequear(d < 0.01, f'El contrafactual por IPC reproduce el haber efectivo: desvio maximo {d:.4f}% (< 0,01%)')
    chequear(bool(h['bono'].notna().all()), f'Bono cargado para todos los meses del haber (ultimo {h.index.max()})')

    m = R['fiscal_mensual']
    fin = min(R['haberes']['factor_iijp'].dropna().index.max(), pd.Period(R['meta']['ultimo_imig'], 'M'))
    esperado = pd.period_range('2024-04', fin, freq='M')
    faltan = [str(p) for p in esperado if p not in m.index]
    chequear(not faltan, 'IMIG sin huecos en la ventana fiscal' + (f' (faltan {faltan})' if faltan else ''))

    # ---------------------------------------------------------------- resumen
    meta = R['meta']
    print(f'\nUltimo IPC {meta["ultimo_ipc"]} | ultimo haber {meta["ultimo_haber"]} | ultima IMIG {meta["ultimo_imig"]}')
    ult = R['var_mensual'].iloc[-1]
    print('Ultimo mes (%): ' + ' | '.join(f'{k} {v:.2f}' for k, v in ult.items()))
    res = R['variantes_resumen']
    firmes = res.index[res['mismo_signo_en_todas']].tolist()
    print(f'Resultados con el mismo signo en las {len(R["variantes"])} variantes: {", ".join(firmes)}')
    print(f'\n{alertas} ALERTA(S)')
    return 1 if alertas else 0


if __name__ == '__main__':
    sys.exit(main())
