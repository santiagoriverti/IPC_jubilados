"""Genera los notebooks de notebooks/ (no editarlos a mano: editar este script y regenerar).

Uso:  python scripts/gen_notebooks.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

SETUP = r'''# Configuracion: en Colab clona (o actualiza) el repo; en local usa la carpeta del repo
import os, sys, subprocess
REPO = 'https://github.com/santiagoriverti/IPC_jubilados.git'
if 'google.colab' in sys.modules:
    RAIZ = '/content/IPC_jubilados'
    if os.path.exists(RAIZ):
        subprocess.run(['git', '-C', RAIZ, 'pull', '-q'], check=True)
    else:
        subprocess.run(['git', 'clone', '-q', '--depth', '1', REPO, RAIZ], check=True)
else:  # subir desde la carpeta actual hasta encontrar el repo
    RAIZ = os.getcwd()
    while not os.path.exists(os.path.join(RAIZ, 'src', 'pipeline.py')) and os.path.dirname(RAIZ) != RAIZ:
        RAIZ = os.path.dirname(RAIZ)
sys.path.insert(0, RAIZ)

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

Arma las ponderaciones del IIJP a partir de los **microdatos** de la Encuesta Nacional de Gastos de los
Hogares 2017/18 (INDEC): gasto de consumo de cada hogar por división COICOP (`gc_01`…`gc_12`).

- Reproduce la canasta del TP original (hogares con al menos un mayor de 65, mezcla 0,69 / 0,31).
- Define la población de referencia del IIJP: **hogares jubilados** (jubilaciones y pensiones ≥ 50% del ingreso).
- Compara con el IPC oficial, que todavía usa la estructura de gasto de la **ENGHo 2004/05**.
- Mide la incertidumbre muestral de las ponderaciones (bootstrap de hogares).
'''),
    code(SETUP),
    code(r'''N_BOOTSTRAP = 300   # replicas para los intervalos de confianza (0 = no calcular)
R = pipeline.calcular(n_bootstrap=N_BOOTSTRAP)'''),
    md(r'''
## Poblaciones

Cantidad de hogares en la muestra y expandidos (con el factor `pondera`) de cada definición.
'''),
    code(r'''display(R['poblaciones'])
print(f"Proporcion ponderada de hogares con un solo mayor de 65: {R['peso_tp_1_mayor']:.4f} (el TP usa 0,69)")'''),
    md(r'''
## Ponderaciones por división (en %)

- `ipc_oficial`: IPC nacional del INDEC (ENGHo 2004/05).
- `tp_original`: lo que cargó el TP. `tp`: la misma canasta recalculada desde los microdatos (coincide).
- `total`: todos los hogares con la ENGHo 2017/18 → lo que sería un IPC con canasta actualizada.
- `jubilados`: **canasta del IIJP**. `jub_bajos` / `jub_altos`: mitades por ingreso per cápita.
'''),
    code(r'''W = R['ponderaciones'].set_index('division')
display((W * 100).round(1))'''),
    code(r'''fig = graficos.g01_ponderaciones(R); plt.show()'''),
    md(r'''
**Lectura.** Frente a todos los hogares de la misma encuesta, los hogares jubilados gastan más en
alimentos (+3,7 p.p.), salud (+5 p.p.) y equipamiento, y menos en educación, transporte, restaurantes y
ropa. Vivienda y servicios pesa **lo mismo** (14,5%) en ambos: la mayor ponderación de vivienda que el TP
atribuía a los jubilados (13,7% vs 9,4% del IPC) es en realidad un efecto de la **canasta nueva**
(2017/18 vs 2004/05), no de la edad.
'''),
    md(r'''
## Incertidumbre muestral

Intervalos de 95% por bootstrap (remuestreo de hogares estratificado por región). Son angostos: la
diferencia entre jubilados y el total de hogares en salud, educación o transporte no es ruido muestral.
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
display((D[['total', 'jubilados', 'jub_bajos']] * 100).round(1))'''),
]

# ------------------------------------------------------------------------------------------------
NB02 = [
    md(r'''
# 02 · IIJP vs IPC: cuánto difieren y por qué

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/IPC_jubilados/blob/main/notebooks/02_iijp_vs_ipc.ipynb)

**Método.** Índice de canasta fija (Lowe), el mismo concepto que el IPC: las cantidades de la canasta
de 2017/18 se valorizan cada mes con los índices de precios por división del INDEC. La ponderación
efectiva de cada rubro se mueve con sus precios relativos.

El TP original aplicaba siempre las mismas ponderaciones a las variaciones mensuales. Eso no es una
canasta fija: sobrepondera los rubros que venían atrasados y exagera la brecha cuando hay ajustes de
precios relativos grandes (2024).
'''),
    code(SETUP),
    code(r'''N_BOOTSTRAP = 300
R = pipeline.calcular(n_bootstrap=N_BOOTSTRAP)
niv, vm = R['niveles'], R['var_mensual']'''),
    md(r'''
## Validación: replicar el IPC oficial

Con las ponderaciones del INDEC y el mismo cálculo se reproduce el nivel general nacional con un error
máximo de ~0,16% en casi 10 años. Si el método no replicara el IPC, no serviría para compararlo.
'''),
    code(r'''v = R['validacion']
print(f"Error maximo: {v['error_pct'].abs().max():.3f}% | ultimo mes: {v['error_pct'].iloc[-1]:.3f}%")
display(v.tail(6))'''),
    md(r'''
## Variación mensual (%)
'''),
    code(r'''display(vm[['IPC oficial', 'IPC ENGHo 17/18', 'IIJP', 'IIJP jub. bajos', 'IIJP método TP']].tail(13))'''),
    md(r'''
## La brecha del TP era en buena parte un artefacto del método

Desde noviembre de 2023 la planilla del TP acumula una brecha de 3,8% (con un error: en febrero 2024
falta la división Vivienda). El mismo método sin ese error da 6,3%; con canasta fija, la brecha es
**2,4%** a mayo 2026, y la banda de incertidumbre muestral no incluye el valor del TP.
'''),
    code(r'''fig = graficos.g02_brecha_nov23(R); plt.show()'''),
    md(r'''
## Brecha por período y sus dos componentes

La brecha IIJP vs IPC oficial combina dos cosas distintas:

1. **Efecto edad**: IIJP vs un IPC recalculado con la canasta de *todos* los hogares de la ENGHo 2017/18.
2. **Efecto canasta vieja**: ese IPC 2017/18 vs el IPC oficial (ENGHo 2004/05).
'''),
    code(r'''fig = graficos.g03_brecha_historica(R); plt.show()'''),
    code(r'''p = R['periodos']
cols = ['periodo', 'desde', 'hasta', 'IPC oficial (%)', 'IIJP (%)', 'brecha IIJP vs IPC oficial (%)',
        'brecha IPC ENGHo 17/18 vs IPC oficial (%)', 'brecha IIJP método TP vs IPC oficial (%)']
display(p[cols])'''),
    code(r'''if 'bootstrap_brechas' in R:
    display(Markdown('**Intervalos de 95% por bootstrap (incertidumbre muestral de la ENGHo):**'))
    display(R['bootstrap_brechas'])'''),
    md(r'''
**Lectura.** La brecha cambia de signo según el período: positiva con Macri (+2,8%), negativa con
Fernández (−4,0%, tarifas congeladas) y positiva desde fines de 2023 (+2,7%). Desde noviembre de 2023
**el efecto edad es negativo** (la canasta de los jubilados subió algo *menos* que la de todos los
hogares): lo que empuja la brecha es que el IPC oficial usa una canasta de 2004/05 que subpondera
vivienda y servicios y sobrepondera ropa. Una corrección permanente del 3,8% (propuesta del TP) no
tiene sustento en los datos.
'''),
    md(r'''
## ¿La diferencia es sistemática? (test de la media mensual)

Diferencia mensual en logaritmos entre los índices, con intervalo de 95% robusto a autocorrelación
(Newey-West). Si el intervalo incluye el 0, no hay evidencia de una brecha sistemática en ese período.
'''),
    code(r'''display(R['brecha_estadistica'])'''),
    md(r'''
## Qué divisiones explican la brecha

Aporte de cada división: (ponderación efectiva IIJP − ponderación efectiva de la otra canasta) ×
(variación de la división − variación promedio). Los aportes suman la brecha.
'''),
    code(r'''fig = graficos.g04_descomposicion(R, 'nov23_ultimo'); plt.show()
display(R['descomposicion']['nov23_ultimo'])'''),
    code(r'''d = R['descomposicion']['dic16_ultimo']
print({k: round(v, 2) if isinstance(v, float) else v for k, v in d.attrs.items()})
display(d)'''),
]

# ------------------------------------------------------------------------------------------------
NB03 = [
    md(r'''
# 03 · Jubilación mínima, bono y costo fiscal

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/santiagoriverti/IPC_jubilados/blob/main/notebooks/03_haberes_y_fiscal.ipynb)

- Haber mínimo (datos.gob.ar) y bono (decretos; congelado en $70.000 desde marzo 2024).
- Movilidad vigente (DNU 274/2024): el haber de cada mes sube lo que subió el IPC dos meses antes.
- Contrafactual: la misma regla con el IIJP. Costo fiscal con el gasto real en jubilaciones y pensiones
  (IMIG, repo `cuentas_publicas`).
- Al final se descarga un ZIP con el Excel de resultados y los gráficos.
'''),
    code(SETUP),
    code(r'''N_BOOTSTRAP = 0   # este notebook no usa los intervalos; poner 500 si se quiere el Excel completo
R = pipeline.calcular(n_bootstrap=N_BOOTSTRAP)
hab = R['haberes']'''),
    md(r'''
## La regla de movilidad se cumple

Desde mayo 2024 el aumento del haber mínimo coincide con el IPC de dos meses antes (1 decimal).
'''),
    code(r'''r = R['regla_movilidad'].copy()
r[['aumento_observado', 'ipc_t_menos_2']] *= 100   # en %
display(r.tail(8))
print('Meses que cumplen la regla:', r['ok'].sum(), 'de', len(r))'''),
    md(r'''
## Poder adquisitivo (noviembre 2023 = 100)

El haber mínimo **sin bono** está ~10% por encima de noviembre 2023 en términos reales; **con el bono**
está ~10% por debajo. La pérdida del jubilado de la mínima viene sobre todo del bono congelado, no del
índice con que se actualiza el haber. (El TP calculaba −9,8% dividiendo el haber de diciembre por la
inflación que incluía diciembre: mezclaba meses.)
'''),
    code(r'''fig = graficos.g05_haber_real(R); plt.show()'''),
    code(r'''b = pd.Period('2023-11', 'M')
u = hab.dropna(subset=['real_haber_ipc']).index.max()
t = pd.DataFrame({
    'sin bono, IPC': hab['real_haber_ipc'] / hab.loc[b, 'real_haber_ipc'] - 1,
    'sin bono, IIJP': hab['real_haber_iijp'] / hab.loc[b, 'real_haber_iijp'] - 1,
    'con bono, IPC': hab['real_con_bono_ipc'] / hab.loc[b, 'real_con_bono_ipc'] - 1,
    'con bono, IIJP': hab['real_con_bono_iijp'] / hab.loc[b, 'real_con_bono_iijp'] - 1,
}).loc[['2023-12', '2024-02', '2024-12', '2025-12', str(u)]] * 100
display(t.round(1))
print(f"Bono de $70.000 actualizado por IPC desde marzo 2024 en {u}: ${hab.loc[u, 'bono_indexado_ipc']:,.0f}")'''),
    md(r'''
## Contrafactual: haber indexado por IIJP desde abril 2024
'''),
    code(r'''c = hab.loc['2024-04':, ['haber_minimo', 'haber_cf_ipc', 'haber_cf_iijp']].copy()
c['diferencia_%'] = (hab['factor_iijp'] - 1) * 100
display(c.iloc[::3])
u2 = hab['factor_iijp'].dropna().index.max()
print(f"En {u2} el haber indexado por IIJP seria {100 * (hab.loc[u2, 'factor_iijp'] - 1):.2f}% mayor: "
      f"${hab.loc[u2, 'haber_cf_iijp'] - hab.loc[u2, 'haber_cf_ipc']:,.0f} por mes en la minima.")'''),
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
    md(r'''
## Descargar resultados (Excel + gráficos)
'''),
    code(r'''import shutil
sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
from construir import exportar
exportar(R)
zip_path = shutil.make_archive(os.path.join(RAIZ, 'IIJP_resultados'), 'zip', os.path.join(RAIZ, 'output'))
print('ZIP:', zip_path)
if 'google.colab' in sys.modules:
    from google.colab import files
    files.download(zip_path)'''),
]


if __name__ == '__main__':
    (RAIZ / 'notebooks').mkdir(exist_ok=True)
    guardar('01_canasta_jubilados.ipynb', NB01)
    guardar('02_iijp_vs_ipc.ipynb', NB02)
    guardar('03_haberes_y_fiscal.ipynb', NB03)
