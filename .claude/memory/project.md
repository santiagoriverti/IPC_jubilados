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
- Colab con `7c770cf`: los 3 notebooks fallaron (ZeroDivisionError, "haber minimo 0"). Causa: la API de
  datos.gob.ar devolvía vacía la serie del haber (intermitente; en la PC andaba por la caché del 06-10).
  Arreglo: `serie_datos_gob` con reintentos y respaldo al CSV de la distribución, caché vacío se vuelve a
  bajar, validaciones que cortan si el haber no cubre la ENGHo o una población queda vacía. Probado con
  una copia del repo sin caché (simula Colab): mismas cifras.
- Colab con `6e7aab1`: los 3 ZIP = local. Segunda revisión "de expertos":
  - **Error de concordancia ENGHo → IPC**: la ENGHo clasifica las expensas en `A0444` (04.4, con el
    agua) y el IPC en 04.1.3 (gastos comunes). Se valorizaban con el índice derivado del agua (GBA 14.256
    vs 6.017 de gastos comunes). Corregido con `estructura.CONCORDANCIA_ENGHO` (también `A0412` otros
    alquileres → 04.1.1), encontrado comparando `engho2018_articulos.zip` con ponderadores_ipc.
    Cambio: completo 2,29 → 1,20%; Milei 3,78 → 3,06%; edad completo 2,01 → 1,60; haber sep-26 +1,95 →
    +1,10%; costo 1,2-1,4% → 0,2-0,6% del gasto previsional.
  - Agregado: variante geométrica vs IPC oficial geométrico; variante comparador = no jubilados;
    intervalos regionales; IC pareado haber mínimo vs IIJP (+2,6% completo, +1,5% Milei, significativo);
    sensibilidad del tope del haber mínimo (1-2 mínimos: resultado estable); cobertura de precios
    (83/16,5/0,5%). Ahora la brecha del período completo NO es firme; el efecto edad completo sí, pero
    viene de 2016-2019.
- Commit `b419fa3` pusheado; Colab con `b419fa3`: los 3 ZIP = local (0 diferencias no esperadas).
  Proyecto verificado de punta a punta. Próximo paso: sección LaTeX del informe INECO.

## Sesión 3 (2026-10-13): divulgación
- Pedido del usuario: documento LaTeX "para prensa", sencillo (se irán agregando detalles), y una
  presentación Beamer estilo Madrid para autoridades de la Facultad (público no técnico). Código para
  copiar y pegar en Overleaf; las figuras las sube él a la carpeta `figuras/`.
- `docs/divulgacion/iijp_prensa.tex` (8 páginas) y `docs/divulgacion/iijp_presentacion.tex` (15
  diapositivas, 16:9). Compilan con pdfLaTeX (MiKTeX) sin errores, advertencias ni cajas desbordadas.
  Prueba local en `_local_run/divulgacion/` (copia de los .tex + `figuras/`).
- Figuras nuevas `iijp_01..06` en `src/graficos.py` (`GRAFICOS_DIVULGACION`, aparte de `GRAFICOS`):
  se exportan a `output/figuras/` y a la carpeta `figuras/` del ZIP de cada notebook (el usuario la sube
  tal cual a Overleaf); cada notebook las muestra antes de la descarga (`figuras_divulgacion()` en
  gen_notebooks). Sin título, letra grande, coma decimal, meses "ene-24". `comparar_zip.py` verifica que
  el ZIP traiga todos los PNG; `tests/test_divulgacion.py`, que los .tex usen justo esas figuras. El
  g04 ahora dice "vs IPC oficial replicado" (3,02 vs 3,06 publicado). `iijp_04` reparte la brecha contra la RÉPLICA del IPC (suma 3,02, no 3,06):
  el epígrafe lo aclara.
- Mensaje honesto en ambos: la brecha desde nov-23 (+3,1%) se debe sobre todo a la canasta vieja del
  IPC (con la canasta de todos los hogares da +3,8%); la de todo el período (+1,2%) no es firme.
- Trampas LaTeX: babel spanish pone espacio antes de % → `\spanishplainpercent`; viñetas cuadradas →
  `es-nolists`; `\text` sin amsmath → `\mathrm`; en Madrid, `\institute[]` evita "(UADE)" en el pie.
- Corregido redondeo doble en README (+4,6 → +4,5% haber mínimo Milei; +1,5 → +1,4% vs IIJP) y en
  revision_TP M3 (dic-23 → nov-23; 4,6 → 4,5%).

## Sesión 4 (2026-10-16): Excel con datos originales
- Pedido: al terminar el notebook 03, descargar un Excel con todos los resultados y los datos originales.
- `exportar.datos_originales()` (IPC divisiones y aperturas, ponderaciones IPC = ENGHo 2004/05, peso de
  regiones, ENGHo 2017/18 hogares/personas/gastos solo con las columnas que usa el cálculo, haber, bono,
  IMIG, PIB, series del TP) y `exportar.excel_completo(R, nombre)` → `_descargas/<nombre>.xlsx`, hoja Indice
  con fuentes. 30 MB, ~2 min con openpyxl (gastos: 901.804 filas, entra en el límite de Excel).
- La ENGHo 2004/05 no tiene microdatos en el análisis: entra solo vía ponderaciones oficiales del IPC.
- Pendiente: probar en Colab (dos files.download seguidos: el navegador puede pedir permiso).
- ZIP del notebook 03 con `fuentes_originales/` (`exportar.FUENTES_ORIGINALES`): archivos tal como
  se publican, bajados a data/cache/originales si no estaban; IMIG original = imig-mensual.csv de datos.gob.ar
  (dataset 452) + imig_consolidado.csv de cuentas_publicas. ZIP 17,7 MB.
- Rutina mensual sep-2026: cifras actualizadas en ESTADO, README, revision_TP, prensa y presentación (sin
  cambios de conclusiones: Milei +3,06%, completo +1,21%, edad completo +1,69%, haber mínimo vs IPC +4,0%).
  Las cifras se sacaron con un script que compara los CSV de HEAD con los nuevos (scratchpad, no versionado).
  Plantilla de prensa INECO: logo en `_local_run/prensa_ineco/figuras/logo_ineco.jpg` (no versionado).

## Sesión 5 (2026-10-19): brecha anual y figuras de divulgación
- Pedido del usuario sobre el documento de prensa: brecha anual, figura 3 más larga, gráficos de inflación anual
  (datos anuales) y mensual, y evitar gráficos que empiecen en fechas políticas (cambios de gobierno).
- Hecho: tabla_anual y brecha_interanual en indices.py; iijp_03 = brecha de 12 meses desde dic-17; iijp_06 base
  dic-2016 (con y sin bono); iijp_07 barras anuales con la brecha de cada año; iijp_08 mensual (completa + 24 meses).
- Bono previsional cargado desde sep-2022 (antes solo bonos de pago único, no cargados).
- Criterio del usuario: los gráficos no arrancan en nov-23 ni en otra fecha de cambio de gobierno (el texto sí
  puede citar esos períodos).
