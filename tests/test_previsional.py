"""Lectura del BESS (sin red): rotulos de intervalos, tramos de haber y cuadros armados a mano con el formato
del boletin."""
import math
from datetime import datetime

import pandas as pd
import pytest

from src import previsional as P


@pytest.mark.parametrize('rotulo, esperado', [
    ('500.000,01 a 510.000,00', (500000.01, 510000.0, False)),
    ('428.633,20 (1)', (428633.2, 428633.2, True)),
    ('2.884.295,54 (4)', (2884295.54, 2884295.54, True)),
    ('26.000.000,01 y mas        ', (26000000.01, math.inf, False)),
    ('26.000.000,01 y más', (26000000.01, math.inf, False)),
    ('19.000.000,01 y 20.000.000,00', (19000000.01, 20000000.0, False)),  # errata del boletin: 'y' por 'a'
    ('Total', None),
])
def test_intervalo(rotulo, esperado):
    assert P._intervalo(rotulo) == esperado


def _intervalos():
    filas = [  # desde, hasta, puntual, total
        (0.01, 99.99, False, 5), (100, 100, True, 40), (100.01, 119.99, False, 2), (120, 120, True, 30),
        (120.01, 200, False, 10), (200.01, 300, False, 6), (300.01, 500, False, 4), (500.01, 600, False, 1),
        (600, 600, True, 1), (600.01, math.inf, False, 1)]
    return pd.DataFrame(filas, columns=['desde', 'hasta', 'puntual', 'total']).assign(mes='2026-09')


def test_puntos_y_tramos():
    iv = _intervalos()
    assert P.puntos(iv) == {'minimo': 100, 'minimo_con_bono': 120, 'maximo': 600}
    t = P.tramos(iv)
    assert list(t.index) == [n for n, _ in P.TRAMOS]
    assert t.loc['La mínima', 'total'] == 70          # minimo exacto + minimo con bono
    assert t.loc['Menos que la mínima', 'total'] == 5
    assert t.loc['Hasta 2 mínimas', 'total'] == 12     # entre minimo y minimo + bono, y hasta 200
    assert t.loc['Más de 5 mínimas', 'total'] == 3     # 500-600 (medio 550), el maximo y mas
    assert t['total'].sum() == iv['total'].sum()
    assert abs(t['total_pct'].sum() - 100) < 1e-9


def test_leer_regimenes_formato_bess():
    filas = [
        ('CUADRO 2.3.8 BENEFICIOS ... SEGÚN TIPO DE BENEFICIO Y RÉGIMEN. SEPTIEMBRE 2026', None),
        ('Régimen', 'TOTAL'),
        ('Total', 100, 1000.0, 10, 80, 800.0, 10, 20, 200.0, 10),
        ('GENERAL LEY N° 24.241', 'SIN MORATORIA', 'Beneficios ordinarios', 30, 450.0, 15, 20, 350, 17.5, 10, 100, 10),
        (None, None, 'Prestación Anticipada Decreto 674/21', 5, 50.0, 10, 5, 50.0, 10, 0, 0, '-'),
        (None, 'CON MORATORIA(2)', None, 60, 300.0, 5, 50, 250.0, 5, 10, 50.0, 5),
        ('ESPECIALES', 'PODER JUDICIAL(3)', None, 5, 200.0, 40, 5, 150.0, 30, 0, 50, 0),
        ('Notas:',),
        ('(1) Se incluye el refuerzo de ingreso previsional Decreto 824/2026.',),
    ]
    with pytest.raises(ValueError, match='faltan regimenes'):  # el formato real tiene todos los regimenes
        P.leer_regimenes({'2.3.8': filas})
    with pytest.raises(ValueError, match='regimen desconocido'):
        P.leer_regimenes({'2.3.8': filas + [('OTRO REGIMEN', 1, 1, 1, 1, 1, 1, 1, 1, 1)]})


def test_serie_toma_no_suspendidos():
    filas = [('CUADRO 2.3.1 ...',), ('Año',), (2018, 1, 2, 3), (2019, 1, 2, 3, 4, 5, 6),
             (datetime(2026, 9, 1), 7, 8, 9, 10, 11, 12)]
    s = P._serie(filas, 3)
    assert s == [('2018', 'promedio anual', [1, 2, 3]), ('2019', 'promedio anual', [4, 5, 6]),
                 ('2026-09', 'mes', [10, 11, 12])]


def test_mes_del_titulo():
    assert P._mes_del_titulo([('CUADRO 4.3.6 COBERTURA ... JUNIO 2025',)]) == '2025-06'
