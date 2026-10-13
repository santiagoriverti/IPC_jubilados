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

## Sesión 2 — 2026-10-13 (rediseño metodológico)
- ZIPs de Colab de NB01/02/03 con 55e87c2 = local (0 diferencias no esperadas): verificación de la
  versión anterior cerrada.
- Revisión "de expertos" pedida por el usuario. Hallazgo principal: las 12 divisiones heredan la
  composición interna de 2004/05 (medicamentos vs prepagas, alquiler vs servicios, transporte público vs
  vehículo) y subestiman la brecha. El efecto edad de Milei (−0,7%) no era robusto. Las estimaciones
  públicas del "IPC con canasta 2017/18" usan ponderaciones fijas sobre variaciones (González-Rozada
  2024 +7,4% se replica exacto): el Lowe del repo es el método correcto.
- El usuario aclaró el objetivo: un IPC de jubilados profesional; el TP es solo la idea. Pidió
  implementar: (1) índice por aperturas regionales, (2) tabla de variantes, (3) subíndice haber mínimo.
- Implementado:
  - `src/estructura.py`: nodos por región (aperturas publicadas + restos `.r` deducidos de las
    ponderaciones oficiales `ponderadores_ipc.xls` del INDEC, encontrado en la página del IPC; umbral
    0,002; huecos de 2020 completados con el agregado). Réplica del IPC nacional 0,081%.
  - `src/ponderaciones.py`: gasto por hogar y nodo desde el archivo de gastos (100% asignado),
    poblaciones nuevas (haber mínimo ≤ 1,1 mínimos del trimestre; 10 variantes de definición).
  - `src/variantes.py`: 19 variantes (detalle, población, ponderación, fórmula, precios de referencia),
    resumen de firmeza. `src/indices.py` genérico (Lowe, Young, geométrico, descomposición por nodo).
  - Pipeline: niveles nacionales y regionales, bootstrap sobre la matriz de gasto, descomposición por
    división y por apertura, haber real y contrafactual con IIJP haber mínimo, bloque `revision_tp`.
  - Gráficos g07 (regiones) y g08 (variantes); notebooks regenerados sin cifras fijas en el markdown.
- Resultado: Milei IIJP vs IPC +3,78% (antes 2,71%); completo +2,29% (antes 1,32%); efecto edad
  completo +2,01% (firme), Milei −0,40% (no firme); haber mínimo Milei +4,97%; haber por IIJP +1,95% en
  sep-26; costo ~0,07-0,08% PIB/año.
- Verificado local: 13 tests, control 0 ALERTAS, notebooks en `_local_run` = construir.py.
- A pedido del usuario se actualizaron todos los .md (README reescrito con la metodología y cifras
  nuevas; revision_TP con las cifras del IIJP vigente, M1b nuevo sobre las 12 divisiones) y se hizo
  commit + push. Solo `seccion_iijp.tex` queda desactualizada (aviso en la cabecera). Falta: Colab.
