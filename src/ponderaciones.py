"""Canastas (estructura del gasto de consumo por division COICOP) a partir de la ENGHo 2017/18.

El archivo de hogares de la ENGHo trae el gasto de consumo mensual del hogar por division
(gc_01..gc_12; su suma es gastot). Con eso se arman las ponderaciones de distintas poblaciones:

- total       : todos los hogares (lo que seria un IPC con la ENGHo 2017/18).
- tp          : la canasta del TP original = 0,69 x hogares con 1 persona de 65+ y 0,31 x hogares con
                2 o mas (0,69 es la proporcion ponderada de hogares con un solo mayor; se replica a 3 decimales).
- con_65      : hogares con al menos una persona de 65+ (agregados en un solo grupo).
- solo_65     : hogares donde todos los miembros tienen 65+.
- jubilados   : hogares cuya principal fuente de ingreso (>= 50%) son jubilaciones y pensiones
                (contributivas y no contributivas). Es la poblacion de referencia del IIJP.
- jub_bajos / jub_altos : hogares jubilados por debajo / encima de la mediana de ingreso per capita
                del grupo (aproxima la division haber minimo / resto que usa el analisis fiscal).

Ponderaciones "plutocraticas" (gasto agregado del grupo, como el IPC) por defecto; "democraticas"
(promedio de las estructuras de cada hogar) como sensibilidad.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

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

POBLACIONES = {
    'total': 'Todos los hogares (ENGHo 2017/18)',
    'tp': 'Canasta del TP (0,69 x 1 mayor + 0,31 x 2+ mayores)',
    'con_65': 'Hogares con al menos una persona de 65+',
    'solo_65': 'Hogares solo de personas de 65+',
    'jubilados': 'Hogares jubilados (jubilación/pensión >= 50% del ingreso)',
    'jub_bajos': 'Hogares jubilados, mitad de menor ingreso per cápita',
    'jub_altos': 'Hogares jubilados, mitad de mayor ingreso per cápita',
}
POBLACION_IIJP = 'jubilados'


def pond_ipc_oficial() -> pd.Series:
    """Ponderaciones del IPC nacional del INDEC por division (ENGHo 2004/05), en fraccion."""
    d = pd.read_csv(fuentes.REFERENCIA / 'ponderaciones_ipc_indec.csv', comment='#', dtype={'codigo': str})
    return pd.Series(d['ponderacion'].values / 100, index=d['codigo'].str.zfill(2), name='ipc_oficial')


def preparar_hogares(hogares: pd.DataFrame, personas: pd.DataFrame) -> pd.DataFrame:
    """Agrega a la tabla de hogares el ingreso previsional y las marcas de cada poblacion."""
    h = hogares.copy()
    prev = personas[['id', 'ijubilacion', 'ipensionesnc']].fillna(0)
    prev = prev.assign(ing_prev=prev['ijubilacion'] + prev['ipensionesnc']).groupby('id')['ing_prev'].sum()
    h['ing_prev'] = h['id'].map(prev).fillna(0)
    h['sh_prev'] = np.where(h['ingtoth'] > 0, h['ing_prev'] / h['ingtoth'].where(h['ingtoth'] > 0), 0)
    h['region_ipc'] = h['region'].map(fuentes.REGIONES_ENGHO)

    h['total'] = True
    h['con_65'] = h['mayor65'] >= 1
    h['tp_1'] = h['mayor65'] == 1
    h['tp_2'] = h['mayor65'] >= 2
    h['solo_65'] = (h['mayor65'] >= 1) & (h['mayor65'] == h['cantmiem'])
    h['jubilados'] = (h['ing_prev'] > 0) & (h['sh_prev'] >= 0.5)
    corte = mediana_ponderada(h.loc[h['jubilados'], 'ingpch'], h.loc[h['jubilados'], 'pondera'])
    h['jub_bajos'] = h['jubilados'] & (h['ingpch'] <= corte)
    h['jub_altos'] = h['jubilados'] & (h['ingpch'] > corte)
    return h


def mediana_ponderada(x: pd.Series, w: pd.Series) -> float:
    o = np.argsort(x.values)
    xs, ws = x.values[o], w.values[o]
    return float(xs[np.searchsorted(np.cumsum(ws), ws.sum() / 2)])


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


def tabla_ponderaciones(h: pd.DataFrame, metodo: str = 'plutocratica') -> pd.DataFrame:
    """Divisiones x canastas: IPC oficial, TP original (tal como lo cargo) y las poblaciones ENGHo."""
    t = pd.DataFrame({'ipc_oficial': pond_ipc_oficial(), 'tp_original': POND_TP_ORIGINAL})
    for p in POBLACIONES:
        t[p] = canasta(h, p, metodo)
    t.index.name = 'codigo'
    t.insert(0, 'division', [DIVISIONES[d] for d in t.index])
    return t


def resumen_poblaciones(h: pd.DataFrame) -> pd.DataFrame:
    """Tamano muestral y expandido de cada poblacion."""
    filas = []
    for p, desc in POBLACIONES.items():
        m = (h['tp_1'] | h['tp_2']) if p == 'tp' else h[p]
        filas.append({'poblacion': p, 'descripcion': desc, 'hogares_muestra': int(m.sum()),
                      'hogares_expandidos': float(h.loc[m, 'pondera'].sum()),
                      'gasto_medio_hogar': float(np.average(h.loc[m, 'gastot'], weights=h.loc[m, 'pondera']))})
    return pd.DataFrame(filas)


def canastas_regionales(h: pd.DataFrame, poblacion: str) -> pd.DataFrame:
    """Gasto agregado (expandido) region x division de una poblacion, para el indice regional."""
    sub = h[h[poblacion]] if poblacion != 'tp' else h[h['con_65']]
    g = sub[GC].mul(sub['pondera'], axis=0).groupby(sub['region_ipc']).sum()
    g.columns = DIVS
    return g


def bootstrap_canastas(h: pd.DataFrame, poblaciones: list[str], n: int = 500, semilla: int = 2018,
                       metodo: str = 'plutocratica') -> dict[str, np.ndarray]:
    """Remuestreo de hogares (con reposicion, estratificado por region) para medir la incertidumbre
    muestral de las ponderaciones. Devuelve {poblacion: matriz n x 12}."""
    rng = np.random.default_rng(semilla)
    grupos = [np.flatnonzero(h['region'].values == r) for r in sorted(h['region'].unique())]
    out = {p: np.empty((n, len(DIVS))) for p in poblaciones}
    for b in range(n):
        idx = np.concatenate([rng.choice(g, size=len(g), replace=True) for g in grupos])
        hb = h.iloc[idx]
        for p in poblaciones:
            out[p][b] = canasta(hb, p, metodo).values
    return out
