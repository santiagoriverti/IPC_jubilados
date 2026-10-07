# Memoria del proyecto IPC_jubilados

## Origen
TP de INECO-UADE (Grupo 2, 2026; el usuario es uno de los profesores) que construyó un "Índice
de Inflación de Jubilados y Pensionados". El usuario pidió tomarlo como base y mejorarlo. Archivos
originales en `Downloads` del usuario (PDF, PPTX, XLSX): NO se versionan (repo público, datos de alumnos).

## Sesión 1 — 2026-10-06
- Revisión completa del TP: canasta replicable desde microdatos ENGHo (hogares con mayores de 65,
  mezcla 0,69/0,31). Errores: feb-2024 sin Vivienda, corrección 3,84% duplicada, proyección "IPC"
  que usa IIJP, costo incremental vs total mezclados, PPA con fechas mezcladas. Método: ponderaciones
  fijas sobre variaciones (no canasta fija), no separa edad de canasta vieja (IPC = ENGHo 2004/05).
- Armado del repo: src/ (fuentes, ponderaciones, indices, haberes, fiscal, pipeline, graficos),
  scripts/ (construir, control_calidad, gen_notebooks), 3 notebooks Colab, tests (7), docs/revision_TP.md.
- Hallazgos: brecha nov-23 → may-26 2,39% (TP 3,84%); efecto edad desde nov-23 −0,69% (la brecha es
  por la canasta vieja del IPC); brecha cambia de signo por gobierno; haber sin bono +10% real vs
  nov-23 y con bono −10% (bono congelado); IIJP desde abr-24 → haber +0,8%; costo ~0,01% PIB/año.
- Corrida en Colab del usuario: los 3 notebooks andan; ZIP del NB03 = corrida local (hoja por hoja).
  Su salida mostró que ANSES usa el IPC(t−2) con 2 decimales (desde niveles), no el publicado a 1
  decimal: corregido (`pipeline.var_movilidad`, tolerancia del control 0,005 p.p.).
- Decisiones propias (revisables): población de referencia = hogares con jubilación/pensión ≥ 50%
  del ingreso; ponderaciones plutocráticas; precio de referencia de la canasta = promedio nov-17/nov-18.
