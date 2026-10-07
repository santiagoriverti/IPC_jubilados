# CLAUDE.md — instrucciones para sesiones de Claude en este repo

## Al empezar

1. `git pull` antes de cualquier cambio (el usuario trabaja desde más de una PC).
2. Leer **`ESTADO.md`** (estado, próximos pasos, rutina mensual, PC nueva).
3. Si hay que tocar cálculos: leer **`CONTEXTO.md`** (definiciones, fuentes, trampas).
4. Historial de sesiones: `.claude/memory/project.md`.

## Reglas del usuario

- **Commits solo con el usuario (Santiago Riverti). NUNCA agregar `Co-Authored-By: Claude`** ni
  ninguna atribución a Claude en commits o PRs.
- Idioma: español (rioplatense) en respuestas, commits y documentación.
- El usuario corre los notebooks en **Google Colab** (cada notebook clona el repo).
- El repo es **público**: los archivos del TP original (PDF, PPTX, XLSX con nombres y legajos de los
  alumnos) **no se versionan**. Si hacen falta, van en `docs/tp_original/` (ignorado por git).
  Solo se versionan las series numéricas en `data/reference/tp_original_series.csv`.
- La revisión del TP (`docs/revision_TP.md`) cita celdas de la planilla original: si cambian las
  cifras corregidas, actualizar esa tabla y el README.

## Reglas técnicas que muerden

- Windows: correr Python con `PYTHONUTF8=1`.
- **Los `.ipynb` se generan con `python scripts/gen_notebooks.py`**: no editarlos a mano ni con
  NotebookEdit. Cambiar el script y regenerar. Se versionan sin outputs.
- **No escribir scripts ni ediciones con heredocs de bash** (rompen `\\` y `\n`). Usar las
  herramientas de archivos o un `.py` aparte.
- Para probar notebooks sin ensuciar los del repo: copiarlos a `_local_run/` (ignorado) y ejecutar con
  `python -m jupyter nbconvert --to notebook --execute --inplace`.
- **Colab reutiliza sesiones**: el usuario suele volver a correr un notebook en una sesión vieja. La
  celda de configuración hace `git fetch --depth 1` + `git reset --hard FETCH_HEAD` (un `git pull`
  falla si la copia tiene cambios) y borra `src.*` de `sys.modules` (si no, Python usa el código viejo
  ya importado: pasó el 2026-10-06, ZIPs con haberes viejos). Imprime "Version del repo"; el ZIP la
  trae en `LEEME.txt` y en la hoja Notas: chequearla al comparar un ZIP de Colab.
- Pedido del usuario: **cada notebook termina descargando un ZIP con todo** (Excel, graficos PNG y CSV),
  vía `src.exportar.zip_resultados` (celdas de `descarga()` en gen_notebooks.py). Escribe en
  `_descargas/` (ignorado), no toca `data/processed` ni `output/`, que solo actualiza `construir.py`.
- Cifras citadas (README, revision_TP, ESTADO) = las que imprimen `construir.py` / `control_calidad.py`.
- Antes de commitear resultados nuevos: `python scripts/control_calidad.py` (0 ALERTAS) y
  `python -m pytest tests -q`.
- `data/cache/` guarda las descargas (ignorado). `--refrescar` en construir.py baja todo de nuevo.
- El costo fiscal lee la IMIG de `cuentas_publicas` (repo hermano en disco o GitHub raw): actualizar
  ese repo primero.

## Cierre de sesión

Actualizar `ESTADO.md` (fecha, cobertura, cifras, próximos pasos) y `.claude/memory/project.md`.
Commit + push (si el push pide credenciales, lo hace el usuario: Claude no ingresa tokens).
