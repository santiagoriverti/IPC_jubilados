"""Descarga y lectura de fuentes.

- INDEC: IPC por division COICOP (nacional y 6 regiones, dic-2016=100) y microdatos ENGHo 2017/18.
- datos.gob.ar: haber minimo jubilatorio (serie 58.1_MP_0_M_24).
- data/reference: bono previsional (no hay serie publica) y ponderaciones oficiales del IPC.
- Repo cuentas_publicas: IMIG (gasto en jubilaciones y pensiones) y AIF (resultados fiscales).

Todo lo descargado se guarda en data/cache/ (ignorado por git) para no repetir descargas.
"""
from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / 'data' / 'cache'
REFERENCIA = RAIZ / 'data' / 'reference'
PROCESADOS = RAIZ / 'data' / 'processed'
UA = {'User-Agent': 'Mozilla/5.0'}

URL_IPC_DIVISIONES = 'https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv'
URL_ENGHO = 'https://www.indec.gob.ar/ftp/cuadros/menusuperior/engho/engho2018_{tabla}.zip'
URL_SERIES = 'https://apis.datos.gob.ar/series/api/series/'
ID_HABER_MINIMO = '58.1_MP_0_M_24'
ID_PIB_NOMINAL = '4.4_OGP_2004_T_17'  # trimestral ANUALIZADO: anual = suma / 4
URL_CUENTAS = 'https://raw.githubusercontent.com/santiagoriverti/cuentas_publicas/main/output/{archivo}'

# Regiones: codigo ENGHo -> nombre en el IPC del INDEC
REGIONES_ENGHO = {1: 'GBA', 2: 'Pampeana', 3: 'Noroeste', 4: 'Noreste', 5: 'Cuyo', 6: 'Patagonia'}


def _bajar(url: str, destino: Path, refrescar: bool = False) -> Path:
    """Descarga url a destino salvo que ya exista (y no se pida refrescar)."""
    if destino.exists() and not refrescar:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    if 'text/html' in r.headers.get('Content-Type', ''):
        raise RuntimeError(f'La URL devolvio HTML en vez de datos: {url}')
    destino.write_bytes(r.content)
    return destino


def _a_numero(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(',', '.', regex=False), errors='coerce')


# --------------------------------------------------------------------------------------------
# IPC INDEC
# --------------------------------------------------------------------------------------------
def leer_ipc_divisiones(refrescar: bool = False) -> pd.DataFrame:
    """IPC por division, formato largo: periodo (Period M), region, codigo ('0' = nivel general,
    '01'..'12' = divisiones), descripcion, indice (dic-2016=100), var_mensual (en %)."""
    ruta = _bajar(URL_IPC_DIVISIONES, CACHE / 'serie_ipc_divisiones.csv', refrescar)
    d = pd.read_csv(ruta, sep=';', encoding='latin-1', dtype={'Codigo': str})
    d = d[d['Clasificador'] == 'Nivel general y divisiones COICOP'].copy()
    d['periodo'] = pd.PeriodIndex(d['Periodo'].astype(str).str[:4] + '-' + d['Periodo'].astype(str).str[4:],
                                  freq='M')
    out = pd.DataFrame({
        'periodo': d['periodo'],
        'region': d['Region'],
        'codigo': d['Codigo'].str.zfill(2).replace({'00': '0'}),
        'descripcion': d['Descripcion'],
        'indice': _a_numero(d['Indice_IPC']),
        'var_mensual': _a_numero(d['v_m_IPC']),
    })
    return out.reset_index(drop=True)


def matriz_indices(ipc: pd.DataFrame, region: str = 'Nacional') -> pd.DataFrame:
    """Matriz periodo x codigo ('0', '01'..'12') con los niveles del indice de una region."""
    m = ipc[ipc['region'] == region].pivot(index='periodo', columns='codigo', values='indice')
    return m.sort_index()[['0'] + [f'{i:02d}' for i in range(1, 13)]]


def matriz_var_publicada(ipc: pd.DataFrame, region: str = 'Nacional') -> pd.DataFrame:
    """Variaciones mensuales tal como las publica el INDEC (1 decimal), en fraccion.
    Solo se usan para replicar el calculo del TP original."""
    m = ipc[ipc['region'] == region].pivot(index='periodo', columns='codigo', values='var_mensual') / 100
    return m.sort_index()[['0'] + [f'{i:02d}' for i in range(1, 13)]]


# --------------------------------------------------------------------------------------------
# ENGHo 2017/18
# --------------------------------------------------------------------------------------------
def leer_engho(tabla: str, refrescar: bool = False, usecols=None) -> pd.DataFrame:
    """Tabla de microdatos ENGHo 2017/18: 'hogares', 'personas' o 'gastos'."""
    ruta = _bajar(URL_ENGHO.format(tabla=tabla), CACHE / f'engho2018_{tabla}.zip', refrescar)
    with zipfile.ZipFile(ruta) as z:
        nombre = [n for n in z.namelist() if n.lower().endswith('.txt')][0]
        with z.open(nombre) as f:
            return pd.read_csv(f, sep='|', encoding='latin-1', usecols=usecols)


# --------------------------------------------------------------------------------------------
# Haberes
# --------------------------------------------------------------------------------------------
def serie_datos_gob(serie_id: str, desde: str = '2016-12-01') -> pd.Series:
    r = requests.get(URL_SERIES, params={'ids': serie_id, 'format': 'csv', 'limit': 5000,
                                         'start_date': desde}, headers=UA, timeout=60)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    s = pd.Series(d.iloc[:, 1].values, index=pd.PeriodIndex(pd.to_datetime(d.iloc[:, 0]), freq='M'))
    return s.astype(float)


def leer_haber_minimo(refrescar: bool = False) -> pd.Series:
    """Haber minimo jubilatorio mensual (pesos corrientes, sin bono)."""
    ruta = CACHE / 'haber_minimo.csv'
    if refrescar or not ruta.exists():
        s = serie_datos_gob(ID_HABER_MINIMO)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        s.rename('haber_minimo').to_frame().to_csv(ruta, index_label='periodo')
    d = pd.read_csv(ruta)
    return pd.Series(d['haber_minimo'].values, index=pd.PeriodIndex(d['periodo'], freq='M'),
                     name='haber_minimo')


def leer_bono() -> pd.Series:
    """Bono/refuerzo previsional para quienes cobran el haber minimo (data/reference)."""
    d = pd.read_csv(REFERENCIA / 'bono_previsional.csv', comment='#')
    return pd.Series(d['bono'].values, index=pd.PeriodIndex(d['periodo'], freq='M'), name='bono')


def leer_pib_anual(refrescar: bool = False) -> pd.Series:
    """PIB nominal anual en millones de pesos (promedio de los trimestres anualizados)."""
    ruta = CACHE / 'pib_nominal_trim.csv'
    if refrescar or not ruta.exists():
        s = serie_datos_gob(ID_PIB_NOMINAL, desde='2016-01-01')
        ruta.parent.mkdir(parents=True, exist_ok=True)
        s.rename('pib').to_frame().to_csv(ruta, index_label='periodo')
    d = pd.read_csv(ruta)
    d['anio'] = d['periodo'].str[:4].astype(int)
    g = d.groupby('anio')['pib'].agg(['sum', 'count'])
    return (g.loc[g['count'] == 4, 'sum'] / 4).rename('pib_millones')


# --------------------------------------------------------------------------------------------
# Cuentas publicas (repo hermano)
# --------------------------------------------------------------------------------------------
def leer_cuentas_publicas(archivo: str, refrescar: bool = False) -> pd.DataFrame:
    """Lee imig_consolidado.csv o aif_consolidado.csv del repo cuentas_publicas.
    Orden: variable de entorno CUENTAS_PUBLICAS_DIR, repo hermano en disco, GitHub."""
    candidatos = []
    if os.environ.get('CUENTAS_PUBLICAS_DIR'):
        candidatos.append(Path(os.environ['CUENTAS_PUBLICAS_DIR']) / 'output' / archivo)
    candidatos.append(RAIZ.parent / 'cuentas_publicas' / 'output' / archivo)
    for c in candidatos:
        if c.exists() and not refrescar:
            return pd.read_csv(c, encoding='utf-8-sig')
    ruta = _bajar(URL_CUENTAS.format(archivo=archivo), CACHE / archivo, refrescar)
    return pd.read_csv(ruta, encoding='utf-8-sig')


IMIG_CONCEPTOS = {
    'Jubilaciones_pensiones': 'jub_contributivas',
    'Pensiones_no_contributivas': 'pnc',
    'Prestaciones_sociales': 'prestaciones_sociales',
    'GASTOS_PRIMARIOS': 'gasto_primario',
    'RESULTADO_PRIMARIO': 'resultado_primario',
    'RESULTADO_FINANCIERO': 'resultado_financiero',
}


def imig_mensual() -> pd.DataFrame:
    """Sector Publico Nacional base caja (IMIG de Hacienda, consolidada en cuentas_publicas),
    millones de $ corrientes: jubilaciones y pensiones contributivas, PNC, prestaciones sociales,
    gasto primario y resultados. Los meses de junio y diciembre incluyen el aguinaldo."""
    m = leer_cuentas_publicas('imig_consolidado.csv')
    m = m[m['concepto_codigo'].isin(IMIG_CONCEPTOS) & (m['nivel_jerarquia'] <= 2)]
    # Algunos conceptos cambian de descripcion entre archivos: quedarse con una fila por mes
    m = m.drop_duplicates(subset=['fecha', 'concepto_codigo'], keep='last')
    t = m.pivot(index='fecha', columns='concepto_codigo', values='valor_millones_pesos')
    t.index = pd.PeriodIndex(pd.to_datetime(t.index), freq='M')
    return t.rename(columns=IMIG_CONCEPTOS)[list(IMIG_CONCEPTOS.values())].sort_index()
