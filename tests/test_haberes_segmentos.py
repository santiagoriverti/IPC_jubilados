"""Simulacion del haber de cada perceptor: movilidad uniforme salvo la suma fija de mar-2020, y bono como
complemento hasta minimo + bono (sin datos ni internet)."""
import numpy as np
import pandas as pd

from src import haberes

IDX = pd.period_range('2020-01', '2020-05', freq='M')
MINIMO = pd.Series([14068.0, 14068.0, 15891.564, 15891.564, 16000.0], index=IDX)  # feb->mar: 2,3% + $1.500


def test_minimo_y_fracciones_siguen_al_minimo():
    h = haberes.haber_perceptores(MINIMO, [1.0, 0.7])
    np.testing.assert_allclose(h[:, 0], MINIMO.values)
    np.testing.assert_allclose(h[:, 1], 0.7 * MINIMO.values)


def test_suma_fija_de_marzo_2020():
    h = haberes.haber_perceptores(MINIMO, [3.0])[:, 0]
    assert np.isclose(h[2], 3 * 14068 * 1.023 + 1500)            # 2,3% + $1.500
    assert np.isclose(h[2] / h[1] - 1, 0.023 + 1500 / (3 * 14068))  # ~5,9%, no 13%
    assert np.isclose(h[4] / h[3], 16000 / 15891.564)             # despues, uniforme


def test_piso_en_el_nuevo_minimo():
    h = haberes.haber_perceptores(MINIMO, [1.05])[:, 0]
    assert h[2] >= MINIMO.iloc[2] - 1e-9


def test_bono_complemento():
    m = pd.Series([100.0, 100.0], index=IDX[:2])
    b = pd.Series([20.0], index=IDX[1:2])
    hab = np.array([[80.0, 100.0, 110.0, 130.0], [80.0, 100.0, 110.0, 130.0]])
    out = haberes.bono_complemento(hab, m, b)
    np.testing.assert_allclose(out[0], 0)                    # mes sin bono
    np.testing.assert_allclose(out[1], [20, 20, 10, 0])      # completo, completo, diferencia, nada


def test_haber_segmentos_promedio_ponderado():
    per = pd.DataFrame({'id': [1, 1, 2], 'k': [1.0, 2.0, 3.0], 'pondera': [1.0, 1.0, 2.0]})
    seg = {'a': pd.Series({1: True, 2: False}), 'b': pd.Series({1: True, 2: True})}
    t = haberes.haber_segmentos(MINIMO, pd.Series(dtype=float), per, seg)
    assert np.isclose(t.loc[IDX[0], 'haber_minimos_a'], 1.5)
    assert np.isclose(t.loc[IDX[0], 'haber_minimos_b'], (1 + 2 + 2 * 3) / 4)
