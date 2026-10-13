"""Corre todo el analisis y devuelve los resultados en un diccionario de DataFrames.

Lo usan scripts/construir.py (exporta CSV, Excel y graficos), scripts/control_calidad.py y los notebooks.

Indice principal (IIJP): canasta fija (Lowe) con la estructura de gasto de los hogares jubilados de la
ENGHo 2017/18, valorizada en cada region al nivel mas desagregado que publica el INDEC (aperturas, con
los restos no publicados deducidos de las ponderaciones oficiales; ver estructura.py). El indice
nacional suma las 6 canastas regionales (cada region pesa segun el gasto de sus hogares jubilados).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import estructura as estr
from . import fiscal, fuentes, haberes, indices, variantes
from . import ponderaciones as pond

NOMBRES = {
    'IPC oficial': 'IPC nacional INDEC (canasta ENGHo 2004/05)',
    'IPC ENGHo 17/18': 'Mismo calculo que el IIJP con la canasta de todos los hogares de la ENGHo 2017/18',
    'IIJP': 'IIJP: canasta de los hogares jubilados (ENGHo 2017/18), aperturas regionales, canasta fija',
    'IIJP haber mínimo': 'IIJP de los hogares jubilados en los que nadie cobra mas de 1,1 haberes minimos',
}
POBLACIONES_INDICE = {'IIJP': 'jubilados', 'IPC ENGHo 17/18': 'total', 'IIJP haber mínimo': 'jub_minimo'}

var_movilidad = haberes.var_movilidad


def _niveles_bootstrap(P: pd.DataFrame, M: np.ndarray) -> pd.DataFrame:
    """Niveles (base dic-2016 = 100) para cada replica: M = replicas x nodos (gasto expandido)."""
    pref = P.loc[indices.REF_ENGHO[0]:indices.REF_ENGHO[1]].mean().values
    L = P.values @ (M / pref).T
    L = L / L[P.index.get_loc(indices.BASE)] * 100
    return pd.DataFrame(L, index=P.index)


def calcular(refrescar: bool = False, n_bootstrap: int = 500, verbose: bool = True) -> dict:
    log = print if verbose else (lambda *a, **k: None)
    R: dict = {}

    # ---------------------------------------------------------------- precios
    ipc = fuentes.leer_ipc_divisiones(refrescar)
    I = fuentes.matriz_indices(ipc, 'Nacional')
    ap = fuentes.leer_ipc_aperturas(refrescar)
    pondr = fuentes.leer_ponderadores_ipc()
    ultimo = min(I.index.max(), ap['periodo'].max())
    I = I.loc[:ultimo]
    ap = ap[ap['periodo'] <= ultimo]
    ipc = ipc[ipc['periodo'] <= ultimo]
    est = estr.construir(ap, pondr)
    est_ra = estr.construir(ap, pondr, resto='agregado')
    est_dr = estr.construir_divisiones(ipc, pondr, regional=True)
    est_dn = estr.construir_divisiones(ipc, pond_nacional=pond.pond_ipc_oficial())
    P = est.precios
    n_der = int((est.nodos['tipo'] == 'resto derivado').sum())
    log(f'IPC: {I.index.min()} a {ultimo} | estructura: {len(est.nodos)} nodos en 6 regiones '
        f'({n_der} restos derivados)')

    # ---------------------------------------------------------------- microdatos y canastas
    hog = fuentes.leer_engho('hogares', refrescar)
    per = fuentes.leer_engho('personas', refrescar, usecols=['id', 'miembro', 'cp03', 'cp04', 'ijubilacion',
                                                              'ipensionesnc'])
    gas = fuentes.leer_engho('gastos', refrescar, usecols=['id', 'clase', 'grupo', 'division', 'monto'])
    haber_serie = fuentes.leer_haber_minimo(refrescar)
    h = pond.preparar_hogares(hog, per, haber_serie)
    E = pond.gasto_por_nodo(gas, h, est)
    E_dr = pond.gasto_por_nodo(gas, h, est_dr)
    E_dn = pond.gasto_por_nodo(gas, h, est_dn)
    cobertura = float((h['pondera'] * E.sum(axis=1)).sum() / (h['pondera'] * h['gastot']).sum())
    log(f'ENGHo: {len(h)} hogares; jubilados {int(h["jubilados"].sum())}, haber minimo '
        f'{int(h["jub_minimo"].sum())} | gasto asignado a nodos: {cobertura * 100:.3f}% de gastot')

    G = {p: pond.canasta_nodos(E, h, p) for p in POBLACIONES_INDICE.values()}
    principales = list(POBLACIONES_INDICE.values())
    R['poblaciones'] = pond.resumen_poblaciones(h)
    R['ponderaciones'] = pond.tabla_ponderaciones(h, pobls=[p for p in pond.POBLACIONES if p != 'tp'])
    R['ponderaciones_democraticas'] = pond.tabla_ponderaciones(h, 'democratica', pobls=principales + ['jub_bajos'])
    nodos = pond.tabla_nodos(E, h, est, principales)
    R['ponderaciones_nodos'] = nodos
    ag = nodos.reset_index().groupby('nodo').agg(
        descripcion=('descripcion', 'first'), division=('division', 'first'), tipo=('tipo', 'first'),
        **{c: (c, 'sum') for c in ['ipc_oficial'] + principales})
    for c in ['ipc_oficial'] + principales:
        ag[f'{c}_en_division'] = ag[c] / ag.groupby('division')[c].transform('sum')
    R['ponderaciones_aperturas'] = ag
    R['estructura'] = est.nodos
    R['indices_residuales'] = estr.residuos(est)
    R['imputaciones'] = est.imputados
    R['sensibilidad_restos'] = estr.sensibilidad_redondeo(ap, pondr)

    # ---------------------------------------------------------------- indices
    niv = {'IPC oficial': I['0']}
    niv.update({k: indices.lowe(P, G[p]) for k, p in POBLACIONES_INDICE.items()})
    niveles = pd.DataFrame(niv)[['IPC oficial', 'IPC ENGHo 17/18', 'IIJP', 'IIJP haber mínimo']]
    niveles.index.name = 'periodo'
    R['niveles'] = niveles
    R['var_mensual'] = niveles.pct_change() * 100
    R['var_interanual'] = (niveles / niveles.shift(12) - 1) * 100

    ipc_reg = ap[ap['codigo'] == '0'].pivot(index='periodo', columns='region', values='indice')
    reg, filas = {}, []
    for r in fuentes.REGIONES:
        cols = [c for c in P.columns if c[0] == r]
        reg[f'IPC {r}'] = ipc_reg[r]
        reg[f'IIJP {r}'] = indices.lowe(P[cols], G['jubilados'][cols])
        for nombre, d, hh in indices.periodos_vigentes(ultimo):
            filas.append({'region': r, 'periodo': nombre, 'desde': d, 'hasta': hh,
                          'IPC region (%)': indices.acumulada(reg[f'IPC {r}'], d, hh) * 100,
                          'IIJP region (%)': indices.acumulada(reg[f'IIJP {r}'], d, hh) * 100,
                          'brecha (%)': indices.brecha(reg[f'IIJP {r}'], reg[f'IPC {r}'], d, hh)})
    R['niveles_regionales'] = pd.DataFrame(reg)
    R['periodos_regionales'] = pd.DataFrame(filas)
    jr = G['jubilados'].groupby(level='region').sum()
    R['peso_regiones'] = pd.DataFrame({'ipc_oficial': est.pond_oficial().groupby(level='region').sum(),
                                       'jubilados': jr, 'total': G['total'].groupby(level='region').sum(),
                                       'hogares_jubilados_muestra': h[h['jubilados']].groupby('region_ipc').size(),
                                       'hogares_haber_minimo_muestra': h[h['jub_minimo']].groupby('region_ipc').size()
                                       }).loc[fuentes.REGIONES]

    # Validacion: con las ponderaciones oficiales, la misma estructura de nodos reproduce el IPC
    w_of = est.pond_oficial()
    replica = indices.laspeyres(P, w_of)
    val = pd.DataFrame({'ipc_oficial': I['0'], 'replica_aperturas': replica,
                        'error_pct': (replica / I['0'] - 1) * 100})
    for r in fuentes.REGIONES:
        cols = [c for c in P.columns if c[0] == r]
        val[f'error_pct_{r}'] = (indices.laspeyres(P[cols], w_of[cols]) / ipc_reg[r] - 1) * 100
    R['validacion'] = val
    log(f'Replica del IPC oficial con la estructura de aperturas: error maximo {val["error_pct"].abs().max():.3f}%')

    # ---------------------------------------------------------------- brechas
    R['periodos'] = indices.tabla_periodos(niv)
    filas = []
    for nombre, d, hh in indices.periodos_vigentes(ultimo):
        for a, b, etiqueta in [('IIJP', 'IPC oficial', 'IIJP vs IPC oficial'),
                               ('IIJP', 'IPC ENGHo 17/18', 'IIJP vs IPC 17/18 (efecto edad)'),
                               ('IPC ENGHo 17/18', 'IPC oficial', 'IPC 17/18 vs oficial (efecto canasta nueva)'),
                               ('IIJP haber mínimo', 'IIJP', 'IIJP haber mínimo vs IIJP')]:
            r_ = indices.brecha_mensual(niv[a], niv[b], pd.Period(d, 'M') + 1, hh)
            filas.append({'periodo': nombre, 'comparacion': etiqueta, **r_})
    R['brecha_estadistica'] = pd.DataFrame(filas)

    # Descomposicion por nodo, sumada por division y por apertura
    dec, dec_nodos = {}, {}
    desc = est.nodos.drop_duplicates('nodo').set_index('nodo')['descripcion']
    for etiqueta, d in [('nov23_ultimo', '2023-11'), ('dic16_ultimo', '2016-12')]:
        x = indices.descomposicion(P, G['jubilados'], w_of, d, ultimo)
        y = indices.descomposicion(P, G['jubilados'], G['total'], d, ultimo, ref_b=indices.REF_ENGHO)
        z = indices.descomposicion(P, G['total'], w_of, d, ultimo)

        def div(s):
            return pond.por_division(s, est)

        t = pd.DataFrame({'division': [pond.DIVISIONES_CORTO[c] for c in pond.DIVS],
                          'var_division_pct': (I.loc[ultimo, pond.DIVS] / I.loc[pd.Period(d, 'M'), pond.DIVS] - 1) * 100,
                          'pond_ef_iijp': div(x['pond_efectiva_a']), 'pond_ef_ipc_oficial': div(x['pond_efectiva_b']),
                          'pond_ef_ipc_1718': div(y['pond_efectiva_b']),
                          'aporte_vs_ipc_oficial': div(x['aporte_pct']), 'aporte_efecto_edad': div(y['aporte_pct']),
                          'aporte_efecto_canasta_nueva': div(z['aporte_pct'])}, index=pond.DIVS)
        t.index.name = 'codigo'
        t.attrs = {'brecha_vs_oficial': x.attrs['brecha_pct'], 'brecha_edad': y.attrs['brecha_pct'],
                   'brecha_canasta': z.attrs['brecha_pct'], 'desde': d, 'hasta': str(ultimo)}
        dec[etiqueta] = t
        n = pd.DataFrame({'pond_ef_iijp': x['pond_efectiva_a'], 'pond_ef_ipc_oficial': x['pond_efectiva_b'],
                          'pond_ef_ipc_1718': y['pond_efectiva_b'], 'aporte_vs_ipc_oficial': x['aporte_pct'],
                          'aporte_efecto_edad': y['aporte_pct'], 'aporte_efecto_canasta_nueva': z['aporte_pct']})
        n = n.groupby(level='nodo').sum()
        n.insert(0, 'descripcion', desc.reindex(n.index).values)
        dec_nodos[etiqueta] = n.sort_values('aporte_vs_ipc_oficial', ascending=False)
    R['descomposicion'] = dec
    R['descomposicion_aperturas'] = dec_nodos

    # Ponderaciones efectivas por division (peso de cada division en el valor de la canasta, mes a mes)
    pref = P.loc[indices.REF_ENGHO[0]:indices.REF_ENGHO[1]].mean()
    V = P * (G['jubilados'] / pref)
    V = V.div(V.sum(axis=1), axis=0)
    div_col = est.nodos.set_index(['region', 'nodo'])['division'].reindex(V.columns).values
    R['pond_efectiva_iijp'] = V.T.groupby(div_col).sum().T

    # ---------------------------------------------------------------- incertidumbre muestral
    if n_bootstrap:
        log(f'Bootstrap de canastas ({n_bootstrap} replicas)...')
        bs = pond.bootstrap_gasto(E, h, principales, n=n_bootstrap)
        cols_div = est.nodos['division'].values
        b_pond = {}
        for p in principales:
            Dv = pd.DataFrame(bs[p], columns=cols_div).T.groupby(level=0).sum().T
            Dv = Dv.div(Dv.sum(axis=1), axis=0)
            for q in (2.5, 97.5):
                b_pond[f'{p}_{q}'] = np.percentile(Dv.values, q, axis=0)
        R['bootstrap_ponderaciones'] = pd.DataFrame(b_pond, index=pond.DIVS)
        L = {p: _niveles_bootstrap(P, bs[p]) for p in principales}
        filas = []
        for nombre, d, hh in indices.periodos_vigentes(ultimo):
            dd, hp = pd.Period(d, 'M'), pd.Period(hh, 'M')
            ofi = 1 + indices.acumulada(I['0'], d, hh)
            acu = {p: L[p].loc[hp] / L[p].loc[dd] for p in principales}
            vs_ofi = (acu['jubilados'] / ofi - 1) * 100
            edad = (acu['jubilados'] / acu['total'] - 1) * 100
            vs_ofi_min = (acu['jub_minimo'] / ofi - 1) * 100
            filas.append({'periodo': nombre, 'desde': d, 'hasta': hh,
                          'brecha_vs_oficial_p2.5': np.percentile(vs_ofi, 2.5),
                          'brecha_vs_oficial_p97.5': np.percentile(vs_ofi, 97.5),
                          'efecto_edad_p2.5': np.percentile(edad, 2.5), 'efecto_edad_p97.5': np.percentile(edad, 97.5),
                          'haber_minimo_vs_oficial_p2.5': np.percentile(vs_ofi_min, 2.5),
                          'haber_minimo_vs_oficial_p97.5': np.percentile(vs_ofi_min, 97.5)})
        R['bootstrap_brechas'] = pd.DataFrame(filas)
        base = pd.Period('2023-11', 'M')
        tray = (L['jubilados'].loc[base:] / L['jubilados'].loc[base]).div(I['0'].loc[base:] / I['0'].loc[base],
                                                                          axis=0) * 100 - 100
        R['banda_brecha_nov23'] = pd.DataFrame({'p2.5': tray.quantile(0.025, axis=1),
                                                'p97.5': tray.quantile(0.975, axis=1)})

    # ---------------------------------------------------------------- haberes
    hab = haberes.tabla_haberes(haber_serie, fuentes.leer_bono())
    v_ipc = var_movilidad(I['0'])
    v_iijp = var_movilidad(niv['IIJP'])
    v_min = var_movilidad(niv['IIJP haber mínimo'])
    R['regla_movilidad'] = haberes.verificar_regla(hab['haber_minimo'], v_ipc)
    fin = min(hab.index.max(), ultimo + 2)  # el haber se conoce hasta 2 meses despues del IPC
    hab = hab.loc[:fin]
    hab['haber_cf_ipc'] = haberes.contrafactual(hab['haber_minimo'], v_ipc)
    hab['haber_cf_iijp'] = haberes.contrafactual(hab['haber_minimo'], v_iijp)
    hab['haber_cf_iijp_minimo'] = haberes.contrafactual(hab['haber_minimo'], v_min)
    hab['factor_iijp'] = hab['haber_cf_iijp'] / hab['haber_cf_ipc']
    hab['factor_iijp_minimo'] = hab['haber_cf_iijp_minimo'] / hab['haber_cf_ipc']
    # Ejercicio del TP: indexacion mensual con rezago de 2 meses desde dic-2023 (cuando todavia regia la
    # formula trimestral de la Ley 27.609). Separa el efecto de la transicion del efecto del indice.
    hab['haber_cf_ipc_dic23'] = haberes.contrafactual(hab['haber_minimo'], v_ipc, desde='2023-12')
    hab['haber_cf_iijp_dic23'] = haberes.contrafactual(hab['haber_minimo'], v_iijp, desde='2023-12')
    hab['bono_indexado_ipc'] = haberes.contrafactual(hab['bono'], v_ipc, desde='2024-03')
    base = pd.Period('2023-11', 'M')
    for k, s in [('ipc', niv['IPC oficial']), ('iijp', niv['IIJP']), ('iijp_minimo', niv['IIJP haber mínimo'])]:
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

    # ---------------------------------------------------------------- variantes (sensibilidad)
    log('Tabla de variantes...')
    ctx = variantes.Contexto(h=h, ipc=I['0'], haber=haber_serie, ultimo=ultimo, estructuras={
        'aperturas': (est, E), 'aperturas_resto_agregado': (est_ra, E), 'div_regional': (est_dr, E_dr),
        'div_nacional': (est_dn, E_dn)})
    R['variantes'], R['variantes_niveles'] = variantes.tabla_variantes(ctx)
    R['variantes_resumen'] = variantes.resumen(R['variantes'])

    # ---------------------------------------------------------------- revision del TP original
    V = fuentes.matriz_var_publicada(ipc, 'Nacional').loc[:ultimo]
    w_tp = pond.canasta(h, 'tp')
    tp_niv = {'IPC oficial': I['0'], 'IIJP canasta TP': indices.lowe(I, w_tp),
              'IIJP método TP': indices.nivel_desde_variaciones(indices.metodo_tp(V, pond.POND_TP_ORIGINAL))}
    tp_ser = pd.read_csv(fuentes.REFERENCIA / 'tp_original_series.csv', comment='#')
    tp_ser.index = pd.PeriodIndex(tp_ser['periodo'], freq='M')
    R['revision_tp'] = {
        'ponderaciones': pd.DataFrame({'division': [pond.DIVISIONES[d] for d in pond.DIVS],
                                       'tp_original': pond.POND_TP_ORIGINAL, 'tp': w_tp}),
        'niveles': pd.DataFrame(tp_niv), 'periodos': indices.tabla_periodos(tp_niv), 'serie_original': tp_ser,
        'peso_tp_1_mayor': pond.peso_tp(h)}

    R['meta'] = {'ultimo_ipc': str(ultimo), 'ultimo_haber': str(hab.index.max()),
                 'ultimo_imig': str(imig.index.max()), 'anio_pib_ref': ult_anio, 'gasto_prev_pct_pib': gpib,
                 'n_bootstrap': n_bootstrap, 'nodos': len(est.nodos), 'restos_derivados': n_der,
                 'cobertura_gasto': cobertura, 'umbral_resto': estr.UMBRAL_RESTO}
    return R
