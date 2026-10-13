"""Tabla de variantes: cuanto dependen los resultados de cada decision metodologica.

Cada variante cambia UNA decision respecto del indice principal (aperturas regionales con restos
derivados, hogares jubilados, ponderaciones plutocraticas, formula de Lowe, precios de referencia del
relevamiento) y recalcula:

- la brecha contra el IPC oficial en cada periodo;
- el efecto edad: contra un indice de todos los hogares calculado con la misma especificacion;
- cuanto mas alto seria hoy el haber si se hubiera indexado por esa variante desde abril 2024.

Regla de lectura: una conclusion es firme si vale (mismo signo) en todas las variantes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import estructura as estr
from . import fuentes, haberes, indices
from . import ponderaciones as pond

ESPEC_BASE = {'estructura': 'aperturas', 'poblacion': 'jubilados', 'metodo': 'plutocratica', 'formula': 'lowe'}

VARIANTES = [
    ('Principal', 'principal', 'Aperturas regionales, restos derivados, hogares jubilados, Lowe, plutocrática', {}),
    ('Detalle', 'resto_agregado', 'Restos no publicados con el índice de su agregado',
     {'estructura': 'aperturas_resto_agregado'}),
    ('Detalle', 'div_regional', '12 divisiones con canastas e índices de cada región', {'estructura': 'div_regional'}),
    ('Detalle', 'div_nacional', '12 divisiones nacionales (método anterior del IIJP)', {'estructura': 'div_nacional'}),
] + [
    ('Población', p, pond.POBLACIONES[p][0], {'poblacion': p})
    for p in ['jub_minimo', 'jub_sin_pnc', 'jub_umbral_75', 'jub_umbral_25', 'jefe_conyuge_jub', 'jefe_65',
              'adultos_jub', 'con_65', 'solo_65', 'jub_bajos', 'jub_altos']
] + [
    ('Ponderación', 'democratica', 'Ponderaciones democráticas (promedio de las estructuras de cada hogar)',
     {'metodo': 'democratica'}),
    ('Fórmula', 'young', 'Young: participaciones de 2017/18 fijas, sin actualizar por precios relativos',
     {'formula': 'young'}),
    ('Fórmula', 'geometrica', 'Geométrica (Cobb-Douglas) con participaciones de 2017/18', {'formula': 'geometrica'}),
    ('Precios de referencia', 'deflactado_trimestre', 'Gasto de cada hogar deflactado por el trimestre de la entrevista',
     {'formula': 'lowe_trimestre'}),
]

ETIQUETAS = {
    'principal': 'Principal', 'resto_agregado': 'Restos = índice del agregado',
    'div_regional': '12 divisiones regionales', 'div_nacional': '12 divisiones nacionales (anterior)',
    'jub_minimo': 'Haber mínimo', 'jub_sin_pnc': 'Sin pensiones no contributivas', 'jub_umbral_75': 'Umbral 75%',
    'jub_umbral_25': 'Umbral 25%', 'jefe_conyuge_jub': 'Jefe/a o cónyuge jubilado', 'jefe_65': 'Jefe/a 65+',
    'adultos_jub': 'Todos los adultos jubilados', 'con_65': 'Con algún 65+', 'solo_65': 'Solo 65+',
    'jub_bajos': 'Jubilados, ingreso bajo', 'jub_altos': 'Jubilados, ingreso alto',
    'democratica': 'Ponderación democrática', 'young': 'Fórmula de Young', 'geometrica': 'Fórmula geométrica',
    'deflactado_trimestre': 'Gasto deflactado por trimestre',
}

PERIODOS_VARIANTES = {'Completo': 'completo', 'Macri (dic-16 a dic-19)': 'macri',
                      'Fernández (dic-19 a nov-23)': 'fernandez', 'Milei (nov-23 al último dato)': 'milei',
                      'Desde 2025 (dic-24 al último dato)': 'desde_2025'}


@dataclass
class Contexto:
    h: pd.DataFrame
    ipc: pd.Series                                     # IPC oficial nacional
    estructuras: dict[str, tuple[estr.Estructura, pd.DataFrame]]   # nombre -> (estructura, gasto por nodo)
    haber: pd.Series                                   # haber minimo
    ultimo: pd.Period


def indice(ctx: Contexto, estructura='aperturas', poblacion='jubilados', metodo='plutocratica',
           formula='lowe') -> pd.Series:
    est, E = ctx.estructuras[estructura]
    P = est.precios
    if formula == 'lowe_trimestre':
        gt = pond.gasto_por_trimestre(E, ctx.h, poblacion)
        q = sum(gt[t] / P.loc[a:b].mean() for t, (a, b) in fuentes.TRIMESTRES_ENGHO.items())
        return indices.lowe_cantidades(P, q)
    w = pond.canasta_nodos(E, ctx.h, poblacion, metodo)
    f = {'lowe': indices.lowe, 'young': indices.young, 'geometrica': indices.geometrica}[formula]
    return f(P, w)


def factor_haber(ctx: Contexto, nivel: pd.Series) -> float:
    """% en que el haber del ultimo mes superaria al efectivo si desde abril 2024 se hubiera
    indexado por `nivel` en lugar del IPC (misma regla: variacion de t-2 con 2 decimales)."""
    hab = ctx.haber.loc[:min(ctx.haber.index.max(), ctx.ultimo + 2)]
    a = haberes.contrafactual(hab, haberes.var_movilidad(nivel))
    b = haberes.contrafactual(hab, haberes.var_movilidad(ctx.ipc))
    return float((a.iloc[-1] / b.iloc[-1] - 1) * 100)


def tabla_variantes(ctx: Contexto) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (tabla de resultados por variante, niveles de cada variante)."""
    per = [(PERIODOS_VARIANTES[n], d, h) for n, d, h in indices.periodos_vigentes(ctx.ultimo)
           if n in PERIODOS_VARIANTES]
    filas, niveles = [], {}
    for grupo, clave, desc, espec in VARIANTES:
        e = {**ESPEC_BASE, **espec}
        a = indice(ctx, **e)
        t = indice(ctx, **{**e, 'poblacion': 'total'})
        niveles[clave] = a
        fila = {'grupo': grupo, 'variante': clave, 'etiqueta': ETIQUETAS[clave], 'descripcion': desc,
                'hogares': int(ctx.h[e['poblacion']].sum())}
        fila.update({f'brecha_{k}': indices.brecha(a, ctx.ipc, d, h) for k, d, h in per})
        fila.update({f'edad_{k}': indices.brecha(a, t, d, h) for k, d, h in per})
        fila['haber_vs_ipc'] = factor_haber(ctx, a)
        fila['var_mensual_ult'] = float(a.pct_change().iloc[-1] * 100)
        fila['var_interanual_ult'] = float((a.iloc[-1] / a.iloc[-13] - 1) * 100)
        filas.append(fila)
    niv = pd.DataFrame(niveles)
    niv.index.name = 'periodo'
    return pd.DataFrame(filas), niv


def resumen(t: pd.DataFrame) -> pd.DataFrame:
    """Para cada resultado: valor principal, rango entre variantes y si el signo se mantiene en todas."""
    num = [c for c in t.columns if c.startswith(('brecha_', 'edad_')) or c == 'haber_vs_ipc']
    v = t.set_index('variante')[num]
    p = v.loc['principal']
    return pd.DataFrame({'principal': p, 'minimo': v.min(), 'variante_minimo': v.idxmin(), 'maximo': v.max(),
                         'variante_maximo': v.idxmax(), 'mismo_signo_en_todas': (np.sign(v) == np.sign(p)).all()})
