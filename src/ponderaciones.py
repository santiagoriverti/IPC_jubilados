"""Canastas (estructura del gasto de consumo) a partir de los microdatos de la ENGHo 2017/18.

- Poblaciones: marcas por hogar (hogares jubilados, todos los hogares, haber minimo y variantes de la
  definicion para la tabla de sensibilidad).
- Gasto por hogar y nodo de la estructura de precios (archivo de gastos de la ENGHo, asignado con
  estructura.Estructura.asignar): es la base de las ponderaciones del IIJP.
- Ponderaciones por division (archivo de hogares, gc_01..gc_12; su suma es gastot): tablas resumen y
  canasta del TP original.

Ponderaciones "plutocraticas" (gasto agregado del grupo, como el IPC) por defecto; "democraticas"
(promedio de las estructuras de cada hogar) como sensibilidad.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import estructura as estr
from . import fuentes

DIVISIONES = {
    '01': 'Alimentos y bebidas no alcohólicas',
    '02': 'Bebidas alcohólicas y tabaco',
    '03': 'Prendas de vestir y calzado',
    '04': 'Vivienda, agua, electricidad, gas y otros combustibles',
    '05': 'Equipamiento y mantenimiento del hogar',
    '06': 'Salud',
    '07': 'Transporte',
    '08': 'Comunicación',
    '09': 'Recreación y cultura',
    '10': 'Educación',
    '11': 'Restaurantes y hoteles',
    '12': 'Bienes y servicios varios',
}
DIVISIONES_CORTO = {
    '01': 'Alimentos', '02': 'Beb. alc. y tabaco', '03': 'Prendas y calzado', '04': 'Vivienda y servicios',
    '05': 'Equipamiento hogar', '06': 'Salud', '07': 'Transporte', '08': 'Comunicación',
    '09': 'Recreación y cultura', '10': 'Educación', '11': 'Restaurantes y hoteles', '12': 'Bs. y serv. varios',
}
DIVS = list(DIVISIONES)
GC = [f'gc_{d}' for d in DIVS]

# Ponderaciones que el TP original cargo en la hoja "Canasta" (columna D, filas 3-14)
POND_TP_ORIGINAL = pd.Series([0.25145, 0.01862, 0.05252, 0.13735, 0.066, 0.10895, 0.12331, 0.05345,
                              0.07714, 0.01245, 0.05607, 0.04269], index=DIVS, name='tp_original')

UMBRAL_JUBILADOS = 0.5      # jubilaciones y pensiones / ingreso del hogar
TOPE_HABER_MINIMO = 1.1     # haber minimo: ningun perceptor cobra mas de 1,1 haberes minimos

# poblacion: (descripcion, rol). Rol: principal (IIJP), comparador, subindice, variante (tabla de
# sensibilidad) o tp (solo para la revision del TP original)
POBLACIONES = {
    'jubilados': ('Hogares jubilados: jubilaciones y pensiones (contributivas y no contributivas) >= 50% del ingreso',
                  'principal'),
    'total': ('Todos los hogares (IPC con la canasta de la ENGHo 2017/18)', 'comparador'),
    'jub_minimo': ('Hogares jubilados en los que ningún perceptor cobra más de 1,1 haberes mínimos', 'subindice'),
    'jub_sin_pnc': ('Jubilaciones y pensiones contributivas >= 50% del ingreso (sin pensiones no contributivas)',
                    'variante'),
    'jub_umbral_75': ('Jubilaciones y pensiones >= 75% del ingreso', 'variante'),
    'jub_umbral_25': ('Jubilaciones y pensiones >= 25% del ingreso', 'variante'),
    'jefe_conyuge_jub': ('Jefe/a o cónyuge cobra jubilación o pensión contributiva', 'variante'),
    'jefe_65': ('Jefe/a de 65 años o más', 'variante'),
    'adultos_jub': ('Todos los adultos (18+) cobran jubilación o pensión', 'variante'),
    'con_65': ('Hogares con al menos una persona de 65+', 'variante'),
    'solo_65': ('Hogares solo de personas de 65+', 'variante'),
    'jub_bajos': ('Hogares jubilados, mitad de menor ingreso per cápita', 'variante'),
    'jub_altos': ('Hogares jubilados, mitad de mayor ingreso per cápita', 'variante'),
    'tp': ('Canasta del TP original (0,69 x 1 mayor + 0,31 x 2+ mayores)', 'tp'),
}
POBLACION_IIJP = 'jubilados'


def poblaciones(rol: str | None = None) -> list[str]:
    return [p for p, (_, r) in POBLACIONES.items() if rol is None or r == rol]


def pond_ipc_oficial() -> pd.Series:
    """Ponderaciones del IPC nacional del INDEC por division (ENGHo 2004/05), en fraccion."""
    d = pd.read_csv(fuentes.REFERENCIA / 'ponderaciones_ipc_indec.csv', comment='#', dtype={'codigo': str})
    return pd.Series(d['ponderacion'].values / 100, index=d['codigo'].str.zfill(2), name='ipc_oficial')


def preparar_hogares(hogares: pd.DataFrame, personas: pd.DataFrame,
                     haber_minimo: pd.Series | None = None) -> pd.DataFrame:
    """Tabla de hogares (indice = id) con ingresos previsionales y las marcas de cada poblacion.
    personas: id, cp03 (edad), cp04 (parentesco: 1 jefe/a, 2 conyuge), ijubilacion, ipensionesnc."""
    h = hogares.copy()
    h.index = h['id'].values
    per = personas.copy()
    per[['ijubilacion', 'ipensionesnc']] = per[['ijubilacion', 'ipensionesnc']].fillna(0)
    per['prev'] = per['ijubilacion'] + per['ipensionesnc']
    g = per.groupby('id')
    h['ing_jub'] = g['ijubilacion'].sum().reindex(h.index).fillna(0)
    h['ing_pnc'] = g['ipensionesnc'].sum().reindex(h.index).fillna(0)
    h['ing_prev'] = h['ing_jub'] + h['ing_pnc']
    ing = h['ingtoth'].where(h['ingtoth'] > 0)
    h['sh_prev'] = (h['ing_prev'] / ing).fillna(0)
    h['sh_jub'] = (h['ing_jub'] / ing).fillna(0)
    h['region_ipc'] = h['region'].map(fuentes.REGIONES_ENGHO)

    def ids(mask) -> pd.Series:
        return pd.Series(h.index.isin(per.loc[mask, 'id'].unique()), index=h.index)

    adultos = per['cp03'] >= 18
    n_ad = per[adultos].groupby('id').size().reindex(h.index).fillna(0)
    n_ad_prev = per[adultos & (per['prev'] > 0)].groupby('id').size().reindex(h.index).fillna(0)
    edad_jefe = per[per['cp04'] == 1].set_index('id')['cp03'].reindex(h.index)

    h['total'] = True
    h['jubilados'] = (h['ing_prev'] > 0) & (h['sh_prev'] >= UMBRAL_JUBILADOS)
    h['jub_sin_pnc'] = (h['ing_jub'] > 0) & (h['sh_jub'] >= UMBRAL_JUBILADOS)
    h['jub_umbral_75'] = (h['ing_prev'] > 0) & (h['sh_prev'] >= 0.75)
    h['jub_umbral_25'] = (h['ing_prev'] > 0) & (h['sh_prev'] >= 0.25)
    h['jefe_conyuge_jub'] = ids(per['cp04'].isin([1, 2]) & (per['ijubilacion'] > 0))
    h['jefe_65'] = edad_jefe >= 65
    h['adultos_jub'] = (n_ad_prev >= 1) & (n_ad_prev == n_ad)
    h['con_65'] = h['mayor65'] >= 1
    h['solo_65'] = (h['mayor65'] >= 1) & (h['mayor65'] == h['cantmiem'])
    h['tp_1'] = h['mayor65'] == 1
    h['tp_2'] = h['mayor65'] >= 2
    corte = mediana_ponderada(h.loc[h['jubilados'], 'ingpch'], h.loc[h['jubilados'], 'pondera'])
    h['jub_bajos'] = h['jubilados'] & (h['ingpch'] <= corte)
    h['jub_altos'] = h['jubilados'] & (h['ingpch'] > corte)
    if haber_minimo is not None:
        # Haber minimo de referencia: el maximo vigente en el trimestre operativo de la entrevista
        tope = {t: float(haber_minimo.loc[a:b].max()) * TOPE_HABER_MINIMO
                for t, (a, b) in fuentes.TRIMESTRES_ENGHO.items()}
        if not all(np.isfinite(list(tope.values()))):
            raise ValueError('La serie del haber minimo no cubre el relevamiento de la ENGHo (nov-2017 a nov-2018): '
                             f'{haber_minimo.index.min()} a {haber_minimo.index.max()}')
        pp = per[per['prev'] > 0]
        rel = pp['prev'] / pp['id'].map(h['trimestre']).map(tope)
        max_rel = rel.groupby(pp['id']).max().reindex(h.index)
        h['jub_minimo'] = h['jubilados'] & (max_rel <= 1).fillna(False)
    return h


def mediana_ponderada(x: pd.Series, w: pd.Series) -> float:
    o = np.argsort(x.values)
    xs, ws = x.values[o], w.values[o]
    return float(xs[np.searchsorted(np.cumsum(ws), ws.sum() / 2)])


# --------------------------------------------------------------------------------------------
# Gasto por nodo de la estructura de precios (base de las ponderaciones del IIJP)
# --------------------------------------------------------------------------------------------
def gasto_por_nodo(gastos: pd.DataFrame, h: pd.DataFrame, est: estr.Estructura) -> pd.DataFrame:
    """Gasto mensual (sin expandir) de cada hogar en cada nodo de la estructura: hogares x (region, nodo).
    gastos: archivo de gastos de la ENGHo con id, clase, grupo, division y monto."""
    g = gastos[['id', 'clase', 'grupo', 'division', 'monto']].copy()
    regs = est.regiones()
    g['region'] = g['id'].map(h['region_ipc']) if regs != ['Nacional'] else 'Nacional'
    combos = g[['region', 'clase', 'grupo', 'division']].drop_duplicates()
    combos['nodo'] = [est.asignar(r, [estr.codigo_engho(c), estr.codigo_engho(gr), estr.codigo_engho(d)])
                      for r, c, gr, d in combos.itertuples(index=False)]
    g = g.merge(combos, on=['region', 'clase', 'grupo', 'division'], how='left')
    t = g.groupby(['id', 'region', 'nodo'])['monto'].sum().unstack(['region', 'nodo'])
    return t.reindex(index=h.index, columns=est.precios.columns).fillna(0.0)


def canasta_nodos(E: pd.DataFrame, h: pd.DataFrame, poblacion: str, metodo: str = 'plutocratica') -> pd.Series:
    """Participacion de cada nodo en el gasto de la poblacion (suma 1)."""
    m = h[poblacion].values.astype(bool)
    w = h['pondera'].values[m]
    X = E.values[m]
    if metodo == 'plutocratica':
        g = w @ X
    elif metodo == 'democratica':
        X = np.clip(X, 0, None)  # ventas de bienes usados (gasto negativo) fuera del promedio por hogar
        tot = X.sum(axis=1)
        ok = tot > 0
        g = w[ok] @ (X[ok] / tot[ok, None])
    else:
        raise ValueError(metodo)
    s = pd.Series(g, index=E.columns)
    return s / s.sum()


def gasto_por_trimestre(E: pd.DataFrame, h: pd.DataFrame, poblacion: str) -> dict[int, pd.Series]:
    """Gasto expandido de la poblacion por nodo, separado por trimestre operativo de la entrevista."""
    out = {}
    for t in sorted(fuentes.TRIMESTRES_ENGHO):
        m = (h[poblacion] & (h['trimestre'] == t)).values
        out[t] = pd.Series(h['pondera'].values[m] @ E.values[m], index=E.columns)
    return out


def por_division(s: pd.Series, est: estr.Estructura) -> pd.Series:
    """Suma por division de una serie indexada por (region, nodo)."""
    div = est.nodos.set_index(['region', 'nodo'])['division']
    return s.groupby(div.reindex(s.index).values).sum().reindex(DIVS)


def tabla_nodos(E: pd.DataFrame, h: pd.DataFrame, est: estr.Estructura, pobls: list[str]) -> pd.DataFrame:
    """Ponderacion de cada (region, nodo) en la canasta nacional: IPC oficial y cada poblacion."""
    t = est.nodos[['region', 'nodo', 'descripcion', 'division', 'tipo', 'pond_oficial']].copy()
    t = t.rename(columns={'pond_oficial': 'ipc_oficial'}).set_index(['region', 'nodo'])
    for p in pobls:
        t[p] = canasta_nodos(E, h, p)
    return t


# --------------------------------------------------------------------------------------------
# Ponderaciones por division (archivo de hogares): tablas resumen y canasta del TP
# --------------------------------------------------------------------------------------------
def estructura(h: pd.DataFrame, metodo: str = 'plutocratica') -> pd.Series:
    """Estructura del gasto de consumo por division de un conjunto de hogares (suma 1)."""
    if metodo == 'plutocratica':
        t = h[GC].mul(h['pondera'], axis=0).sum()
    elif metodo == 'democratica':
        g = h[GC].clip(lower=0)  # gc_07 puede ser negativo (venta de vehiculos)
        tot = g.sum(axis=1)
        ok = tot > 0
        t = g[ok].div(tot[ok], axis=0).mul(h.loc[ok, 'pondera'], axis=0).sum()
    else:
        raise ValueError(metodo)
    t.index = DIVS
    return t / t.sum()


def peso_tp(h: pd.DataFrame) -> float:
    """Proporcion ponderada de hogares con un solo mayor de 65 entre los hogares con mayores."""
    return h.loc[h['tp_1'], 'pondera'].sum() / h.loc[h['con_65'], 'pondera'].sum()


def canasta(h: pd.DataFrame, poblacion: str, metodo: str = 'plutocratica') -> pd.Series:
    if poblacion == 'tp':
        # Como en el TP: mezcla con los pesos redondeados 0,69 / 0,31 (hoja Canasta, columna D)
        return 0.69 * estructura(h[h['tp_1']], metodo) + 0.31 * estructura(h[h['tp_2']], metodo)
    return estructura(h[h[poblacion]], metodo)


def tabla_ponderaciones(h: pd.DataFrame, metodo: str = 'plutocratica',
                        pobls: list[str] | None = None) -> pd.DataFrame:
    """Divisiones x canastas: IPC oficial y las poblaciones de la ENGHo (por defecto, todas)."""
    t = pd.DataFrame({'ipc_oficial': pond_ipc_oficial()})
    for p in (pobls or [p for p in POBLACIONES if p in h.columns or p == 'tp']):
        t[p] = canasta(h, p, metodo)
    t.index.name = 'codigo'
    t.insert(0, 'division', [DIVISIONES[d] for d in t.index])
    return t


def resumen_poblaciones(h: pd.DataFrame) -> pd.DataFrame:
    """Tamano muestral y expandido de cada poblacion."""
    filas = []
    for p, (desc, rol) in POBLACIONES.items():
        if p != 'tp' and p not in h.columns:
            continue
        m = (h['tp_1'] | h['tp_2']) if p == 'tp' else h[p]
        filas.append({'poblacion': p, 'rol': rol, 'descripcion': desc, 'hogares_muestra': int(m.sum()),
                      'hogares_expandidos': float(h.loc[m, 'pondera'].sum()),
                      'gasto_medio_hogar': float(np.average(h.loc[m, 'gastot'], weights=h.loc[m, 'pondera']))})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------------------------
# Incertidumbre muestral
# --------------------------------------------------------------------------------------------
def bootstrap_gasto(E: pd.DataFrame, h: pd.DataFrame, pobls: list[str], n: int = 500,
                    semilla: int = 2018) -> dict[str, np.ndarray]:
    """Remuestreo de hogares con reposicion, estratificado por region (la ENGHo publica no trae las
    unidades primarias de muestreo, asi que no se pueden remuestrear conglomerados: los intervalos son
    una cota inferior de la incertidumbre muestral). Devuelve {poblacion: matriz n x nodos} con el gasto
    expandido por nodo de cada replica."""
    rng = np.random.default_rng(semilla)
    X, w, reg = E.values, h['pondera'].values.astype(float), h['region'].values
    grupos = [np.flatnonzero(reg == r) for r in sorted(np.unique(reg))]
    mascaras = {p: h[p].values.astype(float) for p in pobls}
    out = {p: np.empty((n, X.shape[1])) for p in pobls}
    for b in range(n):
        idx = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in grupos])
        c = np.bincount(idx, minlength=len(w)) * w
        for p in pobls:
            out[p][b] = (c * mascaras[p]) @ X
    return out
