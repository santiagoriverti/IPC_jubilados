"""Haber minimo, bono y poder adquisitivo.

Regimen de movilidad vigente (DNU 274/2024): desde mayo de 2024 el haber del mes t se actualiza
con la variacion mensual del IPC nacional de t-2, calculada desde los niveles del indice y
redondeada a 2 decimales (no la publicada a 1 decimal: verificado en los datos). Abril 2024 fue un mes de
transicion (+27,4% = IPC de febrero 13,2% y un 12,5% adicional). El bono ($70.000 desde marzo
2024) no se actualiza.

Contrafactual: el mismo regimen pero usando el IIJP en lugar del IPC. Como la regla es identica,
la diferencia entre ambos haberes es puramente el efecto del indice.
"""
from __future__ import annotations

import pandas as pd

INICIO_DNU = pd.Period('2024-04', 'M')  # ultimo mes previo a la indexacion mensual por IPC(t-2)


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
