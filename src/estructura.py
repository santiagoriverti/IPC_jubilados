"""Estructura de precios del IIJP: con que indice de precios se valoriza cada gasto de la canasta.

El IPC del INDEC se calcula por region (6 regiones) y se publica, por region, al nivel de division,
grupo y algunas clases ("aperturas"); no hay aperturas nacionales. El IIJP valoriza la canasta de cada
region al nivel mas desagregado publicado (los "nodos" de la estructura):

- hojas: aperturas publicadas sin hijos publicados (p. ej. 04.5 Electricidad, gas y otros combustibles);
- restos: cada agregado publicado con hijos publicados tiene un nodo "<codigo>.r" con lo que sus hijos
  publicados no cubren (en Vivienda de GBA: 04.4 Suministro de agua).

El indice de un resto se deduce de la estructura oficial de ponderaciones (INDEC, dic-2016), porque el
IPC agrega los indices con la formula de Laspeyres:

    I_p,t = sum_c W_c I_c,t / W_p    =>    I_resto,t = (W_p I_p,t - sum_c W_c I_c,t) / W_resto,
    W_resto = W_p - sum_c W_c        (c: hijos publicados de p)

Las ponderaciones oficiales estan redondeadas a 4 decimales: si el resto pesa menos de UMBRAL_RESTO del
gasto de la region, esa diferencia queda dominada por el redondeo y el resto se valoriza con el indice
del agregado (supuesto: se mueve como el promedio del agregado).

Cada gasto de la ENGHo (codigos COICOP de clase, grupo y division) se asigna al nodo mas especifico que
lo contiene: la clase o el grupo si estan publicados, o el resto del agregado publicado que los incluye.
Los rubros de la ENGHo que no estan en la canasta del IPC (p. ej. 06.3 Servicios hospitalarios) caen en
el resto de su division.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import fuentes

UMBRAL_RESTO = 0.002
SUFIJO_RESTO = '.r'
# Codigos publicados cuyo ponderador figura con otro codigo en ponderadores_ipc (prepagas: grupo 06.4)
ALIAS_PONDERADOR = {'06.4.1': '06.4'}
DIVS = [f'{i:02d}' for i in range(1, 13)]
# Clases de la ENGHo que el IPC clasifica con otro codigo (comparando las descripciones del archivo de
# articulos de la ENGHo, engho2018_articulos.txt, con las de ponderadores_ipc). Siempre dentro de la
# misma division, para que las tablas por division coincidan con gc_01..gc_12.
CONCORDANCIA_ENGHO = {
    'A0444': '04.1.3',  # Gastos comunes (expensas), abonos de mantenimiento: en el IPC, 04.1.3 "Gastos
                        # comunes por la vivienda y/o cochera y otros gastos" (la ENGHo los pone en 04.4)
    'A0412': '04.1.1',  # Otros alquileres efectivos (vivienda secundaria, temporal, de otro hogar): alquiler
}


def codigo_engho(c: str) -> str:
    """Codigo de la ENGHo 2017/18 a codigo COICOP del IPC: 'A0411' -> '04.1.1', 'A04' -> '04'."""
    c = str(c).strip()
    d = c[1:3]
    return '.'.join([d] + list(c[3:]))


def codigos_ipc(clase: str, grupo: str, division: str) -> list[str]:
    """Codigos COICOP del IPC de un gasto de la ENGHo, del mas especifico al menos especifico, con la
    concordancia de CONCORDANCIA_ENGHO."""
    clase = str(clase).strip()
    if clase in CONCORDANCIA_ENGHO:
        c = CONCORDANCIA_ENGHO[clase]
        return [c] + ancestros(c)
    return [codigo_engho(clase), codigo_engho(grupo), codigo_engho(division)]


def ancestros(c: str) -> list[str]:
    """'06.4.1' -> ['06.4', '06'] (del mas cercano al mas lejano)."""
    p = c.split('.')
    return ['.'.join(p[:i]) for i in range(len(p) - 1, 0, -1)]


def hijos_publicados(p: str, publicados: set[str]) -> list[str]:
    """Descendientes publicados de p sin otro publicado en el medio (06 -> 06.1 y 06.4.1)."""
    out = []
    for c in publicados:
        if c.startswith(p + '.'):
            entre = [a for a in ancestros(c) if a.startswith(p + '.')]
            if not any(a in publicados for a in entre):
                out.append(c)
    return sorted(out)


@dataclass
class Estructura:
    """precios: periodo x (region, nodo), base dic-2016 = 100.
    nodos: una fila por (region, nodo) con descripcion, division, tipo, pond_region (fraccion del gasto
    de la region en el IPC oficial) y pond_oficial (fraccion del IPC nacional)."""
    precios: pd.DataFrame
    nodos: pd.DataFrame
    hojas: dict[str, set[str]] = field(default_factory=dict)
    agregados: dict[str, set[str]] = field(default_factory=dict)
    nombre: str = ''
    imputados: pd.DataFrame = field(default_factory=pd.DataFrame)

    def asignar(self, region: str, codigos: list[str]) -> str:
        """Nodo de un gasto, dados sus codigos COICOP del mas especifico al menos especifico."""
        for c in codigos:
            if c in self.hojas[region]:
                return c
            if c in self.agregados[region]:
                return c + SUFIJO_RESTO
        raise KeyError(f'{region}: sin nodo para {codigos}')

    def pond_oficial(self) -> pd.Series:
        return self.nodos.set_index(['region', 'nodo'])['pond_oficial']

    def regiones(self) -> list[str]:
        return list(dict.fromkeys(self.nodos['region']))


def completar_huecos(P: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Meses sin indice publicado de una apertura (en GBA, prendas y restaurantes durante el aislamiento
    de 2020): se completan con la variacion mensual del agregado publicado que la contiene. Cuando la
    serie vuelve a publicarse, retoma su nivel oficial."""
    P = P.copy()
    imputados = []
    for c in sorted(P.columns[P.isna().any()], key=lambda x: x.count('.')):
        padre = next(a for a in ancestros(c) if a in P.columns)
        s, ps = P[c].values.copy(), P[padre].values
        meses = []
        for t in range(1, len(s)):
            if np.isnan(s[t]):
                s[t] = s[t - 1] * ps[t] / ps[t - 1]
                meses.append(str(P.index[t]))
        P[c] = s
        imputados.append({'codigo': c, 'con_variacion_de': padre, 'meses': ', '.join(meses)})
    return P, imputados


def construir(aperturas: pd.DataFrame, ponderadores: pd.DataFrame, resto: str = 'derivado',
              umbral: float = UMBRAL_RESTO) -> Estructura:
    """Estructura por aperturas regionales. resto='derivado' (indices de los restos deducidos de las
    ponderaciones oficiales) o 'agregado' (todos los restos con el indice de su agregado: sensibilidad)."""
    cols, filas, hojas_r, agreg_r, imp = {}, [], {}, {}, []
    for r in fuentes.REGIONES:
        a = aperturas[aperturas['region'] == r]
        P = a.pivot(index='periodo', columns='codigo', values='indice').sort_index()
        if P.iloc[0].isna().any() or P['0'].isna().any():
            raise ValueError(f'{r}: falta el nivel general o la base de alguna apertura')
        P, faltantes = completar_huecos(P)
        imp += [{'region': r, **f} for f in faltantes]
        desc = a.drop_duplicates('codigo').set_index('codigo')['descripcion']
        pub = set(P.columns) - {'0'}
        hojas = {c for c in pub if not any(o.startswith(c + '.') for o in pub)}
        agreg = pub - hojas
        hojas_r[r], agreg_r[r] = hojas, agreg

        def W(c):
            return float(ponderadores.loc[ALIAS_PONDERADOR.get(c, c), r])

        for c in sorted(hojas):
            cols[(r, c)] = P[c]
            filas.append({'region': r, 'nodo': c, 'descripcion': desc[c], 'tipo': 'publicado', 'pond_region': W(c)})
        for p in sorted(agreg):
            hijos = hijos_publicados(p, pub)
            w_resto = W(p) - sum(W(c) for c in hijos)
            if resto == 'derivado' and w_resto >= umbral:
                serie = (W(p) * P[p] - sum(W(c) * P[c] for c in hijos)) / w_resto
                if (serie <= 0).any():
                    raise ValueError(f'{r} {p}: indice del resto no positivo')
                tipo = 'resto derivado'
            else:
                serie, tipo = P[p], 'resto = indice del agregado'
            cols[(r, p + SUFIJO_RESTO)] = serie
            filas.append({'region': r, 'nodo': p + SUFIJO_RESTO, 'descripcion': f'Resto de {desc[p]}',
                          'tipo': tipo, 'pond_region': max(w_resto, 0.0)})
    nodos = pd.DataFrame(filas)
    nodos['division'] = nodos['nodo'].str[:2]
    # Ponderacion en el IPC nacional; se normaliza porque las ponderaciones publicadas estan redondeadas
    # (las regionales suman 1,001)
    nodos['pond_oficial'] = nodos['pond_region'] * nodos['region'].map(fuentes.POND_REGIONES)
    nodos['pond_oficial'] /= nodos['pond_oficial'].sum()
    precios = pd.DataFrame(cols)
    precios.columns = pd.MultiIndex.from_tuples(precios.columns, names=['region', 'nodo'])
    precios = precios[list(zip(nodos['region'], nodos['nodo']))]
    return Estructura(precios, nodos, hojas_r, agreg_r, nombre=f'aperturas (resto {resto})',
                      imputados=pd.DataFrame(imp, columns=['region', 'codigo', 'con_variacion_de', 'meses']))


def construir_divisiones(ipc_divisiones: pd.DataFrame, ponderadores: pd.DataFrame | None = None,
                         pond_nacional: pd.Series | None = None, regional: bool = False) -> Estructura:
    """Estructura de 12 divisiones: nacional (una sola canasta, como el metodo anterior) o regional."""
    regiones = fuentes.REGIONES if regional else ['Nacional']
    cols, filas = {}, []
    for r in regiones:
        P = fuentes.matriz_indices(ipc_divisiones, r)
        for d in DIVS:
            cols[(r, d)] = P[d]
            if regional:
                w = float(ponderadores.loc[d, r])
                po = w * fuentes.POND_REGIONES[r]
            else:
                w = po = float(pond_nacional[d]) if pond_nacional is not None else np.nan
            filas.append({'region': r, 'nodo': d, 'descripcion': d, 'tipo': 'publicado', 'pond_region': w,
                          'pond_oficial': po})
    nodos = pd.DataFrame(filas)
    nodos['division'] = nodos['nodo']
    nodos['pond_oficial'] /= nodos['pond_oficial'].sum()
    precios = pd.DataFrame(cols)
    precios.columns = pd.MultiIndex.from_tuples(precios.columns, names=['region', 'nodo'])
    return Estructura(precios, nodos, {r: set(DIVS) for r in regiones}, {r: set() for r in regiones},
                      nombre='divisiones regionales' if regional else 'divisiones nacionales')


def residuos(est: Estructura) -> pd.DataFrame:
    """Indices de los restos derivados (para revisar y exportar)."""
    n = est.nodos[est.nodos['tipo'] == 'resto derivado']
    t = est.precios[list(zip(n['region'], n['nodo']))].copy()
    t.columns = [f'{r} {c}' for r, c in t.columns]
    return t


def sensibilidad_redondeo(aperturas: pd.DataFrame, ponderadores: pd.DataFrame, n: int = 200,
                          semilla: int = 0) -> pd.DataFrame:
    """Dispersion del ultimo nivel de cada resto derivado si las ponderaciones oficiales tuvieran un
    error de redondeo uniforme en +-0,00005 (medio digito del 4to decimal)."""
    base = construir(aperturas, ponderadores)
    der = base.nodos[base.nodos['tipo'] == 'resto derivado'].reset_index(drop=True)
    rng = np.random.default_rng(semilla)
    ult = aperturas[aperturas['periodo'] == aperturas['periodo'].max()]
    disp = []
    for _, f in der.iterrows():
        r, p = f['region'], f['nodo'][:-len(SUFIJO_RESTO)]
        lvl = ult[ult['region'] == r].set_index('codigo')['indice']
        hijos = hijos_publicados(p, set(lvl.index) - {'0'})
        cods = [p] + hijos
        w = np.array([float(ponderadores.loc[ALIAS_PONDERADOR.get(c, c), r]) for c in cods])
        wp = w + rng.uniform(-5e-5, 5e-5, size=(n, len(cods)))
        niv = lvl[cods].values
        res = (wp[:, 0] * niv[0] - wp[:, 1:] @ niv[1:]) / (wp[:, 0] - wp[:, 1:].sum(axis=1))
        disp.append((np.percentile(res, 95) - np.percentile(res, 5)) / np.median(res) * 100)
    t = der[['region', 'nodo', 'descripcion', 'pond_region']].copy()
    t['ultimo_nivel'] = base.precios[list(zip(der['region'], der['nodo']))].iloc[-1].values
    t['dispersion_p5_p95_%'] = disp
    return t
