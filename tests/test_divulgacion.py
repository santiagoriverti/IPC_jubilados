"""Los .tex de docs/divulgacion usan exactamente las figuras que exporta el codigo (carpeta figuras/) y
citan solo entradas que existen en docs/divulgacion/bibliografia.bib."""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import graficos  # noqa: E402

DIR = RAIZ / 'docs' / 'divulgacion'
TEX = sorted(DIR.glob('*.tex'))
# \includegraphics[...]{figuras/x.png} o {x.png} (con \graphicspath) y el macro de la presentacion
# \figura[...]{x.png}. El logo de la plantilla (.jpg) no lo genera el codigo.
PATRONES = [r'\\includegraphics(?:\[[^\]]*\])?\{(?:figuras/)?([\w-]+)\.png\}', r'\\figura(?:\[[^\]]*\])?\{([\w-]+)\.png\}']


def _sin_comentarios(tex: Path) -> str:
    return '\n'.join(re.sub(r'(?<!\\)%.*', '', l) for l in tex.read_text(encoding='utf-8').splitlines())


def _figuras(tex: Path) -> set[str]:
    texto = _sin_comentarios(tex)
    return {m for p in PATRONES for m in re.findall(p, texto)}


def test_hay_documentos():
    assert {t.name for t in TEX} >= {'iijp_prensa.tex', 'iijp_presentacion.tex'}


@pytest.mark.parametrize('tex', TEX, ids=lambda t: t.name)
def test_figuras_exportadas(tex):
    usadas = _figuras(tex)
    assert usadas, f'{tex.name} no usa figuras'
    assert usadas <= set(graficos.GRAFICOS_DIVULGACION), sorted(usadas - set(graficos.GRAFICOS_DIVULGACION))


def test_todas_las_figuras_se_usan():
    usadas = set().union(*(_figuras(t) for t in TEX))
    assert set(graficos.GRAFICOS_DIVULGACION) <= usadas


def test_citas_en_bibliografia():
    claves = set(re.findall(r'^@\w+\{([^,\s]+),', (DIR / 'bibliografia.bib').read_text(encoding='utf-8'), re.M))
    citadas = set()
    for t in TEX:
        for grupo in re.findall(r'\\cite\w*(?:\[[^\]]*\])*\{([^}]+)\}', _sin_comentarios(t)):
            citadas |= {c.strip() for c in grupo.split(',')}
    assert citadas, 'el informe de prensa deberia citar la bibliografia'
    assert citadas <= claves, sorted(citadas - claves)
