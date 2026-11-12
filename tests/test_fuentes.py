"""Cache de descargas: vence para las fuentes mensuales y, sin red, usa la copia guardada (sin internet)."""
import os
import time

import pytest
import requests

from src import fuentes


class _Resp:
    def __init__(self, contenido: bytes):
        self.content = contenido
        self.headers = {'Content-Type': 'text/csv'}

    def raise_for_status(self):
        pass


def _envejecer(ruta, horas):
    t = time.time() - horas * 3600
    os.utime(ruta, (t, t))


def test_cache_vigente_no_baja(tmp_path, monkeypatch):
    ruta = tmp_path / 'serie.csv'
    ruta.write_bytes(b'vieja')
    monkeypatch.setattr(requests, 'get', lambda *a, **k: pytest.fail('no deberia bajar'))
    fuentes._bajar('http://x', ruta, vigencia_horas=12)
    assert ruta.read_bytes() == b'vieja'


def test_cache_vencida_se_vuelve_a_bajar(tmp_path, monkeypatch):
    ruta = tmp_path / 'serie.csv'
    ruta.write_bytes(b'vieja')
    _envejecer(ruta, 48)
    monkeypatch.setattr(requests, 'get', lambda *a, **k: _Resp(b'nueva'))
    fuentes._bajar('http://x', ruta, vigencia_horas=12)
    assert ruta.read_bytes() == b'nueva'


def test_sin_vigencia_no_vence(tmp_path, monkeypatch):
    ruta = tmp_path / 'engho.zip'
    ruta.write_bytes(b'fija')
    _envejecer(ruta, 24 * 365)
    monkeypatch.setattr(requests, 'get', lambda *a, **k: pytest.fail('no deberia bajar'))
    fuentes._bajar('http://x', ruta)
    assert ruta.read_bytes() == b'fija'


def test_sin_red_usa_copia_guardada(tmp_path, monkeypatch):
    ruta = tmp_path / 'serie.csv'
    ruta.write_bytes(b'vieja')
    _envejecer(ruta, 48)

    def falla(*a, **k):
        raise requests.ConnectionError('sin red')

    monkeypatch.setattr(requests, 'get', falla)
    fuentes._bajar('http://x', ruta, vigencia_horas=12)
    assert ruta.read_bytes() == b'vieja'
