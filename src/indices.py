"""Calculo de indices de precios por canasta y comparacion con el IPC.

Metodo (el mismo concepto que usa el INDEC): indice de canasta fija (Lowe/Laspeyres).
Las cantidades de la canasta quedan fijas en el periodo de la encuesta y se valorizan con los
indices de precios por division de cada mes:

    IIJP_t = sum_i q_i * I_i,t ,   q_i = w_i / Ibar_i,ref

donde w_i es la participacion del gasto en la division i medida por la ENGHo 2017/18 e Ibar_i,ref
el nivel promedio del indice de esa division durante el relevamiento (nov-2017 a nov-2018).
Equivale a decir que la ponderacion efectiva de cada division se actualiza con sus precios relativos:
si un rubro se abarata en terminos relativos (p. ej. tarifas congeladas 2019-2023), pesa menos.

El TP original, en cambio, aplicaba siempre las mismas ponderaciones a las variaciones mensuales
(sum_i w_i * pi_i,t). Eso no es un indice de canasta fija: cuando hay grandes cambios de precios
relativos sobrepondera los rubros atrasados y genera una brecha artificial con el IPC
(se incluye `metodo_tp` solo para cuantificar ese sesgo).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DIVS = [f'{i:02d}' for i in range(1, 13)]
REF_ENGHO = ('2017-11', '2018-11')  # periodo de relevamiento de la ENGHo 2017/18
BASE = pd.Period('2016-12', 'M')


def _w(w) -> pd.Series:
    w = pd.Series(w, index=DIVS) if not isinstance(w, pd.Series) else w.reindex(DIVS)
    return w / w.sum()


def lowe(I: pd.DataFrame, w, ref=REF_ENGHO, base=BASE) -> pd.Series:
    """Indice de canasta fija con cantidades del periodo ref (base=100)."""
    pref = I.loc[ref[0]:ref[1], DIVS].mean()
    nivel = (I[DIVS] * (_w(w) / pref)).sum(axis=1)
    return nivel / nivel.loc[base] * 100


def laspeyres(I: pd.DataFrame, w, base=BASE) -> pd.Series:
    """Laspeyres con ponderaciones del periodo base (asi esta construido el IPC oficial)."""
    nivel = (I[DIVS] / I.loc[base, DIVS] * _w(w)).sum(axis=1)
    return nivel / nivel.loc[base] * 100


def lowe_regional(indices_region: dict[str, pd.DataFrame], gasto_region: pd.DataFrame,
                  ref=REF_ENGHO, base=BASE) -> pd.Series:
    """Indice de canasta fija con canastas e indices de precios regionales (6 regiones del IPC)."""
    tot = gasto_region.values.sum()
    nivel = 0
    for r, I in indices_region.items():
        w = gasto_region.loc[r, DIVS] / tot
        pref = I.loc[ref[0]:ref[1], DIVS].mean()
        nivel = nivel + (I[DIVS] * (w / pref)).sum(axis=1)
    return nivel / nivel.loc[base] * 100


def metodo_tp(V: pd.DataFrame, w) -> pd.Series:
    """Variacion mensual como la calculaba el TP: ponderaciones fijas sobre las variaciones
    mensuales publicadas (1 decimal). Devuelve variaciones (fraccion), no niveles."""
    return (V[DIVS] * _w(w)).sum(axis=1)


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


def ponderacion_efectiva(I: pd.DataFrame, w, t, ref=REF_ENGHO) -> pd.Series:
    """Participacion que tiene cada division en el valor de la canasta fija en el mes t."""
    pref = I.loc[ref[0]:ref[1], DIVS].mean()
    v = (_w(w) / pref) * I.loc[pd.Period(t, 'M'), DIVS]
    return v / v.sum()


def descomposicion(I: pd.DataFrame, w_a, w_b, desde, hasta, ref_a=REF_ENGHO, ref_b=None) -> pd.DataFrame:
    """Aporte de cada division a la brecha entre dos canastas fijas, (A_h/A_d) / (B_h/B_d) - 1.

    (A_h/A_d) / (B_h/B_d) - 1 = sum_i (wa_i - wb_i) * (R_i - R_B) / R_B
    con wa, wb = ponderaciones efectivas en `desde`, R_i = I_i,h / I_i,d y R_B = B_h/B_d.
    Una division suma brecha si la canasta A la pondera mas que la B y sus precios subieron mas
    que el promedio de B (o al reves). Los aportes suman exactamente la brecha (en %)."""
    d, h = pd.Period(desde, 'M'), pd.Period(hasta, 'M')
    wa = ponderacion_efectiva(I, w_a, d, ref_a)
    if ref_b is None:  # B es un Laspeyres base dic-2016 (IPC oficial): sus cantidades son w/I_base
        ref_b = (str(BASE), str(BASE))
    wb = ponderacion_efectiva(I, w_b, d, ref_b)
    R = I.loc[h, DIVS] / I.loc[d, DIVS]
    RB = float((wb * R).sum())
    out = pd.DataFrame({'pond_efectiva_a': wa, 'pond_efectiva_b': wb, 'var_division': R - 1,
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
    Responde: la diferencia es sistematica o va y viene?"""
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


def tabla_periodos(niveles: dict[str, pd.Series], referencia: str = 'IPC oficial') -> pd.DataFrame:
    """Inflacion acumulada por periodo de cada indice y su brecha (en %) contra la referencia."""
    filas = []
    ultimo = min(s.dropna().index.max() for s in niveles.values())
    for nombre, d, h in PERIODOS:
        h = h or str(ultimo)
        if pd.Period(h, 'M') > ultimo:
            continue
        fila = {'periodo': nombre, 'desde': d, 'hasta': h}
        ref = acumulada(niveles[referencia], d, h)
        for k, s in niveles.items():
            a = acumulada(s, d, h)
            fila[f'{k} (%)'] = a * 100
            if k != referencia:
                fila[f'brecha {k} vs {referencia} (%)'] = ((1 + a) / (1 + ref) - 1) * 100
        filas.append(fila)
    return pd.DataFrame(filas)
