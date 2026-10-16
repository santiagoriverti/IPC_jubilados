"""Exportacion de resultados: CSV (datos), Excel y graficos PNG.

- `exportar(R, dir_salida, dir_datos)`: escribe IIJP_resultados.xlsx, graficos/ (analisis) y figuras/
  (documento de prensa y presentacion, mismos nombres que en los .tex de docs/divulgacion) en
  dir_salida y los CSV en dir_datos. scripts/construir.py lo usa con output/ y data/processed/
  (versionados).
- `zip_resultados(R, nombre)`: lo que llaman los notebooks al final. Exporta todo a
  _descargas/<nombre>/ (ignorado por git, no toca los archivos versionados) y lo comprime en
  _descargas/<nombre>.zip.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import fuentes, graficos

DESCARGAS = fuentes.RAIZ / '_descargas'


def _sin_period(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.index, pd.PeriodIndex):
        df.index = df.index.astype(str)
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    return df


def tablas_csv(R: dict) -> dict[str, tuple[pd.DataFrame, bool]]:
    """{archivo: (tabla, escribir_indice)}"""
    t = {
        'indices_niveles.csv': (R['niveles'], True),
        'indices_var_mensual.csv': (R['var_mensual'], True),
        'indices_regionales.csv': (R['niveles_regionales'], True),
        'brecha_periodos.csv': (R['periodos'], False),
        'brecha_regiones.csv': (R['periodos_regionales'], False),
        'brecha_estadistica.csv': (R['brecha_estadistica'], False),
        'ponderaciones.csv': (R['ponderaciones'], True),
        'ponderaciones_aperturas.csv': (R['ponderaciones_aperturas'], True),
        'ponderaciones_nodos.csv': (R['ponderaciones_nodos'], True),
        'ponderaciones_democraticas.csv': (R['ponderaciones_democraticas'], True),
        'poblaciones.csv': (R['poblaciones'], False),
        'estructura_nodos.csv': (R['estructura'], False),
        'indices_residuales.csv': (R['indices_residuales'], True),
        'variantes.csv': (R['variantes'], False),
        'variantes_resumen.csv': (R['variantes_resumen'], True),
        'variantes_niveles.csv': (R['variantes_niveles'], True),
        'haberes.csv': (R['haberes'], True),
        'fiscal_mensual.csv': (R['fiscal_mensual'], True),
        'fiscal_anual.csv': (R['fiscal_anual'], True),
        'validacion.csv': (R['validacion'], True),
        'cobertura_precios.csv': (R['cobertura_precios'], True),
        'sensibilidad_haber_minimo.csv': (R['sensibilidad_haber_minimo'], False),
        'revision_tp_periodos.csv': (R['revision_tp']['periodos'], False),
    }
    for k, d in R['descomposicion'].items():
        t[f'descomposicion_{k}.csv'] = (d, True)
    for k, d in R['descomposicion_aperturas'].items():
        t[f'descomposicion_aperturas_{k}.csv'] = (d, True)
    if 'bootstrap_brechas' in R:
        t['bootstrap_brechas.csv'] = (R['bootstrap_brechas'], False)
        t['bootstrap_ponderaciones.csv'] = (R['bootstrap_ponderaciones'], True)
    return t


def hojas_excel(R: dict) -> dict[str, pd.DataFrame]:
    h = {
        'Indices_niveles': R['niveles'],
        'Var_mensual_%': R['var_mensual'],
        'Var_interanual_%': R['var_interanual'],
        'Brecha_periodos': R['periodos'],
        'Brecha_estadistica': R['brecha_estadistica'],
        'Indices_regionales': R['niveles_regionales'],
        'Brecha_regiones': R['periodos_regionales'],
        'Peso_regiones': R['peso_regiones'],
        'Ponderaciones': R['ponderaciones'],
        'Pond_aperturas': R['ponderaciones_aperturas'],
        'Pond_nodos': R['ponderaciones_nodos'],
        'Pond_democraticas': R['ponderaciones_democraticas'],
        'Poblaciones': R['poblaciones'],
        'Descomp_nov23': R['descomposicion']['nov23_ultimo'],
        'Descomp_dic16': R['descomposicion']['dic16_ultimo'],
        'Descomp_aperturas_nov23': R['descomposicion_aperturas']['nov23_ultimo'],
        'Descomp_aperturas_dic16': R['descomposicion_aperturas']['dic16_ultimo'],
        'Pond_efectiva_IIJP': R['pond_efectiva_iijp'],
        'Variantes': R['variantes'],
        'Variantes_resumen': R['variantes_resumen'],
        'Variantes_niveles': R['variantes_niveles'],
        'Sensibilidad_haber_minimo': R['sensibilidad_haber_minimo'],
        'Cobertura_precios': R['cobertura_precios'],
        'Haberes': R['haberes'],
        'Regla_movilidad': R['regla_movilidad'],
        'Fiscal_mensual': R['fiscal_mensual'],
        'Fiscal_anual': R['fiscal_anual'],
        'Desvio_permanente': R['fiscal_desvio_permanente'],
        'Validacion_IPC': R['validacion'],
        'Estructura_nodos': R['estructura'],
        'Indices_residuales': R['indices_residuales'],
        'Sensibilidad_restos': R['sensibilidad_restos'],
        'Imputaciones': R['imputaciones'],
        'Revision_TP_pond': R['revision_tp']['ponderaciones'],
        'Revision_TP_periodos': R['revision_tp']['periodos'],
    }
    if 'bootstrap_brechas' in R:
        h['Bootstrap_brechas'] = R['bootstrap_brechas']
        h['Bootstrap_pond'] = R['bootstrap_ponderaciones']
    return h


def version_repo() -> str:
    """Commit del repo con que se genero la salida (para saber si un ZIP es de una version vieja)."""
    try:
        r = subprocess.run(['git', '-C', str(fuentes.RAIZ), 'log', '-1', '--format=%h (%ad)', '--date=short'],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or 'desconocida'
    except (OSError, subprocess.SubprocessError):
        return 'desconocida'


def notas(R: dict) -> list[str]:
    m = R['meta']
    return [
        'IIJP: Indice de precios de Jubilados y Pensionados. Canasta fija (Lowe) de los hogares jubilados de la '
        'ENGHo 2017/18, valorizada con el IPC del INDEC por aperturas en cada region.',
        f'Version del codigo (commit): {version_repo()}',
        f'Ultimo IPC: {m["ultimo_ipc"]} | ultimo haber: {m["ultimo_haber"]} | ultima IMIG: {m["ultimo_imig"]}'
        f' | replicas bootstrap: {m["n_bootstrap"]}',
        f'Estructura de precios: {m["nodos"]} nodos en 6 regiones ({m["restos_derivados"]} restos derivados de las '
        'ponderaciones oficiales del INDEC). Hoja Estructura_nodos.',
        'Niveles base dic-2016 = 100. Variaciones en %. Brechas: (1 + infl. A) / (1 + infl. B) - 1, en %.',
        'Efecto edad: IIJP contra el mismo calculo con todos los hogares (IPC ENGHo 17/18). Hoja Variantes: '
        'cada fila cambia una sola decision metodologica.',
        'Montos fiscales en millones de pesos corrientes. Metodologia: README y docs/ del repo '
        'github.com/santiagoriverti/IPC_jubilados.',
    ]


def exportar(R: dict, dir_salida: Path, dir_datos: Path) -> None:
    dir_salida, dir_datos = Path(dir_salida), Path(dir_datos)
    dir_datos.mkdir(parents=True, exist_ok=True)
    for carpeta in ('graficos', 'figuras'):
        (dir_salida / carpeta).mkdir(parents=True, exist_ok=True)

    for archivo, (df, con_indice) in tablas_csv(R).items():
        _sin_period(df).to_csv(dir_datos / archivo, index=con_indice, float_format='%.6f', lineterminator='\n')

    with pd.ExcelWriter(dir_salida / 'IIJP_resultados.xlsx', engine='openpyxl') as xw:
        pd.DataFrame({'nota': notas(R)}).to_excel(xw, sheet_name='Notas', index=False)
        for nombre, df in hojas_excel(R).items():
            _sin_period(df).to_excel(xw, sheet_name=nombre[:31])

    for carpeta, dic in (('graficos', graficos.GRAFICOS), ('figuras', graficos.GRAFICOS_DIVULGACION)):
        for nombre, f in dic.items():
            fig = f(R)
            fig.savefig(dir_salida / carpeta / f'{nombre}.png')
            plt.close(fig)


# --------------------------------------------------------------------------------------------
# Excel completo: resultados + datos originales (lo descarga el notebook 03)
# --------------------------------------------------------------------------------------------
# Columnas de los microdatos de la ENGHo 2017/18 que usa el analisis (las bases completas tienen 134, 158
# y 19 columnas; se bajan de URL_ENGHO)
COLS_ENGHO = {
    'hogares': ['id', 'provincia', 'region', 'subregion', 'trimestre', 'anio', 'pondera', 'cantmiem', 'mayor65',
                'ingtoth', 'ingpch', 'gastot'] + [f'gc_{i:02d}' for i in range(1, 13)],
    'personas': ['id', 'miembro', 'pondera', 'cp03', 'cp04', 'ijubilacion', 'ipensionesnc'],
    'gastos': ['id', 'articulo', 'clase', 'grupo', 'division', 'monto'],
}


def datos_originales() -> dict[str, tuple[pd.DataFrame, str]]:
    """{hoja: (tabla, descripcion)} con los datos de entrada del analisis, tal como los lee src/fuentes.py
    (usa data/cache: llamarla despues de pipeline.calcular)."""
    def per(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['periodo'] = df['periodo'].astype(str)
        return df

    def serie(s: pd.Series, nombre: str) -> pd.DataFrame:
        return pd.DataFrame({'periodo': s.index.astype(str), nombre: s.values})

    pondn = pd.read_csv(fuentes.REFERENCIA / 'ponderaciones_ipc_indec.csv', comment='#', dtype={'codigo': str})
    pib_trim = fuentes.CACHE / 'pib_nominal_trim.csv'
    imig = fuentes.imig_mensual()
    imig.index = imig.index.astype(str)
    d = {
        'IPC_divisiones': (per(fuentes.leer_ipc_divisiones()),
                           'INDEC, IPC por division COICOP, nacional y 6 regiones (dic-2016=100; var. mensual en %). '
                           + fuentes.URL_IPC_DIVISIONES),
        'IPC_aperturas': (per(fuentes.leer_ipc_aperturas()),
                          'INDEC, IPC por aperturas (divisiones, grupos y clases) de las 6 regiones (dic-2016=100). '
                          + fuentes.URL_IPC_APERTURAS),
        'Pond_IPC_regiones_0405': (fuentes.leer_ponderadores_ipc().reset_index(),
                                   'INDEC, ponderaciones del IPC por region (fraccion del gasto de la region): '
                                   'canasta de la ENGHo 2004/05 actualizada por precios a dic-2016. ponderadores_ipc.xls'),
        'Pond_IPC_nacional_0405': (pondn, 'INDEC, ponderaciones del IPC nacional por division (en %): ENGHo 2004/05. '
                                          'Metodologia del IPC 2019'),
        'Peso_regiones_IPC': (pd.Series(fuentes.POND_REGIONES, name='ponderacion').rename_axis('region').reset_index(),
                              'INDEC, peso de cada region en el IPC nacional (Metodologia del IPC 2019, cuadro 6)'),
    }
    for t, cols in COLS_ENGHO.items():
        d[f'ENGHo1718_{t}'] = (fuentes.leer_engho(t, usecols=cols),
                               f'INDEC, microdatos de la ENGHo 2017/18, base de {t} (columnas que usa el analisis; '
                               f'montos en pesos corrientes de la entrevista). ' + fuentes.URL_ENGHO.format(tabla=t))
    d['Haber_minimo'] = (serie(fuentes.leer_haber_minimo(), 'haber_minimo'),
                         f'datos.gob.ar, haber minimo jubilatorio en pesos corrientes, sin bono (serie {fuentes.ID_HABER_MINIMO})')
    d['Bono_previsional'] = (serie(fuentes.leer_bono(), 'bono'),
                             'Bono previsional para la jubilacion minima (pesos por mes), cargado a mano de los decretos '
                             '(data/reference/bono_previsional.csv)')
    d['IMIG'] = (imig.reset_index(names='periodo'),
                 'Secretaria de Hacienda, IMIG del Sector Publico Nacional base caja, millones de pesos corrientes '
                 '(repo cuentas_publicas). Junio y diciembre incluyen aguinaldo')
    if pib_trim.exists():
        d['PIB_trimestral'] = (pd.read_csv(pib_trim),
                               f'datos.gob.ar, PIB a precios corrientes, millones de pesos, trimestral anualizado '
                               f'(serie {fuentes.ID_PIB_NOMINAL})')
    d['PIB_anual'] = (fuentes.leer_pib_anual().rename_axis('anio').reset_index(),
                      'PIB anual a precios corrientes, millones de pesos (promedio de los 4 trimestres anualizados)')
    d['TP_original_series'] = (pd.read_csv(fuentes.REFERENCIA / 'tp_original_series.csv', comment='#'),
                               'Series del TP original (planilla de los alumnos, hoja Canasta): solo para la revision')
    return d


def excel_completo(R: dict, nombre: str) -> str:
    """Un solo Excel con todos los resultados (hojas de hojas_excel) y los datos originales (hojas Dato_*),
    con una hoja Indice que describe cada una. Escribe _descargas/<nombre>.xlsx y devuelve la ruta."""
    DESCARGAS.mkdir(parents=True, exist_ok=True)
    ruta = DESCARGAS / f'{nombre}.xlsx'
    res = hojas_excel(R)
    orig = {f'Dato_{k}': v for k, v in datos_originales().items()}
    filas = [{'hoja': k[:31], 'tipo': 'resultado', 'filas': len(v), 'descripcion': ''} for k, v in res.items()]
    filas += [{'hoja': k[:31], 'tipo': 'dato original', 'filas': len(df), 'descripcion': desc}
              for k, (df, desc) in orig.items()]
    indice = pd.DataFrame(filas)
    if indice['hoja'].duplicated().any():
        raise ValueError(f'Hojas repetidas: {indice.loc[indice["hoja"].duplicated(), "hoja"].tolist()}')
    with pd.ExcelWriter(ruta, engine='openpyxl') as xw:
        pd.DataFrame({'nota': notas(R) + [
            'Este archivo trae todos los resultados y, en las hojas Dato_*, los datos originales que usa el analisis. '
            'La hoja Indice describe cada hoja y su fuente.',
            'ENGHo 2004/05: el INDEC no la usa como microdatos sino a traves de las ponderaciones del IPC oficial '
            '(hojas Dato_Pond_IPC_*).']}).to_excel(xw, sheet_name='Notas', index=False)
        indice.to_excel(xw, sheet_name='Indice', index=False)
        for k, df in res.items():
            _sin_period(df).to_excel(xw, sheet_name=k[:31])
        for k, (df, _) in orig.items():
            df.to_excel(xw, sheet_name=k[:31], index=False)
    return str(ruta)


def zip_resultados(R: dict, nombre: str) -> str:
    """Exporta Excel, graficos, figuras y CSV a _descargas/<nombre>/ y devuelve la ruta del ZIP."""
    carpeta = DESCARGAS / nombre
    if carpeta.exists():
        shutil.rmtree(carpeta)
    exportar(R, carpeta, carpeta / 'datos')
    (carpeta / 'LEEME.txt').write_text(
        '\n'.join(notas(R) + ['', 'Contenido:', '  IIJP_resultados.xlsx  todas las tablas (una hoja por tabla)',
                              '  graficos/             graficos del analisis en PNG',
                              '  figuras/              figuras del documento de prensa y de la presentacion '
                              '(docs/divulgacion): subir tal cual a la carpeta "figuras" de Overleaf',
                              '  datos/                las mismas tablas en CSV']) + '\n',
        encoding='utf-8')
    return shutil.make_archive(str(carpeta), 'zip', carpeta)
