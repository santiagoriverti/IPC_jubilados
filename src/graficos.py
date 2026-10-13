"""Graficos (matplotlib, PNG) del analisis. Cada funcion recibe el diccionario de pipeline.calcular()
y devuelve la figura. Paleta categorica validada (azul, naranja, aqua) y divergente azul/rojo."""
from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from . import ponderaciones as pond

AZUL, NARANJA, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
ROJO, GRIS = '#e34948', '#8a8984'
TINTA, TINTA2 = '#0b0b0b', '#52514e'
FUENTE = 'Fuente: elaboración propia con datos de INDEC (IPC por aperturas regionales, ENGHo 2017/18)'

plt.rcParams.update({
    'font.size': 10, 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    'axes.edgecolor': '#c9c8c3', 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#ecebe7',
    'grid.linewidth': 0.8, 'axes.axisbelow': True, 'legend.frameon': False, 'figure.dpi': 110,
    'savefig.dpi': 150, 'savefig.bbox': 'tight', 'lines.linewidth': 2,
})


def _fecha(idx) -> pd.DatetimeIndex:
    return idx.to_timestamp() if isinstance(idx, pd.PeriodIndex) else idx


def _pie(fig, texto=FUENTE):
    fig.text(0.01, -0.02, texto, fontsize=8, color=TINTA2, ha='left', va='top')


def g01_ponderaciones(R):
    W = R['ponderaciones']
    orden = W.sort_values('jubilados').index
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = range(len(orden))
    alto = 0.26
    series = [('ipc_oficial', 'IPC oficial (ENGHo 2004/05)', NARANJA),
              ('total', 'Todos los hogares (ENGHo 2017/18)', AQUA),
              ('jubilados', 'Hogares jubilados (ENGHo 2017/18)', AZUL)]
    for k, (col, lab, c) in enumerate(series):
        ax.barh([i + (k - 1) * alto for i in y], W.loc[orden, col] * 100, height=alto - 0.03, color=c, label=lab)
    ax.set_yticks(list(y))
    ax.set_yticklabels([pond.DIVISIONES_CORTO[c] for c in orden])
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.grid(axis='y', visible=False)
    ax.set_title('Estructura del gasto de consumo por división')
    ax.legend(loc='lower right')
    _pie(fig)
    return fig


def g02_brecha_nov23(R):
    niv = R['niveles']
    base = pd.Period('2023-11', 'M')
    ipc = niv['IPC oficial'].loc[base:]
    b = lambda s: ((s.loc[base:] / s.loc[base]) / (ipc / ipc.loc[base]) - 1) * 100  # noqa: E731
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    x = _fecha(ipc.index)
    if 'banda_brecha_nov23' in R:
        band = R['banda_brecha_nov23']
        ax.fill_between(_fecha(band.index), band['p2.5'], band['p97.5'], color=AZUL, alpha=0.15, lw=0,
                        label='IIJP: intervalo 95% (muestra ENGHo)')
    series = [(niv['IIJP'], 'IIJP (hogares jubilados)', AZUL, '-'),
              (niv['IIJP haber mínimo'], 'IIJP haber mínimo', NARANJA, '-'),
              (niv['IPC ENGHo 17/18'], 'Todos los hogares, canasta 2017/18', AQUA, '-')]
    if 'variantes_niveles' in R:
        series.append((R['variantes_niveles']['div_nacional'], 'IIJP por 12 divisiones (método anterior)', GRIS, '--'))
    for s, lab, c, ls in series:
        y = b(s)
        ax.plot(x, y, color=c, ls=ls, lw=2 if ls == '-' else 1.5, label=lab)
        ax.annotate(f'{y.iloc[-1]:+.1f}%', (x[-1], y.iloc[-1]), xytext=(4, 0), textcoords='offset points',
                    va='center', fontsize=8.5, color=TINTA2)
    ax.axhline(0, color=GRIS, lw=1)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=1))
    ax.set_title('Brecha acumulada contra el IPC oficial desde noviembre 2023')
    ax.set_ylabel('índice / IPC oficial − 1')
    ax.legend(loc='upper left', fontsize=9)
    _pie(fig)
    return fig


def g03_brecha_historica(R):
    niv = R['niveles']
    base = niv.index.min()
    r = lambda a, b: ((niv[a] / niv[a].loc[base]) / (niv[b] / niv[b].loc[base]) - 1) * 100  # noqa: E731
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    x = _fecha(niv.index)
    ax.plot(x, r('IIJP', 'IPC oficial'), color=AZUL, label='IIJP vs IPC oficial (brecha total)')
    ax.plot(x, r('IIJP', 'IPC ENGHo 17/18'), color=AQUA, label='Efecto edad: IIJP vs IPC con canasta 2017/18')
    ax.plot(x, r('IPC ENGHo 17/18', 'IPC oficial'), color=NARANJA,
            label='Efecto canasta vieja: IPC 2017/18 vs IPC oficial (2004/05)')
    ax.axhline(0, color=GRIS, lw=1)
    for fecha, txt in [('2019-12', 'dic-19'), ('2023-11', 'nov-23')]:
        ax.axvline(pd.Period(fecha, 'M').to_timestamp(), color='#c9c8c3', lw=1, ls=':')
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.set_title('Brecha acumulada desde diciembre 2016 y sus dos componentes')
    ax.legend(loc='lower left', fontsize=9)
    _pie(fig)
    return fig


def g04_descomposicion(R, clave='nov23_ultimo'):
    t = R['descomposicion'][clave].copy()
    a = t.attrs
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.4), sharey=True)
    orden = t.sort_values('aporte_vs_ipc_oficial').index
    for ax, col, tit in [(axes[0], 'aporte_vs_ipc_oficial', f'vs IPC oficial: {a["brecha_vs_oficial"]:+.2f}%'),
                         (axes[1], 'aporte_efecto_edad', f'Efecto edad (vs IPC 2017/18): {a["brecha_edad"]:+.2f}%')]:
        v = t.loc[orden, col]
        ax.barh(range(len(v)), v, color=[AZUL if x >= 0 else ROJO for x in v], height=0.7)
        ax.axvline(0, color=GRIS, lw=1)
        ax.set_title(tit, fontsize=11)
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%+.1f'))
        ax.grid(axis='y', visible=False)
        ax.set_xlabel('aporte a la brecha (puntos de %)')
    axes[0].set_yticks(range(len(orden)))
    axes[0].set_yticklabels(t.loc[orden, 'division'])
    fig.suptitle(f'Qué divisiones explican la brecha del IIJP ({a["desde"]} a {a["hasta"]})',
                 x=0.01, ha='left', fontweight='bold', fontsize=12)
    _pie(fig, FUENTE + '. Azul: suma brecha; rojo: resta.')
    fig.tight_layout()
    return fig


def g05_haber_real(R):
    h = R['haberes'].dropna(subset=['real_haber_ipc'])
    base = h['haber_con_bono'].loc[pd.Period('2023-11', 'M')]
    base_s = h['haber_minimo'].loc[pd.Period('2023-11', 'M')]
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    x = _fecha(h.index)
    ax.plot(x, h['real_con_bono_ipc'] / base * 100, color=NARANJA, label='Haber mínimo + bono, deflactado por IPC')
    ax.plot(x, h['real_con_bono_iijp_minimo'] / base * 100, color=NARANJA, ls='--',
            label='Haber mínimo + bono, deflactado por IIJP haber mínimo')
    ax.plot(x, h['real_haber_ipc'] / base_s * 100, color=AZUL, label='Haber mínimo sin bono, deflactado por IPC')
    ax.plot(x, h['real_haber_iijp_minimo'] / base_s * 100, color=AZUL, ls='--',
            label='Haber mínimo sin bono, deflactado por IIJP haber mínimo')
    ax.axhline(100, color=GRIS, lw=1)
    ax.set_title('Poder adquisitivo de la jubilación mínima (noviembre 2023 = 100)')
    ax.legend(loc='upper right', fontsize=9)
    _pie(fig, FUENTE + ', datos.gob.ar (haber mínimo) y decretos (bono).')
    return fig


def g06_costo_fiscal(R):
    m = R['fiscal_mensual']
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.bar(_fecha(m.index), m['costo_pct_gasto'], width=22, color=AZUL)
    ax.axhline(0, color=GRIS, lw=1)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=1))
    ax.set_title('Costo de indexar por IIJP desde abril 2024, en % del gasto en jubilaciones y pensiones')
    _pie(fig, FUENTE + ', IMIG (Hacienda).')
    return fig


def g07_regiones(R):
    t = R['periodos_regionales']
    per = [('Milei (nov-23 al último dato)', 'nov-23 al último dato', AZUL), ('Completo', 'dic-16 al último dato', AQUA)]
    regiones = list(dict.fromkeys(t['region']))
    fig, ax = plt.subplots(figsize=(9, 4.8))
    alto = 0.38
    con_ic = 'brecha_p2.5' in t.columns
    for k, (p, lab, c) in enumerate(per):
        s = t[t['periodo'] == p].set_index('region').loc[regiones]
        v = s['brecha (%)']
        y = [i + (k - 0.5) * alto for i in range(len(regiones))]
        ax.barh(y, v, height=alto - 0.04, color=c, label=lab)
        extremo = v
        if con_ic:
            ax.errorbar(v, y, xerr=[v - s['brecha_p2.5'], s['brecha_p97.5'] - v], fmt='none', ecolor=TINTA2,
                        elinewidth=1, capsize=2)
            extremo = s['brecha_p97.5'].where(v >= 0, s['brecha_p2.5'])
        for yi, vi, xi in zip(y, v, extremo):
            ax.annotate(f'{vi:+.1f}', (xi, yi), xytext=(4 if vi >= 0 else -4, 0), textcoords='offset points',
                        ha='left' if vi >= 0 else 'right', va='center', fontsize=8, color=TINTA2)
    ax.set_yticks(range(len(regiones)))
    ax.set_yticklabels(regiones)
    ax.invert_yaxis()
    ax.axvline(0, color=GRIS, lw=1)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.grid(axis='y', visible=False)
    ax.set_title('Brecha del IIJP contra el IPC de cada región')
    ax.legend(loc='lower right', fontsize=9)
    _pie(fig, FUENTE + ('. Barras de error: intervalo de 95% por bootstrap.' if con_ic else ''))
    return fig


def g08_variantes(R):
    t = R['variantes'].iloc[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(11, 7), sharey=True)
    for ax, col, tit in [(axes[0], 'brecha_milei', 'Brecha vs IPC oficial, nov-23 al último dato'),
                         (axes[1], 'edad_completo', 'Efecto edad, dic-16 al último dato')]:
        y = range(len(t))
        es_p = (t['variante'] == 'principal').values
        ax.scatter(t[col][~es_p], [i for i, e in zip(y, es_p) if not e], s=40, color=AZUL, zorder=3)
        ax.scatter(t[col][es_p], [i for i, e in zip(y, es_p) if e], s=90, color=NARANJA, zorder=4,
                   edgecolor='white', linewidth=1.5)
        ax.axvline(float(t.loc[es_p, col].iloc[0]), color=NARANJA, lw=1, ls=':')
        ax.axvline(0, color=GRIS, lw=1)
        ax.set_title(tit, fontsize=11)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
        ax.grid(axis='y', visible=False)
    axes[0].set_yticks(range(len(t)))
    axes[0].set_yticklabels(t['etiqueta'])
    fig.suptitle('Sensibilidad del IIJP a cada decisión metodológica (naranja: especificación principal)',
                 x=0.01, ha='left', fontweight='bold', fontsize=12)
    _pie(fig, FUENTE + '. Cada fila cambia una sola decisión respecto de la principal.')
    fig.tight_layout()
    return fig


GRAFICOS = {
    'g01_ponderaciones': g01_ponderaciones,
    'g02_brecha_nov23': g02_brecha_nov23,
    'g03_brecha_historica': g03_brecha_historica,
    'g04_descomposicion': g04_descomposicion,
    'g05_haber_real': g05_haber_real,
    'g06_costo_fiscal': g06_costo_fiscal,
    'g07_regiones': g07_regiones,
    'g08_variantes': g08_variantes,
}
