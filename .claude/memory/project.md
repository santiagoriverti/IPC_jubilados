# Memoria del proyecto IPC_jubilados

## Origen
TP de INECO-UADE (Grupo 2, 2026; el usuario es uno de los profesores) que construyó un "Índice
de Inflación de Jubilados y Pensionados". El usuario pidió tomarlo como base y mejorarlo. Archivos
originales en `Downloads` del usuario (`TPINECO_GRUPO 2 (1).pdf`, `TP INECO-INDICES DE PRECIOS.pptx`,
`TP INECO (1).xlsx`): NO se versionan (repo público, datos de alumnos).

## Sesión 1 — 2026-10-06 (commits 57e3823 → ea4ffc3 → cierre)
- Revisión completa del TP: canasta replicable desde microdatos ENGHo (hogares con mayores de 65,
  mezcla 0,69/0,31). Errores: feb-2024 sin Vivienda, corrección 3,84% duplicada, proyección "IPC"
  que usa IIJP, costo incremental vs total mezclados, PPA con fechas mezcladas. Método: ponderaciones
  fijas sobre variaciones (no canasta fija), no separa edad de canasta vieja (IPC = ENGHo 2004/05).
  Todo en `docs/revision_TP.md`.
- Armado del repo: src/ (fuentes, ponderaciones, indices, haberes, fiscal, pipeline, graficos,
  exportar), scripts/ (construir, control_calidad, gen_notebooks, comparar_zip), 3 notebooks Colab,
  7 tests.
- Hallazgos: brecha nov-23 → may-26 2,39% (TP 3,84%); efecto edad desde nov-23 −0,69% (la brecha es
  por la canasta vieja del IPC); brecha cambia de signo por gobierno; haber sin bono +10% real vs
  nov-23 y con bono −10% (bono congelado); IIJP desde abr-24 → haber +0,77%; costo ~0,01% PIB/año.
  De la "pérdida del 19%" del TP, 19,3 de 22,3 p.p. son la transición de fórmula; el índice, 2,5%.
- Corridas del usuario en Colab:
  1. Primera: los 3 notebooks andan; ZIP del NB03 = local. Su salida mostró que ANSES usa el IPC(t−2)
     con 2 decimales desde niveles: corregido (`pipeline.var_movilidad`, tolerancia 0,005 p.p.).
  2. Pidió que **cada notebook descargue un ZIP con todo** (Excel + PNG + CSV): `src/exportar.py`,
     escribe en `_descargas/`.
  3. Al re-correr en sesiones viejas: NB03 falló en `git pull` (copia con cambios del NB03 viejo) y
     NB01/NB02 usaron `src.pipeline` viejo en memoria (ZIPs con haberes de 1 decimal). Corregido en la
     celda de configuración (fetch + reset --hard, purga de `src.*`, imprime versión; el ZIP la trae).
  4. NB03 con `ea4ffc3`: ZIP = local (0 diferencias no esperadas). NB01/NB02: falta re-correrlos.
- Escribí la sección LaTeX del IIJP para el documento INECO "Propuesta de Indicadores Económicos"
  (Overleaf del usuario; figura `figuras/g01_ponderaciones.png`): guardada en
  `docs/informe_indicadores/seccion_iijp.tex` con los `\bibitem` nuevos.
- Decisiones propias (revisables): población de referencia = hogares con jubilación/pensión ≥ 50%
  del ingreso; ponderaciones plutocráticas; precio de referencia de la canasta = promedio nov-17/nov-18;
  sigla IIJP (el informe titula "Índice de Precios de Jubilados Argentinos").
- Pendientes / ideas: ver ESTADO.md §5.
