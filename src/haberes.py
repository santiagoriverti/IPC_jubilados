"""Haber minimo, bono y poder adquisitivo.

Regimen de movilidad vigente (DNU 274/2024): desde mayo de 2024 el haber del mes t se actualiza
con la variacion mensual del IPC nacional de t-2, calculada desde los niveles del indice y
redondeada a 2 decimales (no la publicada a 1 decimal: verificado en los datos). Abril 2024 fue un mes de
transicion (+27,4% = IPC de febrero 13,2% y un 12,5% adicional). El bono ($70.000 desde marzo
2024) no se actualiza.

Contrafactual: el mismo regimen pero usando el IIJP en lugar del IPC. Como la regla es identica,
la diferencia entre ambos haberes es puramente el efecto del indice.

Haber de cada segmento (minima, promedio, alto): no hay serie oficial del haber medio. Desde dic-2016 la
movilidad aplico el mismo porcentaje a todos los haberes salvo en marzo de 2020 (decreto 163/2020: 2,3% mas
una suma fija de $1.500, con piso en el nuevo minimo; la serie del haber minimo lo confirma: +12,97%). Se
simula el haber de cada perceptor de la ENGHo 2017/18 a partir de su posicion en la escala (k = haber / haber
minimo del trimestre de la entrevista): quienes cobran hasta un minimo (pensiones no contributivas, PUAM,
minima) siguen al haber minimo; los demas, la regla general. El bono se suma como complemento hasta minimo +
bono (regla de los decretos; se aplica igual a los refuerzos de 2022-2023, que tuvieron tramos distintos).
Supuesto: cada perceptor conserva su posicion en la escala (sin altas ni bajas de beneficios).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

INICIO_DNU = pd.Period('2024-04', 'M')  # ultimo mes previo a la indexacion mensual por IPC(t-2)
# Meses en que la movilidad no fue un porcentaje uniforme: periodo -> (porcentaje, suma fija en $)
AJUSTES_SUMA_FIJA = {pd.Period('2020-03', 'M'): (0.023, 1500.0)}  # decreto 163/2020


def var_movilidad(nivel: pd.Series) -> pd.Series:
    """Variacion mensual calculada desde los niveles y redondeada a 2 decimales en %: es la que usa
    ANSES para la movilidad (verificado: error 0 en todos los meses desde mayo 2024; con la variacion
    publicada a 1 decimal el error llega a 0,05 p.p.)."""
    return (nivel.pct_change() * 100).round(2) / 100


def tabla_haberes(haber: pd.Series, bono: pd.Series) -> pd.DataFrame:
    t = pd.DataFrame({'haber_minimo': haber})
    t['bono'] = bono.reindex(t.index)
    t['haber_con_bono'] = t['haber_minimo'] + t['bono']
    return t


def real(serie: pd.Series, nivel_precios: pd.Series, base) -> pd.Series:
    """Serie a precios del mes base."""
    p = nivel_precios.reindex(serie.index)
    return serie * float(nivel_precios.loc[pd.Period(base, 'M')]) / p


def contrafactual(haber: pd.Series, infl_alternativa: pd.Series, desde=INICIO_DNU, rezago: int = 2) -> pd.Series:
    """Haber que resultaria de indexar desde `desde` con otra inflacion mensual (fraccion), con el
    mismo rezago que la formula vigente. En `desde` coincide con el haber efectivo."""
    desde = pd.Period(desde, 'M')
    idx = haber.loc[desde:].index
    out = pd.Series(index=idx, dtype=float)
    out.iloc[0] = haber.loc[desde]
    for k in range(1, len(idx)):
        t = idx[k]
        out.iloc[k] = out.iloc[k - 1] * (1 + infl_alternativa.loc[t - rezago])
    return out


def haber_perceptores(haber_minimo: pd.Series, k: np.ndarray, ajustes=AJUSTES_SUMA_FIJA) -> np.ndarray:
    """Haber (sin bono) de cada perceptor, meses x perceptores. k: haber / haber minimo en el primer mes
    (la posicion en la escala no cambia con aumentos uniformes, asi que la medida en 2017/18 vale para dic-2016)."""
    m = haber_minimo.values.astype(float)
    k = np.asarray(k, dtype=float)
    out = np.empty((len(m), len(k)))
    h = k * m[0]
    out[0] = h
    for i in range(1, len(m)):
        t = haber_minimo.index[i]
        if t in ajustes:
            p, s = ajustes[t]
            h = np.where(k <= 1, k * m[i], np.maximum(m[i], h * (1 + p) + s))
        else:
            h = h * m[i] / m[i - 1]
        out[i] = h
    return out


def bono_complemento(haber: np.ndarray, haber_minimo: pd.Series, bono: pd.Series) -> np.ndarray:
    """Bono de cada perceptor: el monto completo hasta el minimo y la diferencia hasta minimo + bono
    para los haberes superiores (0 en los meses sin bono cargado)."""
    m = haber_minimo.values.astype(float)[:, None]
    b = bono.reindex(haber_minimo.index).fillna(0).values.astype(float)[:, None]
    return np.clip(m + b - haber, 0, b)


def haber_segmentos(haber_minimo: pd.Series, bono: pd.Series, perceptores: pd.DataFrame,
                    segmentos: dict[str, pd.Series]) -> pd.DataFrame:
    """Haber medio por perceptor de cada segmento, sin y con bono (pesos corrientes, ponderado por pondera).
    perceptores: id, k y pondera (ponderaciones.perceptores); segmentos: {nombre: marca por hogar}."""
    hp = haber_perceptores(haber_minimo, perceptores['k'].values)
    hb = hp + bono_complemento(hp, haber_minimo, bono)
    cols = {}
    for s, marca in segmentos.items():
        sel = perceptores['id'].map(marca).fillna(False).values.astype(bool)
        w = perceptores['pondera'].values[sel]
        cols[f'haber_{s}'] = hp[:, sel] @ w / w.sum()
        cols[f'haber_con_bono_{s}'] = hb[:, sel] @ w / w.sum()
        cols[f'haber_minimos_{s}'] = cols[f'haber_{s}'] / haber_minimo.values
    return pd.DataFrame(cols, index=haber_minimo.index)


def verificar_regla(haber: pd.Series, var_ipc: pd.Series, desde='2024-05', tol=0.00005) -> pd.DataFrame:
    """Chequea que el haber efectivo siga la regla haber_t = haber_t-1 x (1 + IPC_t-2).
    tol = 0,005 p.p.: solo absorbe el redondeo del haber a centavos."""
    filas = []
    for t in haber.loc[desde:].index:
        if t - 2 not in var_ipc.index or pd.isna(var_ipc.loc[t - 2]):
            continue
        obs = haber.loc[t] / haber.loc[t - 1] - 1
        esp = var_ipc.loc[t - 2]
        filas.append({'periodo': str(t), 'aumento_observado': obs, 'ipc_t_menos_2': esp,
                      'ok': abs(obs - esp) <= tol})
    return pd.DataFrame(filas)
