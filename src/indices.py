"""Calculo de indices de precios por canasta y comparacion con el IPC.

Las funciones reciben una matriz de precios P (periodo x componentes; los componentes pueden ser las 12
divisiones o los nodos (region, apertura) de estructura.Estructura) y una canasta w indexada por esos
mismos componentes.

Metodo principal (el mismo concepto que el IPC): indice de canasta fija (Lowe). Las cantidades de la
canasta quedan fijas en el periodo de la encuesta y se valorizan con los indices de precios de cada mes:

    IIJP_t = sum_i q_i * I_i,t ,   q_i = w_i / Ibar_i,ref

donde w_i es la participacion del gasto en el componente i medida por la ENGHo 2017/18 e Ibar_i,ref el
nivel promedio de su indice durante el relevamiento (nov-2017 a nov-2018). Equivale a actualizar por
precios las ponderaciones desde el periodo de la encuesta (lo que recomienda el Manual del IPC de
OIT/FMI y hace el INDEC): si un rubro se abarata en terminos relativos (tarifas congeladas 2019-2023),
pesa menos.

Alternativas para la tabla de sensibilidad: Young (participaciones de la encuesta fijas sobre los
relativos de precios desde la base, sin actualizar por precios) y geometrica (Cobb-Douglas).

El TP original aplicaba siempre las mismas ponderaciones a las variaciones mensuales
(sum_i w_i * pi_i,t). Eso no es un indice de canasta fija: cuando hay grandes cambios de precios
relativos sobrepondera los rubros atrasados y genera una brecha artificial con el IPC (`metodo_tp`
queda solo para la revision del TP).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DIVS = [f'{i:02d}' for i in range(1, 13)]
REF_ENGHO = ('2017-11', '2018-11')  # periodo de relevamiento de la ENGHo 2017/18
BASE = pd.Period('2016-12', 'M')


def _w(w) -> pd.Series:
    """Canasta normalizada (suma 1). Un vector sin indice se interpreta como las 12 divisiones."""
    w = w if isinstance(w, pd.Series) else pd.Series(np.asarray(w, dtype=float), index=DIVS)
    return w / w.sum()


def lowe(P: pd.DataFrame, w, ref=REF_ENGHO, base=BASE) -> pd.Series:
    """Indice de canasta fija con cantidades del periodo ref (base=100)."""
    w = _w(w)
    pref = P.loc[ref[0]:ref[1], w.index].mean()
    nivel = P[w.index] @ (w / pref)
    return nivel / nivel.loc[base] * 100


def lowe_cantidades(P: pd.DataFrame, q: pd.Series, base=BASE) -> pd.Series:
    """Indice de canasta fija con cantidades q dadas (en unidades de indice)."""
    nivel = P[q.index] @ q
    return nivel / nivel.loc[base] * 100


def laspeyres(P: pd.DataFrame, w, base=BASE) -> pd.Series:
    """Ponderaciones fijas sobre los relativos de precios desde la base. Con ponderaciones del periodo
    base es el Laspeyres con que se calcula el IPC oficial; con las de otro periodo, el indice de Young."""
    w = _w(w)
    nivel = (P[w.index] / P.loc[base, w.index]) @ w
    return nivel / nivel.loc[base] * 100


young = laspeyres


def geometrica(P: pd.DataFrame, w, base=BASE) -> pd.Series:
    """Media geometrica ponderada de los relativos de precios (Cobb-Douglas)."""
    w = _w(w)
    return np.exp(np.log(P[w.index] / P.loc[base, w.index]) @ w) * 100


def metodo_tp(V: pd.DataFrame, w) -> pd.Series:
    """Variacion mensual como la calculaba el TP: ponderaciones fijas sobre las variaciones
    mensuales publicadas (1 decimal). Devuelve variaciones (fraccion), no niveles."""
    w = _w(w)
    return V[w.index] @ w


def nivel_desde_variaciones(v: pd.Series, base=BASE) -> pd.Series:
    """Encadena variaciones mensuales en un nivel (base=100)."""
    v = v.copy()
    v.loc[base] = 0.0
    v = v.sort_index().loc[base:]
    return (1 + v.fillna(0)).cumprod() * 100


def var_mensual(nivel: pd.Series) -> pd.Series:
    return nivel.pct_change()


def var_interanual(nivel: pd.Series) -> pd.Series:
    return nivel / nivel.shift(12) - 1


def acumulada(nivel: pd.Series, desde, hasta) -> float:
    """Variacion entre el nivel de `desde` y el de `hasta` (no incluye la inflacion del mes `desde`).
    'Entre dic-2023 y may-2026' = acumulada(nivel, '2023-12', '2026-05')."""
    return float(nivel.loc[pd.Period(hasta, 'M')] / nivel.loc[pd.Period(desde, 'M')] - 1)


def brecha(a: pd.Series, b: pd.Series, desde, hasta) -> float:
    """Brecha acumulada entre dos indices, en %: (1 + infl. A) / (1 + infl. B) - 1."""
    return ((1 + acumulada(a, desde, hasta)) / (1 + acumulada(b, desde, hasta)) - 1) * 100


def ponderacion_efectiva(P: pd.DataFrame, w, t, ref=REF_ENGHO) -> pd.Series:
    """Participacion que tiene cada componente en el valor de la canasta fija en el mes t."""
    w = _w(w)
    pref = P.loc[ref[0]:ref[1], w.index].mean()
    v = (w / pref) * P.loc[pd.Period(t, 'M'), w.index]
    return v / v.sum()


def descomposicion(P: pd.DataFrame, w_a, w_b, desde, hasta, ref_a=REF_ENGHO, ref_b=None) -> pd.DataFrame:
    """Aporte de cada componente a la brecha entre dos canastas fijas, (A_h/A_d) / (B_h/B_d) - 1.

    (A_h/A_d) / (B_h/B_d) - 1 = sum_i (wa_i - wb_i) * (R_i - R_B) / R_B
    con wa, wb = ponderaciones efectivas en `desde`, R_i = I_i,h / I_i,d y R_B = B_h/B_d.
    Un componente suma brecha si la canasta A lo pondera mas que la B y sus precios subieron mas
    que el promedio de B (o al reves). Los aportes suman exactamente la brecha (en %)."""
    d, h = pd.Period(desde, 'M'), pd.Period(hasta, 'M')
    w_a, w_b = _w(w_a), _w(w_b)
    idx = w_a.index.union(w_b.index, sort=False)
    wa = ponderacion_efectiva(P, w_a, d, ref_a).reindex(idx, fill_value=0.0)
    if ref_b is None:  # B es un Laspeyres base dic-2016 (IPC oficial): sus cantidades son w/I_base
        ref_b = (str(BASE), str(BASE))
    wb = ponderacion_efectiva(P, w_b, d, ref_b).reindex(idx, fill_value=0.0)
    R = P.loc[h, idx] / P.loc[d, idx]
    RB = float((wb * R).sum())
    out = pd.DataFrame({'pond_efectiva_a': wa, 'pond_efectiva_b': wb, 'var_componente': R - 1,
                        'aporte_pct': (wa - wb) * (R - RB) / RB * 100})
    out.attrs['brecha_pct'] = float(((wa * R).sum() / RB - 1) * 100)
    return out


def newey_west_se(x: np.ndarray, lags: int | None = None) -> float:
    """Error estandar de la media robusto a autocorrelacion (Newey-West, nucleo de Bartlett)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if lags is None:
        lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    e = x - x.mean()
    s = e @ e / n
    for k in range(1, lags + 1):
        s += 2 * (1 - k / (lags + 1)) * (e[k:] @ e[:-k]) / n
    return float(np.sqrt(s / n))


def brecha_mensual(nivel_a: pd.Series, nivel_b: pd.Series, desde=None, hasta=None) -> dict:
    """Diferencia media mensual (en log) entre dos indices, con IC 95% Newey-West.
    Responde: la diferencia es persistente mes a mes o se concentra en pocos meses? (Con pocos meses el
    test tiene poca potencia; la incertidumbre de la canasta se mide con el bootstrap.)"""
    d = np.log(nivel_a / nivel_a.shift(1)) - np.log(nivel_b / nivel_b.shift(1))
    d = d.loc[desde:hasta].dropna()
    m, se = d.mean(), newey_west_se(d.values)
    return {'meses': len(d), 'media_pp_mes': m * 100, 'ic95_inf': (m - 1.96 * se) * 100,
            'ic95_sup': (m + 1.96 * se) * 100, 'anualizada_pp': (np.exp(12 * m) - 1) * 100,
            'meses_a_mayor': int((d > 0).sum()), 'acumulada_pct': (np.exp(d.sum()) - 1) * 100}


PERIODOS = [
    ('Completo', '2016-12', None),
    ('Macri (dic-16 a dic-19)', '2016-12', '2019-12'),
    ('Fernández (dic-19 a nov-23)', '2019-12', '2023-11'),
    ('Milei (nov-23 al último dato)', '2023-11', None),
    ('Shock tarifario (nov-23 a dic-24)', '2023-11', '2024-12'),
    ('Desde 2025 (dic-24 al último dato)', '2024-12', None),
    ('Ventana del TP (nov-23 a may-26)', '2023-11', '2026-05'),
]


def periodos_vigentes(ultimo) -> list[tuple[str, str, str]]:
    """PERIODOS con el ultimo dato resuelto, sin los que terminan despues del ultimo dato."""
    ultimo = pd.Period(ultimo, 'M')
    out = []
    for nombre, d, h in PERIODOS:
        h = h or str(ultimo)
        if pd.Period(h, 'M') <= ultimo:
            out.append((nombre, d, h))
    return out


def tabla_periodos(niveles: dict[str, pd.Series], referencia: str = 'IPC oficial') -> pd.DataFrame:
    """Inflacion acumulada por periodo de cada indice y su brecha (en %) contra la referencia."""
    filas = []
    ultimo = min(s.dropna().index.max() for s in niveles.values())
    for nombre, d, h in periodos_vigentes(ultimo):
        fila = {'periodo': nombre, 'desde': d, 'hasta': h}
        ref = acumulada(niveles[referencia], d, h)
        for k, s in niveles.items():
            a = acumulada(s, d, h)
            fila[f'{k} (%)'] = a * 100
            if k != referencia:
                fila[f'brecha {k} vs {referencia} (%)'] = ((1 + a) / (1 + ref) - 1) * 100
        filas.append(fila)
    return pd.DataFrame(filas)
