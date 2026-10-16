"""Genera los notebooks de notebooks/ (no editarlos a mano: editar este script y regenerar).

Uso:  python scripts/gen_notebooks.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

SETUP = r'''# Configuracion: en Colab clona (o actualiza) el repo; en local usa la carpeta del repo
import os, sys, subprocess, importlib
REPO = 'https://github.com/santiagoriverti/IPC_jubilados.git'
if 'google.colab' in sys.modules:
    RAIZ = '/content/IPC_jubilados'
    if os.path.exists(RAIZ):
        # Trae la ultima version de GitHub y descarta cambios locales (la copia de Colab es descartable)
        subprocess.run(['git', '-C', RAIZ, 'fetch', '-q', '--depth', '1', 'origin', 'main'], check=True)
        subprocess.run(['git', '-C', RAIZ, 'reset', '-q', '--hard', 'FETCH_HEAD'], check=True)
    else:
        subprocess.run(['git', 'clone', '-q', '--depth', '1', REPO, RAIZ], check=True)
else:  # subir desde la carpeta actual hasta encontrar el repo
    RAIZ = os.getcwd()
    while not os.path.exists(os.path.join(RAIZ, 'src', 'pipeline.py')) and os.path.dirname(RAIZ) != RAIZ:
        RAIZ = os.path.dirname(RAIZ)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
# Si el notebook ya se corrio en esta sesion, olvidar los modulos de src cargados (pueden ser viejos)
for m in [m for m in sys.modules if m == 'src' or m.startswith('src.')]:
    del sys.modules[m]
importlib.invalidate_caches()
v = subprocess.run(['git', '-C', RAIZ, 'log', '-1', '--format=%h (%ad) %s', '--date=short'],
                   capture_output=True, text=True).stdout.strip()
print('Version del repo:', v or 'sin git')

import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from src import pipeline, graficos, indices, ponderaciones as pond
pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
pd.set_option('display.max_columns', 30)'''


def md(texto: str) -> dict:
    return {'cell_type': 'markdown', 'metadata': {}, 'source': texto.strip('\n').splitlines(keepends=True)}


def code(texto: str) -> dict:
    return {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [],
            'source': texto.strip('\n').splitlines(keepends=True)}


def figuras_divulgacion(nombres: list[str]) -> list[dict]:
    """Celdas que muestran las figuras del documento de prensa y la presentacion (docs/divulgacion)."""
    return [
        md(r'''
## Figuras para el documento de prensa y la presentación

Versiones simplificadas para público no técnico, las que usan `docs/divulgacion/iijp_prensa.tex` y
`docs/divulgacion/iijp_presentacion.tex`. El ZIP de **cualquiera** de los tres notebooks trae las 6 en la
carpeta `figuras/`, con los nombres que esperan los `.tex`: se sube tal cual a la carpeta `figuras` de
Overleaf.
'''),
        code('\n'.join(f'fig = graficos.{n}(R); plt.show()' for n in nombres)),
    ]


def descarga(nombre: str, fuentes_originales: bool = False) -> list[dict]:
    """Celdas finales comunes: exportan todo y, en Colab, descargan el ZIP. Con fuentes_originales el ZIP
    trae ademas la carpeta fuentes_originales/ (notebook 03)."""
    extra = r'''
La carpeta `fuentes_originales/` trae los datos de entrada **tal como se publican**: CSV del IPC, Excel
de ponderaciones, microdatos de la ENGHo 2017/18 (ZIP) y su manual, metodología del IPC (PDF), haber
mínimo, PIB e IMIG de datos.gob.ar, y lo que se cargó a mano (bono). Su `LEEME.txt` da la URL de cada
archivo.
''' if fuentes_originales else ''
    arg = ', fuentes_originales=True' if fuentes_originales else ''
    return [
        md(r'''
## Descargar todos los resultados

ZIP con el Excel (una hoja por tabla), los gráficos del análisis en PNG (`graficos/`), las figuras del
documento de prensa y de la presentación (`figuras/`, para subir a Overleaf) y las tablas en CSV
(`datos/`). En Colab se descarga solo; en la PC queda en la carpeta `_descargas/` del repo.
''' + extra),
        code(f'''from src.exportar import zip_resultados
zip_path = zip_resultados(R, '{nombre}'{arg})
print('ZIP:', zip_path)
if 'google.colab' in sys.modules:
    from google.colab import files
    files.download(zip_path)'''),
    ]


def guardar(nombre: str, celdas: list[dict]) -> None:
    nb = {'cells': celdas, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'}, 'colab': {'provenance': []}},
        'nbformat': 4, 'nbformat_minor': 5}
    ruta = RAIZ / 'notebooks' / nombre
    ruta.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('escrito', ruta.relative_to(RAIZ))


# ------------------------------------------------------------------------------------------------
NB01 = [
    md(r'''
# 01 · La canasta de los jubilados (ENGHo 2017/18)

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/IPC_jubilados/blob/main/notebooks/01_canasta_jubilados.ipynb)

Ponderaciones del IIJP a partir de los **microdatos** de la Encuesta Nacional de Gastos de los Hogares
2017/18 (INDEC): el gasto de cada hogar en cada artículo (archivo de gastos) se asigna al índice de
precios del INDEC con que se valoriza (ver notebook 02).

- **Población de referencia**: hogares jubilados (jubilaciones y pensiones, contributivas y no
  contributivas, ≥ 50% del ingreso del hogar).
- **Subíndice haber mínimo**: hogares jubilados en los que ningún perceptor cobra más de 1,1 haberes
  mínimos (el vigente en el trimestre de la entrevista).
- **Comparador**: todos los hogares de la misma encuesta, y el IPC oficial (ENGHo 2004/05).
- Incertidumbre muestral de las ponderaciones (bootstrap de hogares).
'''),
    code(SETUP),
    code(r'''N_BOOTSTRAP = 300   # replicas para los intervalos de confianza (0 = no calcular)
R = pipeline.calcular(n_bootstrap=N_BOOTSTRAP)
PRINC = ['ipc_oficial', 'total', 'jubilados', 'jub_minimo']'''),
    md(r'''
## Poblaciones

Hogares en la muestra y expandidos (factor `pondera`). Rol: `principal` (IIJP), `subindice`,
`comparador`, `variante` (definiciones alternativas para la tabla de sensibilidad del notebook 02) y
`tp` (solo para la revisión del TP original).
'''),
    code(r'''display(R['poblaciones'])'''),
    md(r'''
## Ponderaciones por división (en %)

`ipc_oficial`: IPC nacional del INDEC (ENGHo 2004/05). `total`: todos los hogares con la ENGHo 2017/18
(lo que sería un IPC con canasta actualizada). `jubilados`: canasta del IIJP. `jub_minimo`: subíndice
haber mínimo. Las demás columnas son las definiciones alternativas de la población.
'''),
    code(r'''W = R['ponderaciones'].set_index('division')
display((W[PRINC] * 100).round(1))
fig = graficos.g01_ponderaciones(R); plt.show()'''),
    code(r'''display((W.drop(columns=PRINC) * 100).round(1))'''),
    md(r'''
## Composición dentro de las divisiones

El IPC no solo pondera distinto las divisiones: dentro de cada una, los jubilados compran cosas
distintas (medicamentos vs prepagas, alquiler vs servicios, transporte público vs vehículo propio), y
esos rubros tuvieron variaciones de precios muy distintas. Por eso el IIJP se valoriza al nivel más
desagregado que publica el INDEC. Participación de cada apertura en el gasto de su división (%),
nacional (suma de las 6 regiones). Los nodos `.r` son la parte de la división sin índice propio publicado.
'''),
    code(r'''A = R['ponderaciones_aperturas']
cols = [f'{c}_en_division' for c in PRINC]
for d in ['04', '06', '07', '05', '09']:
    t = A[A['division'] == d][['descripcion'] + cols].copy()
    t[cols] = t[cols] * 100
    display(Markdown(f'**{pond.DIVISIONES[d]}**'))
    display(t.round(1))'''),
    md(r'''
## Peso de cada región

El IIJP nacional suma las canastas de las 6 regiones: cada región pesa según el gasto de sus hogares
jubilados (en el IPC oficial, según el gasto de todos sus hogares en 2004/05).
'''),
    code(r'''display(R['peso_regiones'].style.format({'ipc_oficial': '{:.1%}', 'jubilados': '{:.1%}', 'total': '{:.1%}'}))'''),
    md(r'''
## Sensibilidad del subíndice haber mínimo al tope

El subíndice toma los hogares jubilados en los que ningún perceptor cobra más de 1,1 haberes mínimos.
Con otros topes cambia la cantidad de hogares; la tabla muestra cuánto cambia la brecha con el IPC y con
el IIJP.
'''),
    code(r'''display(R['sensibilidad_haber_minimo'])'''),
    md(r'''
## Incertidumbre muestral

Intervalos de 95% por bootstrap: remuestreo de hogares estratificado por región. La ENGHo pública no
trae las unidades primarias de muestreo, así que no se pueden remuestrear conglomerados: los intervalos
son una cota inferior del error muestral.
'''),
    code(r'''if 'bootstrap_ponderaciones' in R:
    b = R['bootstrap_ponderaciones'] * 100
    b.index = [pond.DIVISIONES_CORTO[c] for c in b.index]
    display(b.round(1))'''),
    md(r'''
## Sensibilidad: ponderaciones "democráticas"

El IPC usa ponderaciones plutocráticas (cada hogar pesa según cuánto gasta). Promediar las estructuras
de cada hogar (democráticas) da más peso a los hogares de menores ingresos.
'''),
    code(r'''D = R['ponderaciones_democraticas'].set_index('division')
display((D * 100).round(1))'''),
    *figuras_divulgacion(['iijp_01_canasta']),
    *descarga('IIJP_01_canasta_jubilados'),
]

# ------------------------------------------------------------------------------------------------
NB02 = [
    md(r'''
# 02 · IIJP vs IPC: método, validación y resultados

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/IPC_jubilados/blob/main/notebooks/02_iijp_vs_ipc.ipynb)

**Método.** Índice de canasta fija (Lowe), el mismo concepto que el IPC: las cantidades que compraban
los hogares jubilados en 2017/18 se valorizan cada mes con los precios del INDEC.

- **Precios por región y por apertura**: el IPC se calcula en 6 regiones y se publica, en cada una, por
  división, grupo y algunas clases. El IIJP valoriza cada gasto con el índice más específico publicado.
- **Restos**: la parte de cada agregado sin índice propio publicado (p. ej. agua dentro de Vivienda) se
  valoriza con un índice deducido de la estructura oficial de ponderaciones del INDEC (agregación de
  Laspeyres). Si esa parte pesa menos de 0,2% de la región, usa el índice del agregado.
- **Concordancia**: la clasificación de gastos de la ENGHo se lleva a la del IPC (p. ej. las expensas, que
  la ENGHo registra junto al agua y el IPC como gastos comunes de la vivienda).
- **Precios de referencia**: promedio del relevamiento (nov-2017 a nov-2018). Es decir, las ponderaciones
  se actualizan por precios relativos, como recomienda el Manual del IPC (OIT/FMI) y hace el INDEC.
- **Nacional**: suma de las 6 canastas regionales (cada región pesa según el gasto de sus jubilados).
'''),
    code(SETUP),
    code(r'''N_BOOTSTRAP = 300
R = pipeline.calcular(n_bootstrap=N_BOOTSTRAP)
niv, vm = R['niveles'], R['var_mensual']'''),
    md(r'''
## Estructura de precios

Nodos de cada región: aperturas publicadas, restos derivados de las ponderaciones oficiales y restos
valorizados con el índice del agregado. Debajo: los meses en que el INDEC no publicó alguna apertura
(aislamiento de 2020), completados con la variación de su agregado, y la estabilidad de los restos
derivados ante el redondeo de las ponderaciones oficiales (4 decimales).
'''),
    code(r'''e = R['estructura']
display(pd.crosstab(e['region'], e['tipo']))
display(Markdown('Parte de cada canasta valorizada con cada tipo de índice (%):'))
display((R['cobertura_precios'] * 100).round(1))
display(R['imputaciones'])
display(R['sensibilidad_restos'].sort_values('dispersion_p5_p95_%', ascending=False).head(8))'''),
    md(r'''
## Validación: replicar el IPC oficial

Con las ponderaciones oficiales, la misma estructura de nodos reproduce el IPC nacional y el nivel
general de cada región. Si no lo hiciera, no serviría para compararlos.
'''),
    code(r'''v = R['validacion']
print(f"Error maximo nacional: {v['error_pct'].abs().max():.3f}% | ultimo mes: {v['error_pct'].iloc[-1]:.3f}%")
display(v.filter(like='error_pct').abs().max().to_frame('error maximo (%)').round(3))'''),
    md(r'''
## Variación mensual e interanual (%)
'''),
    code(r'''display(vm.tail(13))
display(R['var_interanual'].tail(6))'''),
    md(r'''
## Brecha con el IPC oficial desde noviembre de 2023

La banda es el intervalo de 95% por bootstrap del IIJP. La línea punteada es el método anterior del
IIJP (12 divisiones nacionales), que subestima la brecha porque ignora la composición dentro de cada
división.
'''),
    code(r'''fig = graficos.g02_brecha_nov23(R); plt.show()'''),
    md(r'''
## Brecha por período y sus dos componentes

La brecha IIJP vs IPC oficial combina dos cosas distintas:

1. **Efecto edad**: IIJP vs el mismo cálculo con la canasta de *todos* los hogares de la ENGHo 2017/18.
2. **Efecto canasta vieja**: ese IPC 2017/18 vs el IPC oficial (ENGHo 2004/05).
'''),
    code(r'''fig = graficos.g03_brecha_historica(R); plt.show()
display(R['periodos'])'''),
    code(r'''if 'bootstrap_brechas' in R:
    display(Markdown('**Intervalos de 95% por bootstrap (incertidumbre muestral de la ENGHo):**'))
    display(R['bootstrap_brechas'])'''),
    md(r'''
## ¿La diferencia es persistente? (test de la media mensual)

Diferencia mensual en logaritmos entre los índices, con intervalo de 95% robusto a autocorrelación
(Newey-West). Responde si la brecha se acumula mes a mes o se concentra en pocos meses; con períodos
cortos tiene poca potencia. La precisión de la canasta la mide el bootstrap.
'''),
    code(r'''with pd.option_context('display.float_format', '{:,.3f}'.format):
    display(R['brecha_estadistica'])'''),
    md(r'''
## Regiones

IIJP de cada región contra el IPC oficial de la misma región. Las muestras regionales de hogares
jubilados son chicas fuera de GBA y Pampeana (ver `hogares_jubilados_muestra`).
'''),
    code(r'''fig = graficos.g07_regiones(R); plt.show()
display(R['peso_regiones'])
pr = R['periodos_regionales']
display(pr[pr['periodo'].isin(['Completo', 'Milei (nov-23 al último dato)'])])'''),
    md(r'''
## Qué explica la brecha

Aporte de cada componente: (ponderación efectiva de la canasta A − la de la canasta B) × (variación del
componente − variación promedio de B). Se calcula por nodo y se suma por división; los aportes suman la
brecha. La brecha "vs IPC oficial" usa el IPC replicado con sus ponderaciones (difiere levemente del
publicado). Ponderaciones efectivas en % del valor de la canasta al inicio del período.
'''),
    code(r'''def ver_descomposicion(clave):
    d = R['descomposicion'][clave].copy()
    cols = ['pond_ef_iijp', 'pond_ef_ipc_oficial', 'pond_ef_ipc_1718']
    d[cols] = d[cols] * 100
    a = d.attrs
    print(f"{a['desde']} a {a['hasta']}: brecha vs IPC oficial {a['brecha_vs_oficial']:+.2f}% = "
          f"efecto edad {a['brecha_edad']:+.2f}% y canasta vieja {a['brecha_canasta']:+.2f}% (aprox.)")
    display(d)
    n = R['descomposicion_aperturas'][clave]
    display(Markdown('Aperturas con mayor aporte (en puntos de %):'))
    display(pd.concat([n.head(6), n.tail(4)])[['descripcion', 'aporte_vs_ipc_oficial', 'aporte_efecto_edad',
                                               'aporte_efecto_canasta_nueva']].round(2))

fig = graficos.g04_descomposicion(R, 'nov23_ultimo'); plt.show()
ver_descomposicion('nov23_ultimo')'''),
    code(r'''ver_descomposicion('dic16_ultimo')'''),
    md(r'''
## Sensibilidad: ¿qué conclusiones son firmes?

Cada variante cambia **una** decisión metodológica respecto de la especificación principal (nivel de
detalle, definición de la población, ponderación, fórmula, precios de referencia) y recalcula la brecha
con el IPC oficial, el efecto edad (contra todos los hogares con la misma especificación) y cuánto más
alto sería hoy el haber si se hubiera indexado por esa variante desde abril de 2024. Una conclusión es
firme si mantiene el signo en todas las variantes (`mismo_signo_en_todas`).
'''),
    code(r'''fig = graficos.g08_variantes(R); plt.show()
display(R['variantes_resumen'])'''),
    code(r'''display(R['variantes'].drop(columns=['descripcion']))'''),
    *figuras_divulgacion(['iijp_02_historia', 'iijp_03_desde_nov23', 'iijp_04_que_explica', 'iijp_05_regiones']),
    *descarga('IIJP_02_iijp_vs_ipc'),
]

# ------------------------------------------------------------------------------------------------
NB03 = [
    md(r'''
# 03 · Jubilación mínima, bono y costo fiscal

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/IPC_jubilados/blob/main/notebooks/03_haberes_y_fiscal.ipynb)

- Haber mínimo (datos.gob.ar) y bono (decretos; congelado en $70.000 desde marzo 2024).
- Movilidad vigente (DNU 274/2024): el haber de cada mes sube lo que subió el IPC dos meses antes.
- Poder adquisitivo de la mínima medido con el IPC y con el **IIJP haber mínimo** (la canasta de los
  hogares jubilados que cobran alrededor de la mínima).
- Contrafactual: la misma regla con el IIJP. Costo fiscal con el gasto real en jubilaciones y pensiones
  (IMIG, repo `cuentas_publicas`).
'''),
    code(SETUP),
    code(r'''N_BOOTSTRAP = 300   # este notebook no usa los intervalos, pero van al Excel y a los graficos del ZIP (0 = mas rapido)
R = pipeline.calcular(n_bootstrap=N_BOOTSTRAP)
hab = R['haberes']'''),
    md(r'''
## La regla de movilidad se cumple

Desde mayo 2024 el aumento del haber mínimo coincide exactamente con la variación del IPC de dos meses
antes, calculada desde los niveles del índice con 2 decimales (no la publicada a 1 decimal).
'''),
    code(r'''r = R['regla_movilidad'].copy()
r[['aumento_observado', 'ipc_t_menos_2']] *= 100   # en %
display(r.tail(8))
print('Meses que cumplen la regla:', r['ok'].sum(), 'de', len(r))'''),
    md(r'''
## Poder adquisitivo (noviembre 2023 = 100)

Haber mínimo con y sin bono, deflactado por el IPC oficial, por el IIJP y por el IIJP haber mínimo.
'''),
    code(r'''fig = graficos.g05_haber_real(R); plt.show()'''),
    code(r'''b = pd.Period('2023-11', 'M')
u = hab.dropna(subset=['real_haber_ipc']).index.max()
t = pd.DataFrame({f'{bono}, {nom}': hab[f'{col}_{k}'] / hab.loc[b, f'{col}_{k}'] - 1
                  for bono, col in [('sin bono', 'real_haber'), ('con bono', 'real_con_bono')]
                  for nom, k in [('IPC', 'ipc'), ('IIJP', 'iijp'), ('IIJP haber mínimo', 'iijp_minimo')]})
display((t.loc[['2023-12', '2024-02', '2024-12', '2025-12', str(u)]] * 100).round(1))
print(f"Bono de $70.000 actualizado por IPC desde marzo 2024 en {u}: ${hab.loc[u, 'bono_indexado_ipc']:,.0f}")'''),
    md(r'''
## Contrafactual: haber indexado por IIJP desde abril 2024

Misma regla de movilidad (variación de dos meses antes, con 2 decimales) usando el IIJP o el IIJP haber
mínimo en lugar del IPC.
'''),
    code(r'''c = hab.loc['2024-04':, ['haber_minimo', 'haber_cf_ipc', 'haber_cf_iijp', 'haber_cf_iijp_minimo']].copy()
c['diferencia_iijp_%'] = (hab['factor_iijp'] - 1) * 100
c['diferencia_iijp_minimo_%'] = (hab['factor_iijp_minimo'] - 1) * 100
display(c.iloc[::3])
u2 = hab['factor_iijp'].dropna().index.max()
for k, nom in [('iijp', 'IIJP'), ('iijp_minimo', 'IIJP haber minimo')]:
    f = hab.loc[u2, f'factor_{k}']
    print(f"En {u2} el haber indexado por {nom} seria {100 * (f - 1):.2f}% mayor: "
          f"${hab.loc[u2, f'haber_cf_{k}'] - hab.loc[u2, 'haber_cf_ipc']:,.0f} por mes en la minima.")'''),
    md(r'''
## Costo fiscal

Como la movilidad aplica el mismo porcentaje a todos los haberes, el costo extra de cada mes es el
gasto en jubilaciones y pensiones (contributivas + no contributivas, IMIG) por (factor − 1). Es una cota
superior: ese gasto incluye el bono, que no se indexa.
'''),
    code(r'''fig = graficos.g06_costo_fiscal(R); plt.show()
fa = R['fiscal_anual']
display(fa[['meses', 'gasto_previsional', 'costo_extra', 'costo_pct_gasto_prev', 'costo_pct_res_financiero',
            'costo_pct_pib']])'''),
    md(r'''
## ¿Y si la brecha fuera permanente?

Si el IIJP superara al IPC en *d* puntos por año, el costo relativo al gasto previsional sería
(1 + d)ⁿ − 1, **independiente de la demografía** (el envejecimiento escala igual el gasto con y sin el
cambio de índice). En % del PIB se usa la relación gasto previsional / PIB del último año completo.
'''),
    code(r'''print(f"Gasto previsional / PIB {R['meta']['anio_pib_ref']}: {R['meta']['gasto_prev_pct_pib']:.2f}%")
display(R['fiscal_desvio_permanente'].pivot(index='desvio_pp_anual', columns='anios', values='costo_pct_pib').round(2))'''),
    *figuras_divulgacion(['iijp_06_jubilacion_minima']),
    *descarga('IIJP_03_haberes_y_fiscal', fuentes_originales=True),
    md(r'''
## Excel completo: resultados y datos originales

Un solo Excel con **todos los resultados** (las mismas hojas que el Excel del ZIP) y **los datos
originales** que usa el análisis, en las hojas `Dato_*`: IPC por divisiones y por aperturas (INDEC),
ponderaciones oficiales del IPC (canasta de la ENGHo 2004/05), microdatos de la ENGHo 2017/18 (hogares,
personas y gastos, con las columnas que usa el cálculo), haber mínimo, bono, gasto previsional (IMIG) y
PIB. La hoja `Indice` describe cada hoja y su fuente. Pesa unos 30 MB y tarda un par de minutos en
escribirse. En Colab se descarga solo (si el navegador pregunta, permitir descargas múltiples).
'''),
    code(r'''from src.exportar import excel_completo
xlsx_path = excel_completo(R, 'IIJP_resultados_y_datos_originales')
print('Excel:', xlsx_path)
if 'google.colab' in sys.modules:
    from google.colab import files
    files.download(xlsx_path)'''),
]


if __name__ == '__main__':
    (RAIZ / 'notebooks').mkdir(exist_ok=True)
    guardar('01_canasta_jubilados.ipynb', NB01)
    guardar('02_iijp_vs_ipc.ipynb', NB02)
    guardar('03_haberes_y_fiscal.ipynb', NB03)
