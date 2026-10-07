"""Costo fiscal de indexar los haberes por el IIJP en lugar del IPC.

Como la movilidad aplica el mismo porcentaje a todos los haberes, indexar por otro indice cambia
el gasto en la misma proporcion que el haber:

    costo extra_t = gasto previsional_t x (haber IIJP_t / haber IPC_t - 1)

El gasto previsional sale de la IMIG (Sector Publico Nacional, base caja): jubilaciones y pensiones
contributivas + pensiones no contributivas (incluye aguinaldo en junio y diciembre). Es una cota
superior: ese gasto incluye el bono, que no se indexa (~5-7% del total).

Esto reemplaza el calculo del TP original, que multiplicaba diferencias del haber minimo por
cantidades de beneficiarios con supuestos de haber medio (2,6 x minimo) y mezclaba costo
incremental con gasto total.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def costo_mensual(factor: pd.Series, imig: pd.DataFrame) -> pd.DataFrame:
    gasto = (imig['jub_contributivas'] + imig['pnc']).rename('gasto_previsional')
    t = pd.concat([gasto, factor.rename('factor')], axis=1).dropna()
    t['costo_extra'] = t['gasto_previsional'] * (t['factor'] - 1)
    t['costo_pct_gasto'] = (t['factor'] - 1) * 100
    return t


def costo_anual(mensual: pd.DataFrame, imig: pd.DataFrame, pib_anual: pd.Series) -> pd.DataFrame:
    m = mensual.join(imig[['resultado_primario', 'resultado_financiero']], how='left')
    m['anio'] = m.index.year
    g = m.groupby('anio').agg(meses=('factor', 'size'), gasto_previsional=('gasto_previsional', 'sum'),
                              costo_extra=('costo_extra', 'sum'), resultado_primario=('resultado_primario', 'sum'),
                              resultado_financiero=('resultado_financiero', 'sum'))
    g['costo_pct_gasto_prev'] = g['costo_extra'] / g['gasto_previsional'] * 100
    g['costo_pct_res_primario'] = g['costo_extra'] / g['resultado_primario'] * 100
    g['costo_pct_res_financiero'] = g['costo_extra'] / g['resultado_financiero'] * 100
    g['pib'] = pib_anual.reindex(g.index)
    g['costo_pct_pib'] = g['costo_extra'] / g['pib'] * 100
    g['gasto_prev_pct_pib'] = g['gasto_previsional'] / g['pib'] * 100
    return g


def desvio_permanente(gasto_prev_pct_pib: float, desvios_pp=(0.1, 0.25, 0.5, 1.0),
                      anios=(1, 5, 10, 25)) -> pd.DataFrame:
    """Costo de que el IIJP supere al IPC en d puntos por anio, todos los anios.

    El costo relativo al gasto previsional es (1+d)^n - 1 y no depende de la demografia (que
    escala por igual el gasto con y sin el cambio de indice). Pasado a % del PIB con la relacion
    gasto previsional / PIB actual (si esa relacion sube por envejecimiento, el costo sube igual)."""
    filas = []
    for d in desvios_pp:
        for n in anios:
            rel = (1 + d / 100) ** n - 1
            filas.append({'desvio_pp_anual': d, 'anios': n, 'costo_pct_gasto_prev': rel * 100,
                          'costo_pct_pib': rel * gasto_prev_pct_pib})
    return pd.DataFrame(filas)
