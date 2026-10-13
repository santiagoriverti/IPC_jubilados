"""Los .tex de docs/divulgacion usan exactamente las figuras que exporta el codigo (carpeta figuras/)."""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src import graficos  # noqa: E402

TEX = sorted((RAIZ / 'docs' / 'divulgacion').glob('*.tex'))
# \includegraphics[...]{figuras/x.png} y el macro de la presentacion \figura[...]{x.png}
PATRONES = [r'\\includegraphics(?:\[[^\]]*\])?\{figuras/([\w-]+)\.png\}', r'\\figura(?:\[[^\]]*\])?\{([\w-]+)\.png\}']


def _figuras(tex: Path) -> set[str]:
    texto = '\n'.join(l for l in tex.read_text(encoding='utf-8').splitlines() if not l.lstrip().startswith('%'))
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
