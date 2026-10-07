"""Corre todo el analisis y devuelve los resultados en un diccionario de DataFrames.

Lo usan scripts/construir.py (exporta CSV, Excel y graficos) y los notebooks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import fiscal, fuentes, haberes, indices, ponderaciones as pond

NOMBRES = {
    'IPC oficial': 'IPC nacional INDEC (canasta ENGHo 2004/05)',
    'IPC ENGHo 17/18': 'IPC recalculado con la canasta de todos los hogares de la ENGHo 2017/18',
    'IIJP': 'IIJP: canasta de hogares jubilados (ENGHo 2017/18), canasta fija',
    'IIJP canasta TP': 'Canasta del TP original, calculada como canasta fija',
    'IIJP solo 65+': 'Canasta de hogares solo de mayores de 65',
    'IIJP jub. bajos': 'Hogares jubilados de menores ingresos',
    'IIJP jub. altos': 'Hogares jubilados de mayores ingresos',
    'IIJP regional': 'IIJP con canastas e indices de precios de las 6 regiones',
    'IIJP método TP': 'Canasta del TP con el metodo del TP (ponderaciones fijas sobre variaciones)',
}


def redondear_pct(v: pd.Series) -> pd.Series:
    """Variacion mensual redondeada a 1 decimal en % (como la publica el INDEC y la usa ANSES)."""
    return (v * 100).round(1) / 100


def calcular(refrescar: bool = False, n_bootstrap: int = 500, verbose: bool = True) -> dict:
    log = print if verbose else (lambda *a, **k: None)
    R: dict = {}

    # ---------------------------------------------------------------- precios
    ipc = fuentes.leer_ipc_divisiones(refrescar)
    I = indices_nac = fuentes.matriz_indices(ipc, 'Nacional')
    V = fuentes.matriz_var_publicada(ipc, 'Nacional')
    I_reg = {r: fuentes.matriz_indices(ipc, r) for r in fuentes.REGIONES_ENGHO.values()}
    ultimo = I.index.max()
    log(f'IPC por division: {I.index.min()} a {ultimo}')

    # ---------------------------------------------------------------- canastas
    hog = fuentes.leer_engho('hogares', refrescar)
    per = fuentes.leer_engho('personas', refrescar, usecols=['id', 'miembro', 'ijubilacion', 'ipensionesnc'])
    h = pond.preparar_hogares(hog, per)
    W = pond.tabla_ponderaciones(h)
    R['ponderaciones'] = W
    R['ponderaciones_democraticas'] = pond.tabla_ponderaciones(h, 'democratica')
    R['poblaciones'] = pond.resumen_poblaciones(h)
    R['peso_tp_1_mayor'] = pond.peso_tp(h)
    log(f'ENGHo: {len(h)} hogares; hogares jubilados = {int(h["jubilados"].sum())}')

    # ---------------------------------------------------------------- indices
    niv = {
        'IPC oficial': I['0'],
        'IPC ENGHo 17/18': indices.lowe(I, W['total']),
        'IIJP': indices.lowe(I, W['jubilados']),
        'IIJP canasta TP': indices.lowe(I, W['tp']),
        'IIJP solo 65+': indices.lowe(I, W['solo_65']),
        'IIJP jub. bajos': indices.lowe(I, W['jub_bajos']),
        'IIJP jub. altos': indices.lowe(I, W['jub_altos']),
        'IIJP regional': indices.lowe_regional(I_reg, pond.canastas_regionales(h, 'jubilados')),
        'IIJP método TP': indices.nivel_desde_variaciones(indices.metodo_tp(V, pond.POND_TP_ORIGINAL)),
    }
    niveles = pd.DataFrame(niv)
    niveles.index.name = 'periodo'
    R['niveles'] = niveles
    R['var_mensual'] = niveles.pct_change() * 100
    R['var_interanual'] = (niveles / niveles.shift(12) - 1) * 100

    # Validacion: replicar el IPC oficial con sus ponderaciones
    replica = indices.laspeyres(I, pond.pond_ipc_oficial())
    err = (replica / I['0'] - 1) * 100
    R['validacion'] = pd.DataFrame({'ipc_oficial': I['0'], 'replica_laspeyres': replica, 'error_pct': err})
    log(f'Replica del IPC oficial: error maximo {err.abs().max():.3f}%')

    # Serie del TP original (para documentar diferencias)
    tp = pd.read_csv(fuentes.REFERENCIA / 'tp_original_series.csv', comment='#')
    tp.index = pd.PeriodIndex(tp['periodo'], freq='M')
    R['tp_original'] = tp

    # ---------------------------------------------------------------- brechas
    sel = ['IPC oficial', 'IPC ENGHo 17/18', 'IIJP', 'IIJP canasta TP', 'IIJP solo 65+', 'IIJP jub. bajos',
           'IIJP jub. altos', 'IIJP regional', 'IIJP método TP']
    R['periodos'] = indices.tabla_periodos({k: niv[k] for k in sel})
    filas = []
    for nombre, d, hh in indices.PERIODOS:
        for a, b, etiqueta in [('IIJP', 'IPC oficial', 'IIJP vs IPC oficial'),
                               ('IIJP', 'IPC ENGHo 17/18', 'IIJP vs IPC 17/18 (efecto edad)'),
                               ('IPC ENGHo 17/18', 'IPC oficial', 'IPC 17/18 vs oficial (efecto canasta nueva)')]:
            r = indices.brecha_mensual(niv[a], niv[b], pd.Period(d, 'M') + 1, hh)
            filas.append({'periodo': nombre, 'comparacion': etiqueta, **r})
    R['brecha_estadistica'] = pd.DataFrame(filas)

    # Descomposicion por division
    dec = {}
    for etiqueta, d in [('nov23_ultimo', '2023-11'), ('dic16_ultimo', '2016-12')]:
        x = indices.descomposicion(I, W['jubilados'], pond.pond_ipc_oficial(), d, ultimo)
        y = indices.descomposicion(I, W['jubilados'], W['total'], d, ultimo, ref_b=indices.REF_ENGHO)
        z = indices.descomposicion(I, W['total'], pond.pond_ipc_oficial(), d, ultimo)
        t = pd.DataFrame({'division': [pond.DIVISIONES_CORTO[c] for c in x.index],
                          'var_division_pct': x['var_division'] * 100,
                          'pond_ef_iijp': x['pond_efectiva_a'], 'pond_ef_ipc_oficial': x['pond_efectiva_b'],
                          'pond_ef_ipc_1718': y['pond_efectiva_b'],
                          'aporte_vs_ipc_oficial': x['aporte_pct'], 'aporte_efecto_edad': y['aporte_pct'],
                          'aporte_efecto_canasta_nueva': z['aporte_pct']})
        t.attrs = {'brecha_vs_oficial': x.attrs['brecha_pct'], 'brecha_edad': y.attrs['brecha_pct'],
                   'brecha_canasta': z.attrs['brecha_pct'], 'desde': d, 'hasta': str(ultimo)}
        dec[etiqueta] = t
    R['descomposicion'] = dec

    # Ponderaciones efectivas (cuanto pesa cada rubro en el valor de la canasta, mes a mes)
    R['pond_efectiva_iijp'] = pd.DataFrame(
        {t: indices.ponderacion_efectiva(I, W['jubilados'], t) for t in I.index}).T

    # ---------------------------------------------------------------- incertidumbre muestral
    if n_bootstrap:
        log(f'Bootstrap de canastas ({n_bootstrap} replicas)...')
        bs = pond.bootstrap_canastas(h, ['jubilados', 'total'], n=n_bootstrap)
        R['bootstrap_ponderaciones'] = pd.DataFrame(
            {f'{p}_{q}': np.percentile(bs[p], q, axis=0) for p in bs for q in (2.5, 97.5)}, index=pond.DIVS)
        filas = []
        for nombre, d, hh in indices.PERIODOS:
            hh = hh or str(ultimo)
            ofi = indices.acumulada(I['0'], d, hh)
            vs_ofi, edad = [], []
            for b in range(n_bootstrap):
                j = indices.acumulada(indices.lowe(I, bs['jubilados'][b]), d, hh)
                t = indices.acumulada(indices.lowe(I, bs['total'][b]), d, hh)
                vs_ofi.append(((1 + j) / (1 + ofi) - 1) * 100)
                edad.append(((1 + j) / (1 + t) - 1) * 100)
            filas.append({'periodo': nombre, 'desde': d, 'hasta': hh,
                          'brecha_vs_oficial_p2.5': np.percentile(vs_ofi, 2.5),
                          'brecha_vs_oficial_p97.5': np.percentile(vs_ofi, 97.5),
                          'efecto_edad_p2.5': np.percentile(edad, 2.5), 'efecto_edad_p97.5': np.percentile(edad, 97.5)})
        R['bootstrap_brechas'] = pd.DataFrame(filas)

        # Banda para la brecha acumulada mes a mes desde nov-2023
        base = pd.Period('2023-11', 'M')
        tray = []
        for b in range(n_bootstrap):
            j = indices.lowe(I, bs['jubilados'][b]).loc[base:]
            tray.append(((j / j.iloc[0]) / (I['0'].loc[base:] / I['0'].loc[base]) - 1) * 100)
        tray = pd.concat(tray, axis=1)
        R['banda_brecha_nov23'] = pd.DataFrame({'p2.5': tray.quantile(0.025, axis=1),
                                                'p97.5': tray.quantile(0.975, axis=1)})

    # ---------------------------------------------------------------- haberes
    hab = haberes.tabla_haberes(fuentes.leer_haber_minimo(refrescar), fuentes.leer_bono())
    v_ipc_pub = V['0']
    v_iijp = redondear_pct(niv['IIJP'].pct_change())
    R['regla_movilidad'] = haberes.verificar_regla(hab['haber_minimo'], v_ipc_pub)
    fin = min(hab.index.max(), ultimo + 2)  # el haber se conoce hasta 2 meses despues del IPC
    hab = hab.loc[:fin]
    hab['haber_cf_ipc'] = haberes.contrafactual(hab['haber_minimo'], v_ipc_pub)
    hab['haber_cf_iijp'] = haberes.contrafactual(hab['haber_minimo'], v_iijp)
    hab['factor_iijp'] = hab['haber_cf_iijp'] / hab['haber_cf_ipc']
    # Ejercicio del TP: indexacion mensual con rezago de 2 meses desde dic-2023 (cuando todavia regia la
    # formula trimestral de la Ley 27.609). Separa el efecto de la transicion del efecto del indice.
    hab['haber_cf_ipc_dic23'] = haberes.contrafactual(hab['haber_minimo'], v_ipc_pub, desde='2023-12')
    hab['haber_cf_iijp_dic23'] = haberes.contrafactual(hab['haber_minimo'], v_iijp, desde='2023-12')
    hab['bono_indexado_ipc'] = haberes.contrafactual(hab['bono'], v_ipc_pub, desde='2024-03')
    for k, s in [('ipc', niv['IPC oficial']), ('iijp', niv['IIJP']), ('iijp_bajos', niv['IIJP jub. bajos'])]:
        base = pd.Period('2023-11', 'M')
        hab[f'real_haber_{k}'] = haberes.real(hab['haber_minimo'], s, base)
        hab[f'real_con_bono_{k}'] = haberes.real(hab['haber_con_bono'], s, base)
    R['haberes'] = hab

    # ---------------------------------------------------------------- fiscal
    imig = fuentes.imig_mensual()
    pib = fuentes.leer_pib_anual(refrescar)
    mensual = fiscal.costo_mensual(hab['factor_iijp'].dropna(), imig)
    anual = fiscal.costo_anual(mensual, imig, pib)
    R['fiscal_mensual'] = mensual
    R['fiscal_anual'] = anual
    ult_anio = int(anual.dropna(subset=['pib']).query('meses == 12').index.max()) if anual['pib'].notna().any() else None
    gpib = float(anual.loc[ult_anio, 'gasto_prev_pct_pib']) if ult_anio else np.nan
    R['fiscal_desvio_permanente'] = fiscal.desvio_permanente(gpib)
    R['meta'] = {'ultimo_ipc': str(ultimo), 'ultimo_haber': str(hab.index.max()),
                 'ultimo_imig': str(imig.index.max()), 'anio_pib_ref': ult_anio, 'gasto_prev_pct_pib': gpib,
                 'n_bootstrap': n_bootstrap}
    return R
