"""Graficos (matplotlib, PNG) del analisis. Cada funcion recibe el diccionario de pipeline.calcular()
y devuelve la figura. Paleta categorica validada (azul, naranja, aqua) y divergente azul/rojo."""
from __future__ import annotations

import matplotlib.dates as mdates
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
    for ax, col, tit in [(axes[0], 'aporte_vs_ipc_oficial', f'vs IPC oficial replicado: {a["brecha_vs_oficial"]:+.2f}%'),
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


# ---------------------------------------------------------------------------------------------
# Graficos de divulgacion (documento de prensa y presentacion de docs/divulgacion/): sin titulo (lo
# pone el epigrafe o el titulo de la diapositiva), letra mas grande, decimales con coma y rotulos
# directos. Se exportan a figuras/ (output/figuras/ y la carpeta figuras/ de cada ZIP), con los mismos
# nombres que usan los .tex: esa carpeta se sube tal cual a la carpeta "figuras" de Overleaf.
# ---------------------------------------------------------------------------------------------
RC_DIVULGACION = {'font.size': 12.5, 'axes.titlesize': 13, 'legend.fontsize': 12, 'savefig.dpi': 200}
FUENTE_CORTA = 'Fuente: INECO-UADE con datos del INDEC (IPC y ENGHo 2017/18)'
MILEI = 'Milei (nov-23 al último dato)'


MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre',
         'noviembre', 'diciembre']


def _coma(x, dec=1, signo=False) -> str:
    """Numero con coma decimal (3,1 o +3,1); el cero va sin signo."""
    if round(x, dec) == 0:
        x, signo = 0.0, False
    s = f'{x:+.{dec}f}' if signo else f'{x:.{dec}f}'
    return s.replace('.', ',').replace('-', '−')


def _eje_pct(ax, eje='y', dec=0, signo=False):
    f = mticker.FuncFormatter(lambda v, _: _coma(v, dec, signo) + '%')
    (ax.yaxis if eje == 'y' else ax.xaxis).set_major_formatter(f)


def _mes(p) -> str:
    """'ene-24' (Period o Timestamp)."""
    return f'{MESES[p.month - 1][:3]}-{str(p.year)[2:]}'


def _mes_largo(p) -> str:
    """'agosto 2026'."""
    return f'{MESES[p.month - 1]} {p.year}'


def _eje_meses(ax):
    """Marcas en enero y julio, rotuladas 'ene-24'."""
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _mes(mdates.num2date(v))))


def _eje_anios(ax):
    """Una marca por anio, rotulada '2017'."""
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))


def iijp_01_canasta(R):
    W = R['ponderaciones']
    orden = W.sort_values('jubilados').index
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(9, 6))
        y = range(len(orden))
        alto = 0.38
        for k, (col, lab, c) in enumerate([('ipc_oficial', 'Canasta del IPC oficial (2004/05)', NARANJA),
                                           ('jubilados', 'Canasta de los hogares jubilados (2017/18)', AZUL)]):
            v = W.loc[orden, col] * 100
            yy = [i + (k - 0.5) * alto for i in y]
            ax.barh(yy, v, height=alto - 0.04, color=c, label=lab)
            for yi, vi in zip(yy, v):
                ax.annotate(_coma(vi), (vi, yi), xytext=(3, 0), textcoords='offset points', va='center',
                            fontsize=10, color=TINTA2)
        ax.set_yticks(list(y))
        ax.set_yticklabels([pond.DIVISIONES_CORTO[c] for c in orden])
        _eje_pct(ax, 'x')
        ax.grid(axis='y', visible=False)
        ax.set_xlabel('% del gasto de consumo')
        ax.legend(loc='lower right')
        _pie(fig, 'Fuente: INECO-UADE con datos del INDEC (ENGHo 2004/05 y 2017/18)')
    return fig


def iijp_02_historia(R):
    niv = R['niveles']
    base = niv.index.min()
    b = ((niv['IIJP'] / niv['IIJP'].loc[base]) / (niv['IPC oficial'] / niv['IPC oficial'].loc[base]) - 1) * 100
    x = _fecha(niv.index)
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(9.5, 5))
        cortes = [pd.Period('2019-12', 'M'), pd.Period('2023-11', 'M')]
        tramos = [(base, cortes[0], 'Macri'), (cortes[0], cortes[1], 'Fernández'), (cortes[1], niv.index.max(), 'Milei')]
        for k, (d, h, nombre) in enumerate(tramos):
            if k % 2 == 1:
                ax.axvspan(d.to_timestamp(), h.to_timestamp(), color='#f3f2ee', lw=0)
            medio = d.to_timestamp() + (h.to_timestamp() - d.to_timestamp()) / 2
            ax.text(medio, 1.0, nombre, transform=ax.get_xaxis_transform(), ha='center', va='bottom',
                    fontsize=12, color=TINTA2)
        ax.fill_between(x, b, 0, where=b >= 0, color=AZUL, alpha=0.18, lw=0, interpolate=True)
        ax.fill_between(x, b, 0, where=b < 0, color=ROJO, alpha=0.18, lw=0, interpolate=True)
        ax.plot(x, b, color=AZUL, lw=2.2)
        ax.annotate(_coma(b.iloc[-1], signo=True) + '%', (x[-1], b.iloc[-1]), xytext=(5, 0),
                    textcoords='offset points', va='center', fontsize=11, color=AZUL, fontweight='bold')
        ax.axhline(0, color=GRIS, lw=1)
        _eje_pct(ax, 'y', signo=True)
        ax.set_ylabel('IIJP sobre IPC oficial (acumulado)')
        _pie(fig, FUENTE_CORTA + '. Base diciembre 2016. Arriba de cero: los precios de la canasta de los '
                                 'jubilados subieron más que el IPC.')
    return fig


def iijp_03_brecha_interanual(R):
    """Brecha de los ultimos 12 meses (serie completa: desde dic-2017, sin una base elegida a mano)."""
    b = R['brecha_interanual']
    x = _fecha(b.index)
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(11, 5))
        for col, lab, c in [('IIJP haber mínimo', 'Jubilados que cobran la mínima', NARANJA),
                            ('IIJP', 'Todos los hogares jubilados (IIJP)', AZUL)]:
            y = b[col]
            ax.plot(x, y, color=c, lw=2.2, label=lab)
            ax.annotate(_coma(y.iloc[-1], signo=True) + '%', (x[-1], y.iloc[-1]), xytext=(5, 0),
                        textcoords='offset points', va='center', fontsize=11, color=c, fontweight='bold')
        ax.axhline(0, color=GRIS, lw=1)
        _eje_pct(ax, 'y', signo=True)
        _eje_anios(ax)
        ax.set_ylabel('inflación de 12 meses sobre el IPC')
        ax.legend(loc='upper left')
        _pie(fig, FUENTE_CORTA + '. Cada punto compara los últimos 12 meses. Arriba de cero: los precios de la '
                                 'canasta de los jubilados subieron más que el IPC.')
    return fig


def iijp_04_que_explica(R):
    t = R['descomposicion']['nov23_ultimo']
    t = t.sort_values('aporte_vs_ipc_oficial')
    v = t['aporte_vs_ipc_oficial']
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(9, 6))
        ax.barh(range(len(v)), v, color=[AZUL if x >= 0 else ROJO for x in v], height=0.7)
        for i, vi in enumerate(v):
            ax.annotate(_coma(vi, signo=True), (vi, i), xytext=(4 if vi >= 0 else -4, 0), textcoords='offset points',
                        ha='left' if vi >= 0 else 'right', va='center', fontsize=10, color=TINTA2)
        ax.set_yticks(range(len(v)))
        ax.set_yticklabels(t['division'])
        ax.axvline(0, color=GRIS, lw=1)
        ax.margins(x=0.12)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda z, _: _coma(z, 1, True)))
        ax.grid(axis='y', visible=False)
        ax.set_xlabel('aporte a la diferencia con el IPC oficial (puntos porcentuales)')
        _pie(fig, FUENTE_CORTA + f'. Noviembre 2023 a {_mes_largo(R["niveles"].index.max())}. '
                                 'Azul: suma; rojo: resta.')
    return fig


def iijp_05_regiones(R):
    t = R['periodos_regionales']
    s = t[t['periodo'] == MILEI].set_index('region')['brecha (%)']
    nombres = {'GBA': 'Gran Buenos Aires'}
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(9, 4.8))
        y = range(len(s))
        ax.barh(list(y), s.values, color=AZUL, height=0.62)
        for yi, vi in zip(y, s.values):
            ax.annotate(_coma(vi, signo=True) + '%', (vi, yi), xytext=(4, 0), textcoords='offset points',
                        va='center', fontsize=11, color=TINTA2)
        ax.set_yticks(list(y))
        ax.set_yticklabels([nombres.get(r, r) for r in s.index])
        ax.invert_yaxis()
        ax.axvline(0, color=GRIS, lw=1)
        ax.margins(x=0.1)
        _eje_pct(ax, 'x')
        ax.grid(axis='y', visible=False)
        ax.set_xlabel('IIJP de la región sobre el IPC de la misma región')
        _pie(fig, FUENTE_CORTA + f'. Noviembre 2023 a {_mes_largo(R["niveles"].index.max())}.')
    return fig


def iijp_06_jubilacion_minima(R):
    """Poder de compra de la jubilacion minima en toda la serie (diciembre 2016 = 100). El bono se suma desde
    el primer mes cargado en data/reference/bono_previsional.csv."""
    h = R['haberes'].dropna(subset=['real_haber_ipc'])
    x = _fecha(h.index)
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(11, 5.2))
        for defl, lab, c in [('ipc', 'medida con el IPC oficial', AZUL),
                             ('iijp_minimo', 'medida con la inflación de los jubilados de la mínima', NARANJA)]:
            base = h[f'real_haber_{defl}'].iloc[0]
            sin = h[f'real_haber_{defl}'] / base * 100
            con = (h[f'real_con_bono_{defl}'] / base * 100).fillna(sin)  # meses sin bono: el haber solo
            ax.plot(x, con, color=c, lw=2.4, label=f'Con bono, {lab}')
            sin = sin.loc[h['bono'].first_valid_index():]
            ax.plot(_fecha(sin.index), sin, color=c, lw=1.6, ls='--', label=f'Sin bono, {lab}')
            for y in (sin, con):
                ax.annotate(_coma(y.iloc[-1], 0), (x[-1], y.iloc[-1]), xytext=(5, 0), textcoords='offset points',
                            va='center', fontsize=11, color=c, fontweight='bold')
        ax.axhline(100, color=GRIS, lw=1)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _coma(v, 0)))
        _eje_anios(ax)
        ax.set_ylabel('poder de compra (diciembre 2016 = 100)')
        ax.legend(loc='lower left', fontsize=10.5)
        inicio = _mes_largo(h['bono'].dropna().index.min())
        _pie(fig, 'Fuente: INECO-UADE con datos del INDEC, datos.gob.ar (haber mínimo) y decretos del bono. '
                  f'El bono se incluye desde {inicio}.')
    return fig


def iijp_07_inflacion_anual(R):
    """Inflacion anual (diciembre a diciembre) del IPC y del IIJP, con la brecha de cada anio."""
    t = R['inflacion_anual']
    rot = [str(a) if c else f'{a}*' for a, c in zip(t['anio'], t['completo'])]
    with plt.rc_context(RC_DIVULGACION):
        fig, ax = plt.subplots(figsize=(11, 5.4))
        ancho = 0.4
        xs = range(len(t))
        for k, (col, lab, c) in enumerate([('IPC oficial (%)', 'IPC oficial', NARANJA), ('IIJP (%)', 'IIJP', AZUL)]):
            xx = [i + (k - 0.5) * ancho for i in xs]
            ax.bar(xx, t[col], width=ancho - 0.03, color=c, label=lab)
            for xi, vi in zip(xx, t[col]):
                ax.annotate(_coma(vi, 0), (xi, vi), xytext=(0, 2), textcoords='offset points', ha='center',
                            va='bottom', fontsize=9.5, color=TINTA2)
        tope = t[['IPC oficial (%)', 'IIJP (%)']].max(axis=1)
        for i, (vi, bi) in enumerate(zip(tope, t['brecha IIJP vs IPC oficial (%)'])):
            ax.annotate(_coma(bi, 1, True), (i, vi), xytext=(0, 17), textcoords='offset points', ha='center',
                        va='bottom', fontsize=10.5, fontweight='bold', color=AZUL if bi >= 0 else ROJO)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(rot)
        ax.margins(y=0.14)
        _eje_pct(ax, 'y')
        ax.grid(axis='x', visible=False)
        ax.set_ylabel('inflación anual (diciembre a diciembre)')
        ax.legend(loc='upper left')
        ult = t.iloc[-1]
        nota = '' if ult['completo'] else f' *{ult["anio"]}: diciembre a {_mes_largo(pd.Period(ult["hasta"], "M"))}.'
        _pie(fig, FUENTE_CORTA + '. En negrita: brecha del año (IIJP sobre IPC, en %).' + nota)
    return fig


def iijp_08_inflacion_mensual(R):
    """Inflacion mensual del IPC y del IIJP: serie completa y ultimos 24 meses."""
    v = R['var_mensual'].dropna()
    with plt.rc_context(RC_DIVULGACION):
        fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8), gridspec_kw={'hspace': 0.35})
        for ax, d, ancho, marca in ((a1, v, 2, None), (a2, v.iloc[-24:], 2.4, 'o')):
            x = _fecha(d.index)
            for col, c in [('IPC oficial', NARANJA), ('IIJP', AZUL)]:
                ax.plot(x, d[col], color=c, lw=ancho, label=col, marker=marca, ms=4)
            ax.set_ylabel('inflación mensual')
        _eje_pct(a1, 'y')
        _eje_pct(a2, 'y', dec=1)
        _eje_anios(a1)
        a1.set_title('Desde enero de 2017', fontweight='normal')
        a1.legend(loc='upper left')
        a2.set_title('Últimos 24 meses', fontweight='normal')
        a2.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
        a2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda z, _: _mes(mdates.num2date(z))))
        xu = _fecha(v.index)[-1]
        a, b = v['IPC oficial'].iloc[-1], v['IIJP'].iloc[-1]
        for y, c, dy in [(a, NARANJA, -9 if a <= b else 9), (b, AZUL, 9 if a <= b else -9)]:
            a2.annotate(_coma(y) + '%', (xu, y), xytext=(6, dy), textcoords='offset points', va='center',
                        fontsize=11, color=c, fontweight='bold')
        _pie(fig, FUENTE_CORTA + f'. Último dato: {_mes_largo(v.index.max())}.')
    return fig


GRAFICOS_DIVULGACION = {
    'iijp_01_canasta': iijp_01_canasta,
    'iijp_02_historia': iijp_02_historia,
    'iijp_03_brecha_interanual': iijp_03_brecha_interanual,
    'iijp_04_que_explica': iijp_04_que_explica,
    'iijp_05_regiones': iijp_05_regiones,
    'iijp_06_jubilacion_minima': iijp_06_jubilacion_minima,
    'iijp_07_inflacion_anual': iijp_07_inflacion_anual,
    'iijp_08_inflacion_mensual': iijp_08_inflacion_mensual,
}


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
