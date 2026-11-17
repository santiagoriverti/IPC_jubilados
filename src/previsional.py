"""Datos administrativos del sistema previsional: Boletin Estadistico de la Seguridad Social (BESS).

El BESS (Secretaria de Trabajo, Direccion Nacional de Politicas de la Seguridad Social, con datos de ANSES) es
trimestral y se publica en Excel por capitulo. Se usan tres:

- pasivos (cap. II, SIPA): beneficios, masa y haber medio por regimen (cuadro 2.3.8), beneficiarios titulares
  por intervalo de haber (2.2.6), beneficios por intervalo de haber y regimen (2.3.7), serie anual de
  beneficios y haber medio (2.3.5) y beneficios con y sin moratoria (2.3.1).
- pnc (cap. III): pensiones no contributivas (3.1 y 3.4) y PUAM (3.7).
- indicadores (cap. IV): cobertura de las personas de 60 a 90 anios (4.3.6).

El haber del BESS es bruto (antes de descontar las cuotas de la moratoria, el impuesto a las ganancias o la
obra social) e incluye el refuerzo (bono) desde septiembre de 2022. Un "beneficio" es una jubilacion o una
pension; un "beneficiario titular" es una persona, con todos sus beneficios del SIPA sumados (cuadro 2.2.6).
Solo cubre lo que administra ANSES: no las cajas provinciales, municipales y profesionales ni las fuerzas
armadas y de seguridad nacionales.

Las tablas leidas (bess_*.csv) se versionan en data/processed: si el BESS no se puede bajar (sin red, cambio
de URL) se usan esas copias con un aviso. Un cambio de formato de los cuadros da error (no se adivina).
"""
from __future__ import annotations

import math
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from . import fuentes

URL_PAGINA = 'https://www.argentina.gob.ar/trabajo/seguridadsocial/bess'
URL_ARCHIVO = 'https://www.argentina.gob.ar/sites/default/files/estadisticas_de_seguridad_social_{cap}_{edicion}.xlsx'
CAPITULOS = ('pasivos', 'pnc', 'indicadores')
CACHE_BESS = fuentes.CACHE / 'bess'
# La pagina del BESS cambia con cada edicion trimestral: se consulta de nuevo pasada esta vigencia
VIGENCIA_HORAS = 24 * 7
TABLAS = ('regimenes', 'intervalos_titulares', 'intervalos_regimen', 'serie_sipa', 'no_contributivas', 'cobertura')

# Regimenes del cuadro 2.3.8 (y columnas del 2.3.7): nombre en el BESS (sin acentos, minusculas) -> (nombre, grupo)
REGIMENES = [
    ('total', ('Total', 'total')),
    ('beneficios ordinarios', ('General sin moratoria', 'general')),
    ('prestacion anticipada', ('General sin moratoria', 'general')),
    ('con moratoria', ('General con moratoria', 'general')),
    ('leyes anteriores', ('Leyes anteriores a la 24.241', 'general')),
    ('docentes no universitarios', ('Docentes no universitarios', 'especial')),
    ('luz y fuerza', ('Luz y Fuerza', 'especial')),
    ('investigadores', ('Investigadores científicos', 'especial')),
    ('poder judicial', ('Poder Judicial', 'especial')),
    ('sin prestaciones de otro', ('Docentes universitarios', 'especial')),
    ('en simultaneidad', ('Docentes universitarios', 'especial')),
    ('en haber integrado', ('Docentes universitarios', 'especial')),
    ('servicio exterior', ('Servicio Exterior', 'especial')),
    ('rio turbio', ('Río Turbio', 'especial')),
    ('policia', ('Policías provinciales transferidas', 'retiro')),
]
ORDEN_REGIMENES = ['Total', 'General sin moratoria', 'General con moratoria', 'Leyes anteriores a la 24.241',
                   'Docentes no universitarios', 'Luz y Fuerza', 'Investigadores científicos', 'Poder Judicial',
                   'Docentes universitarios', 'Servicio Exterior', 'Río Turbio', 'Policías provinciales transferidas']
# Columnas del cuadro 2.3.7 (despues del total), en orden
COLS_INTERVALOS_REGIMEN = ['Leyes anteriores a la 24.241', 'General sin moratoria', 'General sin moratoria',
                           'General con moratoria', 'Docentes no universitarios', 'Luz y Fuerza',
                           'Investigadores científicos', 'Poder Judicial', 'Docentes universitarios',
                           'Docentes universitarios', 'Docentes universitarios', 'Servicio Exterior', 'Río Turbio',
                           'Policías provinciales transferidas']
# Columnas del cuadro 2.2.6 (despues del total): tipo de beneficio del titular
COLS_INTERVALOS_TITULARES = ['jubilacion_sin_moratoria'] * 3 + ['jubilacion_con_moratoria'] * 3 + ['solo_pension'] * 2
# Tramos de haber, en haberes minimos (limite superior incluido)
TRAMOS = [('Menos que la mínima', None), ('La mínima', None), ('Hasta 2 mínimas', 2.0), ('De 2 a 3 mínimas', 3.0),
          ('De 3 a 5 mínimas', 5.0), ('Más de 5 mínimas', math.inf)]
COLS_COBERTURA = ['jubilacion_sin_moratoria_o_especial', 'jubilacion_solo_moratoria', 'jubilacion_total',
                  'pension_y_jubilacion', 'solo_pension', 'pension_total', 'total_anses', 'pnc', 'puam',
                  'no_contributiva_total', 'otros_sistemas', 'total']
MESES_ES = {m: i + 1 for i, m in enumerate(['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
                                            'septiembre', 'octubre', 'noviembre', 'diciembre'])}


# --------------------------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------------------------
def _norm(s) -> str:
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().lower()


def ultima_edicion(refrescar: bool = False) -> str:
    """Edicion mas reciente del capitulo de pasivos ('09-2026'), leida de la pagina del BESS. Sin red, la ultima
    edicion bajada a data/cache/bess."""
    ruta = CACHE_BESS / 'pagina_bess.html'
    try:  # la pagina es HTML: fuentes._bajar la rechazaria
        if refrescar or not fuentes._vigente(ruta, VIGENCIA_HORAS):
            r = requests.get(URL_PAGINA, headers=fuentes.UA, timeout=60)
            r.raise_for_status()
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(r.text, encoding='utf-8')
    except requests.RequestException as e:
        print(f'ATENCION: no se pudo leer la pagina del BESS ({e})')
    ediciones = []
    if ruta.exists():
        ediciones = re.findall(r'estadisticas_de_seguridad_social_pasivos_(\d{2}-\d{4})\.xlsx', ruta.read_text('utf-8'))
    ediciones += [p.stem.rsplit('_', 1)[-1] for p in CACHE_BESS.glob('estadisticas_de_seguridad_social_pasivos_*.xlsx')]
    if not ediciones:
        raise RuntimeError(f'No se encontro ninguna edicion del BESS en {URL_PAGINA}')
    return max(set(ediciones), key=lambda e: (e[3:], e[:2]))


def archivo(cap: str, edicion: str, refrescar: bool = False) -> Path:
    """Excel de un capitulo del BESS (lo baja a data/cache/bess si no esta)."""
    nombre = Path(URL_ARCHIVO.format(cap=cap, edicion=edicion)).name
    return fuentes._bajar(URL_ARCHIVO.format(cap=cap, edicion=edicion), CACHE_BESS / nombre, refrescar)


def fuentes_originales() -> list[tuple]:
    """Entradas para exportar.FUENTES_ORIGINALES con los Excel de la ultima edicion bajada."""
    filas, ultima = [], ultima_edicion_bajada()
    for p in sorted(CACHE_BESS.glob('estadisticas_de_seguridad_social_*.xlsx')):
        cap, ed = p.stem.split('_')[-2:]
        if cap in CAPITULOS and ed == ultima:
            filas.append((f'BESS/{p.name}', URL_ARCHIVO.format(cap=cap, edicion=ed), p,
                          f'BESS (Secretaria de Trabajo, datos de ANSES), capitulo {cap}, datos a {ed}'))
    return filas


def ultima_edicion_bajada() -> str | None:
    eds = [p.stem.rsplit('_', 1)[-1] for p in CACHE_BESS.glob('estadisticas_de_seguridad_social_pasivos_*.xlsx')]
    return max(eds, key=lambda e: (e[3:], e[:2])) if eds else None


# --------------------------------------------------------------------------------------------
# Lectura de los cuadros
# --------------------------------------------------------------------------------------------
def _libro(ruta: Path) -> dict[str, list[tuple]]:
    """{titulo del cuadro ('2.3.8'): filas} de un Excel del BESS. El cuadro se identifica por el titulo
    'CUADRO x.y.z ...' de la hoja (no por el nombre de la hoja, que agrupa a veces varios cuadros)."""
    import openpyxl
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    out = {}
    for ws in wb.worksheets:
        filas = [tuple(r) for r in ws.iter_rows(values_only=True)]
        for f in filas[:8]:
            m = next((re.match(r'CUADRO (\d+(?:\.\d+)+)', str(v).strip()) for v in f if isinstance(v, str)
                      and str(v).strip().startswith('CUADRO')), None)
            if m:
                out.setdefault(m.group(1), filas)
                break
    wb.close()
    return out


def _cuadro(libro: dict, codigo: str) -> list[tuple]:
    if codigo not in libro:
        raise ValueError(f'BESS: no se encontro el cuadro {codigo} (cambio el formato del boletin)')
    return libro[codigo]


def _es_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _partir(fila: tuple) -> tuple[list[str], list]:
    """(rotulos de texto antes del primer numero, valores desde el primer numero; '-' = NaN, sin vacios)."""
    i = next((k for k, v in enumerate(fila) if _es_num(v)), None)
    if i is None:
        return [], []
    rot = [str(v).strip() for v in fila[:i] if isinstance(v, str) and str(v).strip()]
    vals = [float(v) if _es_num(v) else np.nan for v in fila[i:] if v is not None and str(v).strip() != '']
    return rot, vals


def _titulo(filas: list[tuple]) -> str:
    return next(str(v) for f in filas[:8] for v in f if isinstance(v, str) and v.strip().startswith('CUADRO'))


def _mes_del_titulo(filas: list[tuple]) -> str:
    """'2026-09' a partir de 'SEPTIEMBRE 2026' en el titulo del cuadro."""
    m = re.search(r'(' + '|'.join(MESES_ES) + r')\s+(\d{4})', _norm(_titulo(filas)))
    if not m:
        raise ValueError(f'BESS: no se encontro el mes en el titulo: {_titulo(filas)}')
    return f'{m.group(2)}-{MESES_ES[m.group(1)]:02d}'


def _regimen(rotulo: str) -> tuple[str, str]:
    r = _norm(rotulo)
    for clave, valor in REGIMENES:
        if clave in r:
            return valor
    raise ValueError(f'BESS: regimen desconocido en el cuadro 2.3.8: {rotulo!r}')


def leer_regimenes(libro: dict) -> pd.DataFrame:
    """Cuadro 2.3.8: beneficios, masa de haberes brutos (pesos) y haber medio por regimen, total, jubilaciones y
    pensiones (los docentes universitarios y la prestacion anticipada se suman a su regimen)."""
    filas = _cuadro(libro, '2.3.8')
    mes = _mes_del_titulo(filas)
    reg = []
    for f in filas:
        rot, v = _partir(f)
        if not rot or len(v) < 9 or _norm(rot[-1]).startswith('('):
            continue
        nombre, grupo = _regimen(rot[-1])
        reg.append({'regimen': nombre, 'grupo': grupo, 'beneficios': v[0], 'masa': v[1], 'jub_beneficios': v[3],
                    'jub_masa': v[4], 'pen_beneficios': v[6], 'pen_masa': v[7]})
    d = pd.DataFrame(reg).groupby(['regimen', 'grupo'], as_index=False, sort=False).sum()
    for pre in ('', 'jub_', 'pen_'):
        d[f'{pre}haber_medio'] = d[f'{pre}masa'] / d[f'{pre}beneficios'].replace(0, np.nan)
    d['mes'] = mes
    d = d.set_index('regimen').reindex(ORDEN_REGIMENES).reset_index()
    if d['beneficios'].isna().any():
        raise ValueError(f'BESS 2.3.8: faltan regimenes {d.loc[d["beneficios"].isna(), "regimen"].tolist()}')
    total = d.loc[d['regimen'] == 'Total', 'beneficios'].iloc[0]
    if abs(d.loc[d['regimen'] != 'Total', 'beneficios'].sum() - total) > 0.5:
        raise ValueError('BESS 2.3.8: los regimenes no suman el total')
    return d


_MONTO = r'\d{1,3}(?:\.\d{3})*,\d{2}'


def _intervalo(rotulo: str) -> tuple[float, float, bool] | None:
    """(desde, hasta, puntual) de un rotulo del BESS: '500.000,01 a 510.000,00', '428.633,20 (1)',
    '26.000.000,01 y mas'."""
    nums = [float(x.replace('.', '').replace(',', '.')) for x in re.findall(_MONTO, rotulo)]
    if len(nums) == 2:
        return nums[0], nums[1], False
    if len(nums) == 1 and re.search(r'\(\d\)', rotulo):
        return nums[0], nums[0], True
    if len(nums) == 1 and 'mas' in _norm(rotulo):
        return nums[0], math.inf, False
    return None


def _leer_intervalos(filas: list[tuple], columnas: list[str]) -> pd.DataFrame:
    out, total = [], None
    for f in filas:
        rot, v = _partir(f)
        if not rot:
            continue
        if _norm(rot[-1]) == 'total':
            total = v
            continue
        iv = _intervalo(rot[-1])
        if iv is None:
            continue
        if len(v) != len(columnas) + 1:
            raise ValueError(f'BESS: intervalo {rot[-1]!r} con {len(v)} columnas (se esperaban {len(columnas) + 1})')
        fila = {'desde': iv[0], 'hasta': iv[1], 'puntual': iv[2], 'total': v[0]}
        for c, x in zip(columnas, v[1:]):
            fila[c] = fila.get(c, 0.0) + x
        out.append(fila)
    d = pd.DataFrame(out)
    if total is None or abs(d['total'].sum() - total[0]) > 0.5:
        raise ValueError('BESS: los intervalos de haber no suman el total')
    d['mes'] = _mes_del_titulo(filas)
    return d


def leer_intervalos_titulares(libro: dict) -> pd.DataFrame:
    """Cuadro 2.2.6: beneficiarios titulares (personas) por intervalo de su haber total del SIPA."""
    return _leer_intervalos(_cuadro(libro, '2.2.6'), COLS_INTERVALOS_TITULARES)


def leer_intervalos_regimen(libro: dict) -> pd.DataFrame:
    """Cuadro 2.3.7: beneficios por intervalo de haber y regimen."""
    return _leer_intervalos(_cuadro(libro, '2.3.7'), COLS_INTERVALOS_REGIMEN)


def _periodo(v) -> tuple[str, str] | None:
    """('2025', 'promedio anual') o ('2026-09', 'mes') del rotulo de fila de una serie del BESS."""
    if isinstance(v, datetime):
        return f'{v.year}-{v.month:02d}', 'mes'
    if _es_num(v) and 1990 <= v <= 2100:
        return str(int(v)), 'promedio anual'
    if isinstance(v, str) and re.fullmatch(r'\s*(19|20)\d{2}\s*(\(\d\))?\s*', v):
        return v.strip()[:4], 'promedio anual'
    return None


def _serie(filas: list[tuple], n: int, ultimos: bool = True) -> list[tuple[str, str, list]]:
    """Filas (periodo, tipo, valores) de una serie: n valores, o 2n si hay un bloque de 'no suspendidos'
    (desde 2019), del que se toman los ultimos n."""
    out = []
    for f in filas:
        i = next((k for k, v in enumerate(f) if v is not None and str(v).strip() != ''), None)
        if i is None:
            continue
        p = _periodo(f[i])
        if p is None:
            continue
        v = [float(x) if _es_num(x) else np.nan for x in f[i + 1:] if x is not None and str(x).strip() != '']
        v = [x for x in v]
        if len(v) >= 2 * n and ultimos:
            v = v[n:2 * n]
        elif len(v) >= n:
            v = v[:n]
        else:
            continue
        out.append((p[0], p[1], v))
    return out


def leer_serie_sipa(libro: dict) -> pd.DataFrame:
    """Cuadros 2.3.5 y 2.3.1: beneficios (no suspendidos desde 2019), con y sin moratoria, y haber medio del SIPA
    por anio (promedio mensual) y el ultimo mes publicado."""
    s5 = _serie(_cuadro(libro, '2.3.5'), 6, ultimos=False)
    s1 = _serie(_cuadro(libro, '2.3.1'), 9)
    a = pd.DataFrame([(p, t, *v) for p, t, v in s5], columns=['periodo', 'tipo', 'beneficios', 'jub_beneficios',
                                                              'pen_beneficios', 'haber_medio', 'jub_haber_medio',
                                                              'pen_haber_medio'])
    b = pd.DataFrame([(p, *v) for p, _, v in s1], columns=[
        'periodo', 'beneficios_2', 'beneficios_con_moratoria', 'beneficios_sin_moratoria', 'jub_2',
        'jub_con_moratoria', 'jub_sin_moratoria', 'pen_2', 'pen_con_moratoria', 'pen_sin_moratoria'])
    d = a.merge(b, on='periodo', how='left').drop(columns=['beneficios_2', 'jub_2', 'pen_2'])
    return d.drop_duplicates('periodo', keep='last').reset_index(drop=True)


def leer_no_contributivas(libro: dict) -> pd.DataFrame:
    """Cuadros 3.1, 3.4 y 3.7: pensiones no contributivas (no suspendidas) por tipo y PUAM, con su haber medio."""
    tipos = ['PNC total', 'PNC asistenciales', 'PNC invalidez', 'PNC vejez', 'PNC madre de 7 hijos',
             'PNC leyes especiales', 'PNC graciables', 'PNC ex combatientes de Malvinas']
    ben = {p: v for p, _, v in _serie(_cuadro(libro, '3.1'), 8)}
    hab = {p: v for p, _, v in _serie(_cuadro(libro, '3.4'), 8, ultimos=False)}
    puam = {p: v for p, _, v in _serie(_cuadro(libro, '3.7'), 2)}
    filas = []
    for p in sorted(set(ben) | set(puam)):
        if p < '2020':
            continue
        for k, t in enumerate(tipos):
            if p in ben:
                filas.append({'periodo': p, 'prestacion': t, 'beneficios': ben[p][k],
                              'haber_medio': hab.get(p, [np.nan] * 8)[k]})
        if p in puam:
            filas.append({'periodo': p, 'prestacion': 'PUAM', 'beneficios': puam[p][0], 'haber_medio': puam[p][1]})
    return pd.DataFrame(filas)


def leer_cobertura(libro: dict) -> pd.DataFrame:
    """Cuadro 4.3.6: proporcion de la poblacion de cada edad (60 a 90) con cada tipo de beneficio (registros
    administrativos de ANSES sobre la poblacion proyectada)."""
    filas = _cuadro(libro, '4.3.6')
    mes = _mes_del_titulo(filas)
    out = []
    for f in filas:
        i = next((k for k, v in enumerate(f) if v is not None and str(v).strip() != ''), None)
        if i is None:
            continue
        rot = str(f[i]).strip()
        if not (re.fullmatch(r'Total \d+-\d+', rot) or (_es_num(f[i]) and 60 <= f[i] <= 90)):
            continue
        vals = [float(x) if _es_num(x) else 0.0 for x in (list(f[i + 1:i + 13]) + [None] * 12)[:12]]
        out.append({'edad': rot if isinstance(f[i], str) else str(int(f[i])), **dict(zip(COLS_COBERTURA, vals))})
    d = pd.DataFrame(out).drop_duplicates('edad').reset_index(drop=True)
    d['mes'] = mes
    return d


# --------------------------------------------------------------------------------------------
# Carga (BESS o copia en data/processed)
# --------------------------------------------------------------------------------------------
def leer_bess(refrescar: bool = False) -> dict[str, pd.DataFrame]:
    """Las tablas de TABLAS, leidas de la ultima edicion del BESS. Si no se puede bajar o leer, las copias de
    data/processed/bess_*.csv (con un aviso)."""
    try:
        ed = ultima_edicion(refrescar)
        lib = {}
        for cap in CAPITULOS:
            lib.update(_libro(archivo(cap, ed, refrescar)))
        T = {'regimenes': leer_regimenes(lib), 'intervalos_titulares': leer_intervalos_titulares(lib),
             'intervalos_regimen': leer_intervalos_regimen(lib), 'serie_sipa': leer_serie_sipa(lib),
             'no_contributivas': leer_no_contributivas(lib), 'cobertura': leer_cobertura(lib)}
        T['edicion'] = ed
        return T
    except Exception as e:  # noqa: BLE001 (sin red o cambio de formato: copia versionada)
        rutas = {t: fuentes.PROCESADOS / f'bess_{t}.csv' for t in TABLAS}
        if not all(r.exists() for r in rutas.values()):
            raise
        print(f'ATENCION: no se pudo leer el BESS ({type(e).__name__}: {e}); se usan las copias de data/processed')
        T = {t: pd.read_csv(r, dtype={'periodo': str, 'mes': str, 'edad': str}) for t, r in rutas.items()}
        if 'puntual' in T['intervalos_titulares']:
            for t in ('intervalos_titulares', 'intervalos_regimen'):
                T[t]['puntual'] = T[t]['puntual'].astype(bool)
        T['edicion'] = T['regimenes']['mes'].iloc[0][5:] + '-' + T['regimenes']['mes'].iloc[0][:4]
        return T


# --------------------------------------------------------------------------------------------
# Resultados
# --------------------------------------------------------------------------------------------
def puntos(iv: pd.DataFrame) -> dict[str, float]:
    """Haber minimo, minimo con bono y maximo del mes: los tres intervalos puntuales del BESS, en orden."""
    p = sorted(iv.loc[iv['puntual'], 'desde'].unique())
    if len(p) != 3:
        raise ValueError(f'BESS: se esperaban 3 haberes puntuales (minimo, minimo + bono, maximo) y hay {p}')
    return {'minimo': p[0], 'minimo_con_bono': p[1], 'maximo': p[2]}


def _tramo(fila, pt: dict) -> str:
    if fila['puntual'] and fila['desde'] in (pt['minimo'], pt['minimo_con_bono']):
        return 'La mínima'
    if fila['hasta'] < pt['minimo']:
        return 'Menos que la mínima'
    medio = fila['desde'] if math.isinf(fila['hasta']) else (fila['desde'] + fila['hasta']) / 2
    k = medio / pt['minimo']
    return next(n for n, tope in TRAMOS[2:] if k <= tope)


def tramos(iv: pd.DataFrame) -> pd.DataFrame:
    """Personas (o beneficios) por tramo de haber en haberes minimos: cantidad y % de cada columna. Los intervalos
    del BESS son de $10.000 a $1.000.000: cada uno va al tramo de su punto medio."""
    pt = puntos(iv)
    cols = [c for c in iv.columns if c not in ('desde', 'hasta', 'puntual', 'mes')]
    t = iv.assign(tramo=iv.apply(_tramo, axis=1, pt=pt)).groupby('tramo')[cols].sum()
    t = t.reindex([n for n, _ in TRAMOS]).fillna(0)
    pct = (t / t.sum() * 100).add_suffix('_pct')
    return pd.concat([t, pct], axis=1).rename_axis('tramo')


def resumen(T: dict) -> pd.DataFrame:
    """Cifras principales para el texto: indicador, valor, unidad."""
    reg = T['regimenes'].set_index('regimen')
    it = T['intervalos_titulares']
    ir = T['intervalos_regimen']
    pt = puntos(it)
    tr = tramos(it)
    s = T['serie_sipa'].set_index('periodo')
    u = s.index[-1]
    nc = T['no_contributivas']
    ult_nc = nc['periodo'].max()
    nc = nc[nc['periodo'] == ult_nc].set_index('prestacion')
    cob = T['cobertura'].set_index('edad')
    tot = reg.loc['Total']
    gral = reg.loc['General sin moratoria', 'haber_medio']
    en_minima = it.loc[it['puntual'] & it['desde'].isin([pt['minimo'], pt['minimo_con_bono']]), 'total'].sum()
    hasta_minima = it.loc[it['hasta'] <= pt['minimo_con_bono'], 'total'].sum()
    # mediana de los titulares: primer intervalo en que la acumulada pasa la mitad
    acum = it.sort_values(['desde', 'hasta'])['total'].cumsum()
    med = it.sort_values(['desde', 'hasta']).loc[acum >= it['total'].sum() / 2].iloc[0]
    filas = [
        ('mes', T['regimenes']['mes'].iloc[0], 'mes de los datos'),
        ('haber_minimo', pt['minimo'], '$'), ('haber_minimo_con_bono', pt['minimo_con_bono'], '$'),
        ('haber_maximo', pt['maximo'], '$'), ('haber_maximo_en_minimos', pt['maximo'] / pt['minimo'], 'mínimos'),
        ('beneficios_sipa', tot['beneficios'], 'beneficios'),
        ('jubilaciones_sipa', tot['jub_beneficios'], 'beneficios'),
        ('pensiones_sipa', tot['pen_beneficios'], 'beneficios'),
        ('titulares_sipa', it['total'].sum(), 'personas'),
        ('haber_medio_sipa', tot['haber_medio'], '$ (bruto, con bono)'),
        ('haber_medio_jubilaciones', tot['jub_haber_medio'], '$'),
        ('haber_medio_pensiones', tot['pen_haber_medio'], '$'),
        ('haber_medio_general_sin_moratoria', gral, '$'),
        ('haber_medio_general_con_moratoria', reg.loc['General con moratoria', 'haber_medio'], '$'),
        ('pct_beneficios_con_moratoria', reg.loc['General con moratoria', 'beneficios'] / tot['beneficios'] * 100, '%'),
        ('pct_jubilaciones_con_moratoria', reg.loc['General con moratoria', 'jub_beneficios'] / tot['jub_beneficios'] * 100, '%'),
        ('titulares_en_la_minima', en_minima, 'personas'),
        ('pct_titulares_en_la_minima', en_minima / it['total'].sum() * 100, '%'),
        ('pct_titulares_hasta_minima_con_bono', hasta_minima / it['total'].sum() * 100, '%'),
        ('pct_titulares_menos_que_minima', tr.loc['Menos que la mínima', 'total_pct'], '%'),
        ('pct_titulares_hasta_2_minimas', tr.loc[['Menos que la mínima', 'La mínima', 'Hasta 2 mínimas'],
                                                 'total_pct'].sum(), '%'),
        ('pct_titulares_mas_de_5_minimas', tr.loc['Más de 5 mínimas', 'total_pct'], '%'),
        ('titular_mediano_desde', med['desde'], '$ (intervalo de la mediana)'),
        ('titular_mediano_en_minimos', med['desde'] / pt['minimo'], 'mínimos'),
        ('pct_moratoria_en_la_minima',
         ir.loc[ir['puntual'] & ir['desde'].isin([pt['minimo'], pt['minimo_con_bono']]), 'General con moratoria'].sum()
         / ir['General con moratoria'].sum() * 100, '% de los beneficios con moratoria'),
        ('beneficios_regimenes_especiales', reg.loc[reg['grupo'] == 'especial', 'beneficios'].sum(), 'beneficios'),
        ('pct_beneficios_regimenes_especiales', reg.loc[reg['grupo'] == 'especial', 'beneficios'].sum()
         / tot['beneficios'] * 100, '%'),
        ('pct_masa_regimenes_especiales', reg.loc[reg['grupo'] == 'especial', 'masa'].sum() / tot['masa'] * 100, '%'),
        ('haber_medio_regimenes_especiales', reg.loc[reg['grupo'] == 'especial', 'masa'].sum()
         / reg.loc[reg['grupo'] == 'especial', 'beneficios'].sum(), '$'),
        ('beneficios_sobre_haber_maximo_especiales',
         ir.loc[ir['desde'] > pt['maximo'], [r for r in dict.fromkeys(COLS_INTERVALOS_REGIMEN)
                                             if reg.loc[r, 'grupo'] == 'especial']].sum().sum(), 'beneficios'),
        ('pnc', nc.loc['PNC total', 'beneficios'], f'beneficios ({ult_nc})'),
        ('pnc_invalidez', nc.loc['PNC invalidez', 'beneficios'], f'beneficios ({ult_nc})'),
        ('pnc_vejez', nc.loc['PNC vejez', 'beneficios'], f'beneficios ({ult_nc})'),
        ('pnc_haber_medio', nc.loc['PNC total', 'haber_medio'], f'$ ({ult_nc})'),
        ('puam', nc.loc['PUAM', 'beneficios'], f'beneficios ({ult_nc})'),
        ('puam_haber_medio', nc.loc['PUAM', 'haber_medio'], f'$ ({ult_nc})'),
        # Haber medio de todo lo que paga ANSES a jubilados y pensionados (SIPA + PNC + PUAM): rango para validar el
        # haber del "jubilado promedio" que se simula desde la ENGHo (por beneficio <= por persona)
        ('haber_medio_anses_por_beneficio',
         (tot['masa'] + (nc.loc[['PNC total', 'PUAM'], 'beneficios'] * nc.loc[['PNC total', 'PUAM'], 'haber_medio']).sum())
         / (tot['beneficios'] + nc.loc[['PNC total', 'PUAM'], 'beneficios'].sum()), '$ (SIPA + PNC + PUAM)'),
        ('haber_medio_anses_por_persona',
         (tot['masa'] + (nc.loc[['PNC total', 'PUAM'], 'beneficios'] * nc.loc[['PNC total', 'PUAM'], 'haber_medio']).sum())
         / (it['total'].sum() + nc.loc[['PNC total', 'PUAM'], 'beneficios'].sum()),
         '$ (titulares del SIPA + PNC + PUAM; cota superior: algunos cobran PNC y SIPA)'),
        ('cobertura_65_90', cob.loc['Total 65-90', 'total'] * 100, f'% ({T["cobertura"]["mes"].iloc[0]})'),
        ('cobertura_65_90_solo_moratoria', cob.loc['Total 65-90', 'jubilacion_solo_moratoria'] * 100, '%'),
        ('cobertura_65_90_otros_sistemas', cob.loc['Total 65-90', 'otros_sistemas'] * 100, '%'),
        ('cobertura_65_90_no_contributiva', cob.loc['Total 65-90', 'no_contributiva_total'] * 100, '%'),
        ('cobertura_60_90', cob.loc['Total 60-90', 'total'] * 100, '%'),
        ('serie_ultimo_periodo', u, ''),
    ]
    for r in ['Poder Judicial', 'Servicio Exterior', 'Docentes no universitarios', 'Investigadores científicos',
              'Docentes universitarios', 'Luz y Fuerza', 'Río Turbio']:
        filas.append((f'veces_general_{_norm(r).replace(" ", "_")}', reg.loc[r, 'haber_medio'] / gral,
                      'veces el haber medio general sin moratoria'))
        sobre = ir.loc[ir['desde'] > pt['maximo'], r].sum() / ir[r].sum() * 100
        filas.append((f'pct_sobre_maximo_{_norm(r).replace(" ", "_")}', sobre, '% de sus beneficios'))
    return pd.DataFrame(filas, columns=['indicador', 'valor', 'unidad'])


def haber_real(serie: pd.DataFrame, niveles: pd.DataFrame, base: str = '2017') -> pd.DataFrame:
    """Haber medio del SIPA en terminos reales (base = 100) con cada indice de `niveles` (IPC oficial, IIJP...).
    Los anios usan el promedio de los indices del anio (como el haber medio del BESS, promedio mensual); el ultimo
    mes publicado, el indice de ese mes. Solo periodos con indices completos (desde 2017)."""
    filas = []
    for _, f in serie.iterrows():
        p = f['periodo']
        if f['tipo'] == 'mes':
            idx = niveles.loc[pd.Period(p, 'M'):pd.Period(p, 'M')]
        else:
            idx = niveles.loc[pd.Period(f'{p}-01', 'M'):pd.Period(f'{p}-12', 'M')]
            if len(idx) < 12:
                continue
        if idx.empty:
            continue
        filas.append({'periodo': p, 'tipo': f['tipo'], 'haber_medio': f['haber_medio'], **idx.mean().to_dict()})
    d = pd.DataFrame(filas).set_index('periodo')
    cols = list(niveles.columns)
    b = d.loc[base]
    for c in cols:
        d[f'real_{c}'] = d['haber_medio'] / d[c] / (b['haber_medio'] / b[c]) * 100
    return d.drop(columns=cols).reset_index()


def calcular(niveles: pd.DataFrame, refrescar: bool = False) -> dict:
    """Todo lo del BESS para R['previsional']: tablas leidas, tramos, resumen y haber medio real."""
    T = leer_bess(refrescar)
    out = {t: T[t] for t in TABLAS}
    out['edicion'] = T['edicion']
    out['tramos_titulares'] = tramos(T['intervalos_titulares'])
    out['tramos_regimen'] = tramos(T['intervalos_regimen'])
    out['resumen'] = resumen(T)
    out['haber_real'] = haber_real(T['serie_sipa'], niveles[['IPC oficial', 'IIJP']])
    return out
