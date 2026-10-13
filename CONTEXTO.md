# CONTEXTO — definiciones, decisiones, fuentes y trampas

## 1. Definiciones

- **IIJP** (índice de precios de jubilados y pensionados): índice de canasta fija (Lowe) con la
  estructura de gasto de los **hogares jubilados** de la ENGHo 2017/18, valorizada con el IPC del INDEC
  **por región y al nivel más desagregado publicado** (aperturas). Base dic-2016 = 100.
  IIJPₜ = Σᵣ Σₖ qᵣₖ Iᵣₖ,ₜ con qᵣₖ = gᵣₖ / Īᵣₖ: gᵣₖ = gasto expandido de los hogares jubilados de la región
  r en el nodo k; Īᵣₖ = promedio del índice del nodo durante el relevamiento (nov-2017 a nov-2018).
  Equivale a actualizar por precios las ponderaciones desde el período de la encuesta (Manual del IPC
  OIT/FMI; el INDEC hace lo mismo con la ENGHo 2004/05). Las regiones pesan según el gasto de sus
  hogares jubilados.
- **Nodos de la estructura de precios** (`src/estructura.py`), por región:
  - *hojas*: aperturas publicadas sin hijos publicados (p. ej. `04.5` Electricidad, gas y otros
    combustibles, `06.4.1` Prepagas, `07.3` Transporte público, `10` Educación);
  - *restos* (`<código>.r`): lo que los hijos publicados de un agregado no cubren (en Vivienda de GBA:
    `04.4` Suministro de agua). Índice del resto deducido de las ponderaciones oficiales (agregación de
    Laspeyres): I_resto = (W_p I_p − Σ W_c I_c) / (W_p − Σ W_c). Si W_resto < 0,002 del gasto regional
    (`UMBRAL_RESTO`), el redondeo de las ponderaciones lo vuelve inestable y se usa el índice del agregado.
  - 254 nodos en total (47 restos derivados). Cada gasto de la ENGHo (clase/grupo/división COICOP) va al
    nodo más específico que lo contiene, después de la concordancia ENGHo → IPC
    (`estructura.CONCORDANCIA_ENGHO`: expensas `A0444` → 04.1.3, otros alquileres `A0412` → 04.1.1);
    los rubros que no están en la canasta del IPC (p. ej. 06.3 hospitalarios, 12.4 geriátricos y
    residencias) caen en el resto de su división. Cobertura de la canasta de jubilados: 83% aperturas
    publicadas, 16,5% restos derivados, 0,5% índice del agregado (`R['cobertura_precios']`).
- **Hogar jubilado**: (Σ `ijubilacion` + Σ `ipensionesnc` de sus miembros) / `ingtoth` ≥ 0,5.
  `ijubilacion` = ingreso neto por jubilación o pensión (contributiva); `ipensionesnc` = pensiones no
  contributivas (discapacidad, graciables, veteranos). Criterio de fuente principal de ingreso, como los
  índices de hogares pensionados de la ONS (que usan 75%: está entre las variantes).
- **Haber mínimo** (`jub_minimo`, subíndice): hogares jubilados en los que ningún perceptor de
  jubilación o pensión cobra más de 1,1 haberes mínimos (el máximo vigente en el trimestre operativo de
  la entrevista; 1,1 cubre el descuento de PAMI y los aumentos dentro del trimestre). 2.081 hogares, 40%
  de los hogares jubilados expandidos. `h['max_haberes_minimos']` guarda el cociente de cada hogar y
  `ponderaciones.marcar_haber_minimo(h, tope)` permite otros topes (`R['sensibilidad_haber_minimo']`, de
  1 a 2 haberes mínimos).
- **IPC ENGHo 17/18**: el mismo cálculo con la canasta de todos los hogares. Separa:
  - *efecto edad* = IIJP vs IPC 17/18 (misma especificación);
  - *efecto canasta vieja* = IPC 17/18 vs IPC oficial (canasta ENGHo 2004/05).
- **Brecha** entre índices en un período: (1 + infl. A) / (1 + infl. B) − 1.
- **Ventanas**: `indices.acumulada(nivel, desde, hasta)` no incluye la inflación del mes `desde`.
  "Dic-23 → may-26" en la jerga del TP = `acumulada(nivel, '2023-11', '2026-05')`.
- **Períodos** (`indices.PERIODOS`): Completo (dic-16 → último), Macri (dic-16 → dic-19), Fernández
  (dic-19 → nov-23), Milei (nov-23 → último), Shock tarifario (nov-23 → dic-24), Desde 2025
  (dic-24 → último), Ventana del TP (nov-23 → may-26).
- **Descomposición** (`indices.descomposicion`): aporte = (ω_A − ω_B)(Rᵢ − R_B)/R_B con ponderaciones
  efectivas al inicio del período, por nodo; se suma por división y por apertura (sumando regiones).
- **Contrafactual de haberes**: misma regla de movilidad (IPC t−2 con 2 decimales) con el IIJP desde
  abr-2024 (`haber_cf_iijp`, `factor_iijp`) y con el IIJP haber mínimo (`haber_cf_iijp_minimo`).
  Ejercicio del TP desde dic-2023: `haber_cf_*_dic23`.
- **Costo fiscal**: (jubilaciones contributivas + PNC de la IMIG) × (factor IIJP − 1). Cota superior
  (incluye el bono, que no se indexa).
- **Método del TP**: Σ wᵢ πᵢ,t con ponderaciones fijas sobre variaciones mensuales publicadas. No es
  canasta fija; queda solo en el bloque `R['revision_tp']`. Es también lo que hacen varias estimaciones
  públicas del "IPC con canasta 2017/18" (la de González-Rozada para 2024, +7,4%, se replica exacta).

## 2. Decisiones metodológicas (sesión 2, 2026-10-13; revisables con el usuario)

- **Nivel de detalle**: aperturas regionales con restos derivados (antes: 12 divisiones nacionales). Las
  12 divisiones heredan la composición interna de 2004/05 de todos los hogares y subestiman la brecha
  (medicamentos vs prepagas, alquiler vs servicios, transporte público vs vehículo).
- **Población de referencia**: hogares jubilados (≥ 50% del ingreso). Incluye PNC (la movilidad también
  las actualiza); la mayoría de los perceptores de PNC tiene < 65 años. Variantes: sin PNC, umbral 75% y
  25%, jefe/a o cónyuge jubilado, jefe/a 65+, todos los adultos jubilados, con algún 65+, solo 65+,
  mitades de ingreso per cápita, haber mínimo.
- Ponderaciones plutocráticas (como el IPC); democráticas como variante.
- Precio de referencia de la canasta: promedio del relevamiento (nov-17/nov-18). Variante: gasto de
  cada hogar deflactado por el índice de su trimestre operativo (cambia ≤ 0,15 p.p.).
- Fórmula de Lowe. Variantes: Young (sin actualizar por precios relativos) y geométrica; la geométrica se
  compara con el IPC oficial recalculado con la misma fórmula (si no, la brecha mezcla canasta y fórmula).
- Comparador del efecto edad: todos los hogares (equivale a un IPC con canasta 2017/18). Variante: los
  hogares no jubilados (contraste puro; el efecto del período completo pasa de +1,6% a +1,9%).
- **Regla de firmeza**: una conclusión es firme si mantiene el signo en las 20 variantes
  (`R['variantes_resumen']`, gráfico g08).
- Bootstrap: 500 réplicas en `construir.py`, 300 en los notebooks (semilla 2018), remuestreo de hogares
  estratificado por región; da intervalos para la brecha nacional, el efecto edad, el haber mínimo (vs IPC
  y, pareado, vs IIJP) y las brechas regionales. Sin conglomerados (la ENGHo pública no trae UPM ni
  estrato): cota inferior.
- Test de brecha persistente: media de la diferencia mensual en logaritmos, error de Newey-West
  (rezagos = ⌊4 (T/100)^(2/9)⌋). Con períodos cortos, poca potencia.

## 3. Fuentes

| Dato | Origen | Función |
|---|---|---|
| IPC por división, nacional y regional | `indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv` (sep `;`, latin-1, coma decimal) | `fuentes.leer_ipc_divisiones` |
| IPC por aperturas, solo regional | `indec.gob.ar/ftp/cuadros/economia/serie_ipc_aperturas.csv` (mismo formato; columna `Descripcion_aperturas`) | `fuentes.leer_ipc_aperturas` |
| Ponderaciones oficiales por región (división, grupo, clase) | `data/reference/ponderadores_ipc_regiones.csv` ← INDEC `ponderadores_ipc.xls` | `fuentes.leer_ponderadores_ipc` |
| Peso de cada región en el IPC nacional | Metodología IPC 2019, cuadro 6 (GBA 0,447; Pampeana 0,342; NOA 0,069; NEA 0,045; Cuyo 0,052; Patagonia 0,046) | `fuentes.POND_REGIONES` |
| Ponderaciones nacionales por división | `data/reference/ponderaciones_ipc_indec.csv` | `ponderaciones.pond_ipc_oficial` |
| ENGHo 2017/18 | `indec.gob.ar/ftp/cuadros/menusuperior/engho/engho2018_{hogares,personas,gastos}.zip` (txt sep `\|`); manual: `engho2017_18_manual_uso_bases.pdf` | `fuentes.leer_engho` |
| Haber mínimo | datos.gob.ar `58.1_MP_0_M_24` | `fuentes.leer_haber_minimo` |
| Bono | manual, `data/reference/bono_previsional.csv` (decretos) | `fuentes.leer_bono` |
| IMIG (gasto previsional, resultados) | `cuentas_publicas/output/imig_consolidado.csv` (disco o GitHub raw) | `fuentes.imig_mensual` |
| PIB nominal | datos.gob.ar `4.4_OGP_2004_T_17` (trimestral **anualizado**: anual = suma/4) | `fuentes.leer_pib_anual` |
| Series del TP original | `data/reference/tp_original_series.csv` | `pipeline` (`R['revision_tp']`) |

## 4. Salidas

- `pipeline.calcular()` devuelve un dict `R`. Índices: `niveles` (IPC oficial, IPC ENGHo 17/18, IIJP,
  IIJP haber mínimo), `var_mensual`, `var_interanual`, `niveles_regionales` (IPC e IIJP de cada región).
  Brechas: `periodos`, `periodos_regionales`, `brecha_estadistica`, `bootstrap_brechas`,
  `banda_brecha_nov23`, `descomposicion` (por división) y `descomposicion_aperturas`
  (`nov23_ultimo`, `dic16_ultimo`). Canastas: `ponderaciones` (por división, todas las poblaciones),
  `ponderaciones_aperturas` (nacional por apertura, con participación dentro de la división),
  `ponderaciones_nodos` (región × nodo), `ponderaciones_democraticas`, `peso_regiones`, `poblaciones`.
  Estructura: `estructura` (nodos), `indices_residuales`, `sensibilidad_restos`, `imputaciones`,
  `validacion`, `cobertura_precios`. Sensibilidad: `variantes`, `variantes_resumen`, `variantes_niveles`,
  `sensibilidad_haber_minimo`; `periodos_regionales` trae los intervalos bootstrap. Haberes y fiscal:
  `haberes`, `regla_movilidad`, `fiscal_*`. TP: `revision_tp`. `meta`.
- `src/exportar.py`: `exportar(R, dir_salida, dir_datos)` (Excel con una hoja por tabla + 8 PNG + 29 CSV)
  y `zip_resultados(R, nombre)` (lo mismo + `LEEME.txt` en `_descargas/<nombre>.zip`; lo usan los
  notebooks). La hoja Notas y el LEEME traen el commit.
- Gráficos (`src/graficos.py`): g01 ponderaciones, g02 brecha desde nov-23 (banda bootstrap, haber mínimo,
  todos los hogares y método anterior), g03 brecha histórica y componentes, g04 descomposición, g05 haber
  real (IPC e IIJP haber mínimo), g06 costo fiscal, g07 regiones, g08 variantes.

## 5. Trampas conocidas

- **Concordancia ENGHo ≠ IPC**: la ENGHo 2017/18 clasifica las expensas en 04.4.4 (con el agua); el IPC,
  en 04.1.3 (gastos comunes). Sin la concordancia, las expensas (1,8% de la canasta de jubilados) se
  valorizaban con el índice del agua, que en GBA subió 2,4 veces más desde 2016: la brecha del período
  completo daba +2,3% en vez de +1,2%. Antes de agregar rubros, comparar las descripciones de
  `engho2018_articulos.zip` (INDEC, mismo FTP que la ENGHo) con las de `ponderadores_ipc_regiones.csv`.
- **Aperturas solo regionales**: no hay aperturas nacionales; el IIJP nacional se arma sumando regiones.
  GBA publica además `04.3` y `09.1`. Prepagas se publica como `06.4.1` pero su ponderador es `06.4`
  (`estructura.ALIAS_PONDERADOR`).
- **Huecos de 2020**: el INDEC no publicó `03.1`, `03.2` (abr-2020) ni `11.1` (abr-jul 2020) en ninguna
  región; se completan con la variación de su agregado (`estructura.completar_huecos`, hoja Imputaciones).
- **Ponderaciones redondeadas**: las regionales del IPC nacional suman 1,001 y las de algunas regiones
  0,9999/1,0001; `pond_oficial` se normaliza. Los restos con peso < 0,002 usan el índice del agregado;
  los derivados se mueven < 5% ante un error de redondeo de ±0,00005 (`sensibilidad_restos`).
- La réplica del IPC nacional con la estructura de aperturas tiene error ≤ 0,08% (regiones ≤ 0,26%). Las
  divisiones nacionales NO se reproducen sumando regiones en Educación (error 5%): por eso el IIJP no usa
  divisiones nacionales en la especificación principal.
- **Regiones ENGHo ≠ orden del IPC**: 1 GBA, 2 Pampeana, 3 Noroeste, 4 Noreste, 5 Cuyo, 6 Patagonia
  (`fuentes.REGIONES_ENGHO`).
- **Trimestre operativo** de la ENGHo: arranca en noviembre de 2017 (`anio` = 2017 solo en el primero);
  el manual no da los meses exactos (`fuentes.TRIMESTRES_ENGHO` es un supuesto). Los montos de la ENGHo
  están en pesos corrientes de la entrevista (el gasto medio sube 27% entre el primer y el último trimestre).
- `gastot` = suma de `gc_01..gc_12` = suma del archivo de gastos = `gascomp` + `gasvent` (ventas de bienes
  usados, negativas: se netean, como recomienda el manual del IPC). `gc_07` y algunos montos de `07.1`
  pueden ser negativos; en las ponderaciones democráticas se recortan a 0.
- El ingreso de la ENGHo incluye imputaciones del INDEC (23% de los hogares tiene algún componente imputado).
- Las ponderaciones del TP se reproducen con la mezcla 0,69/0,31 (columna D de la planilla); el texto del
  TP dice 0,691/0,309.
- **Movilidad**: el haber de t sube la variación del IPC de t−2 **calculada desde los niveles y
  redondeada a 2 decimales** (no la publicada a 1 decimal). Abril 2024 fue de transición (+27,4%). Los
  contrafactuales usan el mismo redondeo (`haberes.var_movilidad`; alias `pipeline.var_movilidad`).
- **La API de series de datos.gob.ar falla de forma intermitente** (oct-2026: la misma consulta devuelve
  la serie completa o una tabla vacía según el momento). `fuentes.serie_datos_gob` reintenta, si sigue
  vacía baja el CSV estático de la distribución (`fuentes.DISTRIBUCIONES`, haber mínimo y PIB) y si no hay
  datos lanza un error; nunca guarda una serie vacía en caché. Con una serie vacía del haber, el grupo
  haber mínimo quedaba en 0 hogares (falló así en Colab el 2026-10-13): `preparar_hogares` y el pipeline
  ahora cortan con un mensaje claro.
- El haber se conoce hasta 2 meses después del último IPC; la IMIG suele llegar 1 mes después del haber.
- La IMIG de junio y diciembre incluye aguinaldo (el factor relativo aplica igual). Algunos conceptos
  aparecen con dos descripciones: se deduplica por (fecha, código).
- El bootstrap mide solo el error muestral de la ENGHo (sin conglomerados), no la incertidumbre por la
  especificación: para eso está la tabla de variantes, cuyo rango es mucho mayor.
- Un índice que solo cambia ponderaciones no capta precios propios de los jubilados (cobertura de PAMI en
  medicamentos, tarifa social de transporte, segmentación de subsidios energéticos por ingreso).
- Colab: sesiones reutilizadas pueden tener el repo con cambios locales y módulos viejos en memoria
  (resuelto en la celda de configuración; ver CLAUDE.md).
