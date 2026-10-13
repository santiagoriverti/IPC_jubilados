"""Tests de la estructura de precios por aperturas (datos sinteticos, no descargan nada)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import estructura as estr  # noqa: E402
from src import fuentes, indices  # noqa: E402


@pytest.fixture
def sintetico():
    """6 regiones con divisiones 01 (publica 01.1, no publica 01.2) y 02 (sin aperturas)."""
    rng = np.random.default_rng(3)
    idx = pd.period_range('2016-12', '2019-12', freq='M')
    filas, pond, ocultos = [], {}, {}
    for r in fuentes.REGIONES:
        w11, w12, w02 = 0.3, 0.2, 0.5
        s = {c: 100 * np.cumprod(np.r_[1, 1 + rng.normal(0.02, 0.01, len(idx) - 1)]) for c in ['01.1', '01.2', '02']}
        s['01'] = (w11 * s['01.1'] + w12 * s['01.2']) / (w11 + w12)
        s['0'] = (w11 + w12) * s['01'] + w02 * s['02']
        ocultos[r] = pd.Series(s['01.2'], index=idx)
        for c in ['0', '01', '01.1', '02']:
            filas += [{'periodo': p, 'region': r, 'codigo': c, 'descripcion': c, 'indice': v} for p, v in zip(idx, s[c])]
        pond[r] = {'0': 1.0, '01': w11 + w12, '01.1': w11, '01.2': w12, '02': w02}
    W = pd.DataFrame(pond)
    W.insert(0, 'descripcion', W.index)
    return pd.DataFrame(filas), W, ocultos


def test_resto_derivado_reproduce_la_serie_no_publicada(sintetico):
    ap, W, ocultos = sintetico
    e = estr.construir(ap, W)
    for r in fuentes.REGIONES:
        assert np.allclose(e.precios[(r, '01.r')], ocultos[r])
    assert set(e.nodos.loc[e.nodos['region'] == 'GBA', 'nodo']) == {'01.1', '01.r', '02'}


def test_ponderaciones_oficiales_replican_el_nivel_general(sintetico):
    ap, W, _ = sintetico
    e = estr.construir(ap, W)
    for r in fuentes.REGIONES:
        cols = [c for c in e.precios.columns if c[0] == r]
        rep = indices.laspeyres(e.precios[cols], e.pond_oficial()[cols])
        gen = ap[(ap['region'] == r) & (ap['codigo'] == '0')].set_index('periodo')['indice']
        assert np.allclose(rep.values, gen.values)


def test_resto_chico_usa_el_indice_del_agregado(sintetico):
    ap, W, _ = sintetico
    e = estr.construir(ap, W, umbral=0.25)  # el resto (0,2) queda por debajo del umbral
    div01 = ap[(ap['region'] == 'GBA') & (ap['codigo'] == '01')]['indice'].values
    assert np.allclose(e.precios[('GBA', '01.r')].values, div01)


def test_asignacion_de_codigos(sintetico):
    ap, W, _ = sintetico
    e = estr.construir(ap, W)
    assert e.asignar('GBA', ['01.1.4', '01.1', '01']) == '01.1'
    assert e.asignar('GBA', ['01.2.1', '01.2', '01']) == '01.r'
    assert e.asignar('GBA', ['02.1.1', '02.1', '02']) == '02'


def test_codigos_y_jerarquia():
    assert estr.codigo_engho('A0411') == '04.1.1'
    assert estr.codigo_engho('A04') == '04'
    assert estr.hijos_publicados('06', {'06', '06.1', '06.4.1', '06.1.1'}) == ['06.1', '06.4.1']


def test_concordancia_engho_ipc():
    # Expensas: la ENGHo las codifica en 04.4.4; el IPC, en 04.1.3 (gastos comunes)
    assert estr.codigos_ipc('A0444', 'A044', 'A04') == ['04.1.3', '04.1', '04']
    assert estr.codigos_ipc('A0412', 'A041', 'A04') == ['04.1.1', '04.1', '04']
    assert estr.codigos_ipc('A0441', 'A044', 'A04') == ['04.4.1', '04.4', '04']
    # la concordancia nunca cambia la division
    assert all(v[:2] == k[1:3] for k, v in estr.CONCORDANCIA_ENGHO.items())


def test_huecos_se_completan_con_la_variacion_del_agregado():
    idx = pd.period_range('2020-01', periods=4, freq='M')
    P = pd.DataFrame({'0': [100, 110, 121, 133.1], '03': [100, 110, 121, 133.1], '03.1': [100, np.nan, np.nan, 140]},
                     index=idx)
    Q, imp = estr.completar_huecos(P)
    assert Q['03.1'].tolist() == pytest.approx([100, 110, 121, 140])
    assert imp[0]['con_variacion_de'] == '03'
