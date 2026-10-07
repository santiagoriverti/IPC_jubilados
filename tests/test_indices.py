"""Tests rapidos con datos sinteticos (no descargan nada). Correr: python -m pytest tests -q"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import fiscal, haberes, indices  # noqa: E402

DIVS = indices.DIVS


@pytest.fixture
def precios():
    rng = np.random.default_rng(0)
    idx = pd.period_range('2016-12', '2020-12', freq='M')
    v = rng.normal(0.02, 0.01, size=(len(idx), 12))
    v[0] = 0
    I = pd.DataFrame(100 * np.cumprod(1 + v, axis=0), index=idx, columns=DIVS)
    w = pd.Series(rng.dirichlet(np.ones(12)), index=DIVS)
    I['0'] = indices.laspeyres(I, w)
    return I, w


def test_lowe_con_referencia_en_la_base_es_laspeyres(precios):
    I, w = precios
    a = indices.lowe(I, w, ref=('2016-12', '2016-12'))
    b = indices.laspeyres(I, w)
    assert np.allclose(a, b)


def test_canasta_fija_no_es_metodo_tp(precios):
    I, w = precios
    v = I[DIVS].pct_change()
    tp = indices.nivel_desde_variaciones(indices.metodo_tp(v, w))
    lw = indices.laspeyres(I, w)
    assert not np.allclose(tp.values, lw.values)  # el metodo del TP no replica una canasta fija


def test_descomposicion_suma_la_brecha(precios):
    I, w = precios
    w2 = pd.Series(np.roll(w.values, 3), index=DIVS)
    d = indices.descomposicion(I, w, w2, '2018-06', '2020-12', ref_b=indices.REF_ENGHO)
    a = indices.lowe(I, w)
    b = indices.lowe(I, w2)
    brecha = (indices.acumulada(a, '2018-06', '2020-12') + 1) / (indices.acumulada(b, '2018-06', '2020-12') + 1) - 1
    assert d['aporte_pct'].sum() == pytest.approx(brecha * 100, abs=1e-9)
    assert d.attrs['brecha_pct'] == pytest.approx(brecha * 100, abs=1e-9)


def test_acumulada_excluye_mes_inicial():
    n = pd.Series([100, 110, 121], index=pd.period_range('2023-11', periods=3, freq='M'))
    assert indices.acumulada(n, '2023-12', '2024-01') == pytest.approx(0.10)


def test_newey_west_ruido_blanco():
    x = np.random.default_rng(1).normal(size=5000)
    assert indices.newey_west_se(x) == pytest.approx(1 / np.sqrt(5000), rel=0.1)


def test_contrafactual_reproduce_regla():
    idx = pd.period_range('2024-01', '2024-08', freq='M')
    infl = pd.Series([0.2, 0.13, 0.11, 0.088, 0.042, 0.046, 0.04, 0.042], index=idx)
    h = pd.Series(100.0, index=idx)
    for k in range(4, len(idx)):
        h.iloc[k] = h.iloc[k - 1] * (1 + infl.iloc[k - 2])
    cf = haberes.contrafactual(h, infl, desde='2024-04')
    assert np.allclose(cf.values, h.loc['2024-04':].values)


def test_desvio_permanente_cero():
    t = fiscal.desvio_permanente(6.5, desvios_pp=(0.0,), anios=(10,))
    assert t['costo_pct_gasto_prev'].iloc[0] == 0
