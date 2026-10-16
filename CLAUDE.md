# CLAUDE.md — instrucciones para sesiones de Claude en este repo

## Al empezar

1. `git pull` antes de cualquier cambio (el usuario trabaja desde más de una PC).
2. Leer **`ESTADO.md`** (estado, cifras vigentes, dónde se citan, próximos pasos, rutina, PC nueva).
3. Si hay que tocar cálculos: leer **`CONTEXTO.md`** (definiciones, decisiones, fuentes, trampas).
4. Historial de sesiones: `.claude/memory/project.md`.

## Reglas del usuario

- **Objetivo**: un índice de precios de jubilados (IPC jubilados) profesional y coherente que muestre la
  evolución de la canasta de consumo de los jubilados en Argentina. El TP de los alumnos es solo el
  origen de la idea: si una metodología mejor es posible, se cambia (sesión 2: aperturas regionales).
  Primero el procesamiento y la metodología; la redacción del informe (sección LaTeX) va después.
- **Commits solo con el usuario (Santiago Riverti). NUNCA agregar `Co-Authored-By: Claude`** ni
  ninguna atribución a Claude en commits o PRs. Commit/push solo cuando el usuario lo pide.
- Idioma: español (rioplatense) en respuestas, commits y documentación.
- El usuario corre los notebooks en **Google Colab** (cada notebook clona el repo desde GitHub: un
  cambio no llega a Colab hasta que se pushea).
- **Cada notebook termina descargando un ZIP con todo** (Excel, `graficos/`, `figuras/`, CSV y
  LEEME.txt), vía `src.exportar.zip_resultados` (celdas de `descarga()` en `gen_notebooks.py`). Escribe
  en `_descargas/` (ignorado); no toca `data/processed` ni `output/`, que solo actualiza `construir.py`.
  `figuras/` = las figuras de `graficos.GRAFICOS_DIVULGACION`, con los nombres que usan los `.tex` de
  `docs/divulgacion/`: el usuario la sube tal cual a la carpeta `figuras` de Overleaf. Una figura nueva
  para esos documentos va en ese diccionario (el test `tests/test_divulgacion.py` verifica que cada
  `\includegraphics` tenga su figura y al revés).
- El ZIP del notebook 03 trae además `fuentes_originales/` (`exportar.FUENTES_ORIGINALES` y
  `copiar_fuentes_originales`: CSV, XLS, ZIP y PDF tal como se publican, con su URL en un LEEME.txt; si uno
  no se puede bajar se anota y no corta). Un dato de entrada nuevo va también en esa lista.
- El notebook 03 además descarga `IIJP_resultados_y_datos_originales.xlsx` (`exportar.excel_completo`:
  hojas de resultados + hojas `Dato_*` de `exportar.datos_originales()`, hoja `Indice` con las fuentes; ~30 MB,
  ~2 min). Un dato de entrada nuevo en `fuentes.py` va también en `datos_originales()`.
- Cuando el usuario pasa ZIPs de Colab: `python scripts/construir.py` (si cambió algo) y
  `python scripts/comparar_zip.py <zips>`. Esperable: diferencias solo en bootstrap y Notas.
- El repo es **público**: los archivos del TP original (PDF, PPTX, XLSX con nombres y legajos de los
  alumnos) **no se versionan**. Si hacen falta, van en `docs/tp_original/` (ignorado por git).
  Solo se versionan las series numéricas en `data/reference/tp_original_series.csv`.
- `docs/revision_TP.md` cita celdas de la planilla original y cifras corregidas;
  `docs/informe_indicadores/seccion_iijp.tex` es la sección del informe INECO "Propuesta de Indicadores
  Económicos" (el documento completo está en el Overleaf del usuario, con la figura en `figuras/`);
  `docs/divulgacion/` tiene el documento de prensa y la presentación Beamer (tema Madrid) para público
  no técnico: lenguaje simple, coma decimal, sin intervalos de confianza (la firmeza se dice con las
  variantes). Se entregan como código para copiar y pegar en Overleaf; antes, compilarlos con pdfLaTeX
  (MiKTeX en la PC) y revisar 0 errores, 0 advertencias y 0 cajas desbordadas.
  Si cambian las cifras, actualizar todos los documentos de la tabla de `ESTADO.md` §3.

## Reglas técnicas que muerden

- Windows: correr Python con `PYTHONUTF8=1`.
- **Los `.ipynb` se generan con `python scripts/gen_notebooks.py`**: no editarlos a mano ni con
  NotebookEdit. Cambiar el script y regenerar. Se versionan sin outputs.
- **No escribir scripts ni ediciones con heredocs de bash** (rompen `\\` y `\n`). Usar las
  herramientas de archivos o un `.py` aparte.
- Para probar notebooks sin ensuciar los del repo: copiarlos a `_local_run/` (ignorado), bajar
  `N_BOOTSTRAP` con sed y ejecutar con `python -m jupyter nbconvert --to notebook --execute --inplace`.
- **Colab reutiliza sesiones**: el usuario suele volver a correr un notebook en una sesión vieja. La
  celda de configuración hace `git fetch --depth 1` + `git reset --hard FETCH_HEAD` (un `git pull`
  falla si la copia tiene cambios) y borra `src.*` de `sys.modules` (si no, Python usa el código viejo
  ya importado: pasó el 2026-10-06, ZIPs con haberes viejos). Imprime "Version del repo"; el ZIP la
  trae en `LEEME.txt` y en la hoja Notas: chequearla al comparar un ZIP de Colab.
- Cifras citadas (README, revision_TP, seccion_iijp.tex, ESTADO) = las que imprimen `construir.py` /
  `control_calidad.py` (ver ESTADO §2-§3).
- Antes de commitear resultados nuevos: `python scripts/control_calidad.py` (0 ALERTAS) y
  `python -m pytest tests -q`.
- `data/cache/` guarda las descargas (ignorado). `--refrescar` en construir.py baja todo de nuevo.
- El costo fiscal lee la IMIG de `cuentas_publicas` (repo hermano en disco o GitHub raw): actualizar
  ese repo primero.
- La regla de movilidad usa el IPC(t−2) **desde niveles con 2 decimales** (`haberes.var_movilidad`),
  no el publicado a 1 decimal. Tolerancia del control: 0,005 p.p.
- **Estructura de precios** (`src/estructura.py`): el IIJP se valoriza con las aperturas regionales del
  IPC (`serie_ipc_aperturas.csv`, no hay aperturas nacionales) y restos deducidos de las ponderaciones
  oficiales (`data/reference/ponderadores_ipc_regiones.csv`, copia del `ponderadores_ipc.xls` del INDEC:
  no editar a mano). Si el INDEC agrega o quita aperturas, la estructura se rearma sola; revisar el
  control de calidad (réplica del IPC < 0,2%, restos estables, 100% del gasto asignado) y la hoja
  Imputaciones (huecos completados con la variación del agregado).
- Toda decisión metodológica nueva entra como variante en `src/variantes.py` (cambia una sola cosa
  respecto de la principal); una conclusión es firme si mantiene el signo en todas.

## Cierre de sesión

Actualizar `ESTADO.md` (fecha, cobertura, cifras, verificación, próximos pasos) y
`.claude/memory/project.md`. Commit + push si el usuario lo pide (si el push pide credenciales, lo
hace el usuario: Claude no ingresa tokens).
