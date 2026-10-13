# Revisión del TP "Índice de Precios de Jubilados y Pensionados" (INECO · UADE, Grupo 2)

Materiales revisados: informe (PDF, 17 págs.), presentación (21 diapositivas) y planilla
(hojas `Canasta`, `Indicadores sociales` e `Impacto fiscal`). Los archivos originales **no se
versionan** en este repo (tienen nombres y legajos); las series que calcula la planilla están en
[`data/reference/tp_original_series.csv`](../data/reference/tp_original_series.csv) para poder
comparar. Todas las cifras "corregidas" salen de `python scripts/construir.py` (datos hasta
ago-2026) y se pueden reproducir con los notebooks. Las del IIJP corresponden a la metodología vigente
(octubre 2026): canasta de los hogares jubilados valorizada por región con las aperturas del IPC (ver el
[README](../README.md)); las del método y la canasta del TP están en las hojas `Revision_TP_*` del Excel.

## Resumen

La ventana "dic-23 → may-26" del TP incluye la inflación de diciembre 2023, es decir, va del nivel de
noviembre 2023 al de mayo 2026; las cifras corregidas usan esa misma ventana.

| Afirmación del TP | Resultado con el método corregido | Causa principal de la diferencia |
|---|---|---|
| Brecha IIJP vs IPC dic-23 → may-26: **+3,84%** | **+2,74%** (IC 95% muestral: 2,18 a 3,23). Con la canasta y el método del TP la brecha sería 6,3%; con canasta fija y 12 divisiones, 2,6% | Método de agregación (M1), febrero 2024 sin Vivienda (B1) y nivel de detalle de los precios (M1b) |
| La brecha se debe al patrón de consumo de los jubilados | Desde nov-23 el **efecto edad es −0,7%** (su signo depende de la especificación); la brecha viene de que el IPC oficial usa la canasta de 2004/05 (+3,8%) | No separa edad de canasta vieja (M2) |
| Corregir permanentemente un 3,8% | La brecha cambia de signo por período (Macri +3,2%, Fernández −4,9%, Milei +3,1%) y en 2016-2026 la media mensual no es distinta de 0 | Generaliza un episodio (M4) |
| Pérdida de poder adquisitivo de la mínima dic-23 → may-26: **−9,77%** | Haber **sin bono: +13,2%** (vs dic-23) / +9,1% (vs nov-23). **Con bono: −9,7%** (vs nov-23; −13,3% con el IIJP haber mínimo) | Fechas mezcladas (B6); el bono congelado es lo que explica la pérdida |
| Indexando por IIJP desde dic-23 la mínima sería $484.827 en may-26 (pérdida ~19%, $1,8 M acumulados) | El nivel es parecido ($483.176), pero de esa diferencia **19,3 de 22,9 puntos son la transición de fórmula** (ene-feb 2024 sin aumento); el efecto del índice es **3,0%** | Atribuye al índice un efecto de la fórmula (M5) |
| Desde jun-24, mínima por IIJP $15.276 (3,9%) mayor en may-26 | Con la regla vigente desde abr-24: **+0,75%** en may-26 ($2.947) y +1,1% en sep-26 | Método (M1) y la "corrección" duplicada (B3) |
| Costo fiscal may-26: $186.167 M, 38,9% del resultado financiero | **$42.559 M**, 0,75% del gasto previsional, 8,9% del resultado financiero del mes | Brecha sobreestimada y supuestos de beneficiarios (M7) |
| Brecha de sostenibilidad 2050: $54,6 billones (148 vs 94) | Ese resultado exige que el IIJP supere al IPC en **1,9 p.p. por año durante 24 años**: unas 15 veces el promedio histórico (0,12 p.p./año, no significativo) | Supuesto no respaldado por los datos (M6) |

## A. Lo que está bien y se conserva

- **La pregunta** (¿la inflación de los jubilados difiere de la general?) y el enfoque de usar fuentes oficiales.
- **La canasta**: las ponderaciones de la hoja `Canasta` (B3:D14) se reproducen desde los microdatos
  de la ENGHo 2017/18 con diferencia máxima de 0,0006 (hogares con 1 mayor de 65 y con 2 o más;
  0,69 es la proporción ponderada de hogares con un solo mayor: 0,6899). Es un buen punto de partida.
- **Los insumos de precios**: las variaciones por división cargadas coinciden con las del INDEC en
  todos los meses salvo el error de febrero 2024 (B1).
- **El haber mínimo** está bien cargado y la indexación con rezago de dos meses (hoja `Impacto fiscal`,
  columna E) reproduce la lógica de la movilidad vigente.
- La intención de **cuantificar el costo fiscal** y compararlo con el resultado de las cuentas públicas.

## B. Errores de la planilla

**B1. Febrero 2024 sin la división Vivienda** (`Canasta!A422:D435`). El bloque tiene 11 divisiones
y sus ponderaciones suman 0,863. Vivienda (13,7%) subió 20,2% ese mes. El IIJP de febrero da 11,97%
cuando con la propia metodología del TP debería dar 14,74%. Como el error es a la baja, compensa
parcialmente el sesgo del método (M1).

**B2. Etiqueta duplicada.** El bloque de `Canasta!A257` dice "MARZO 2025" pero es enero 2025 (el
cálculo usa los datos correctos de enero; solo es la etiqueta).

**B3. La "corrección" cuenta dos veces la brecha** (`Impacto fiscal!E38 = E36*(1+0,0384)` y
`G38 = G36*(1+0,0384)`). E36 y G36 ya son haberes indexados por el IIJP, es decir, ya contienen la
brecha con el IPC; multiplicarlos otra vez por 1,0384 la duplica. Todos los escenarios "con
corrección" (Q4:Q10, R4:R10, bloques T-AA) heredan el error. Por eso los haberes "c/corrección" son
≈ 1,039² veces los de la mínima por IPC.

**B4. La proyección "Mínima IPC" no usa el IPC** (`Impacto fiscal!L4 = D36*(1+C35)`,
`L5 = L4*(1+C36)`): C35 y C36 son el IIJP de abril y mayo. Además, desde agosto las tres trayectorias
usan la misma inflación del REM (K4:K9), así que la "diferencia" proyectada es solo la brecha de nivel
de mayo arrastrada, no una divergencia futura.

**B5. Se mezclan costo incremental y gasto total** (`Impacto fiscal`, bloques "Junio" y "Julio").
El bloque de junio multiplica *diferencias* de haber (O4) por beneficiarios: $193.110 M de costo
extra. El de julio multiplica *niveles* de haber (N5): $5,28 billones, que es gasto total. El texto
compara ambos como si fueran lo mismo ("casi el doble", "diferencia de $202.790 M").

**B6. Poder adquisitivo con fechas mezcladas** (`Indicadores sociales!C2 = -(1-((393173/4,1219)/105712))`).
105.712 es el haber de diciembre 2023 (que ya incluye el aumento de diciembre), pero 4,1219 es la
inflación desde noviembre (incluye el 25,5% de diciembre). Comparado de forma consistente, el haber
sin bono de mayo 2026 está **13,2% por encima** del de diciembre 2023 (9,1% sobre noviembre). La
pérdida real aparece al sumar el bono: haber + bono cae 9,7% entre nov-23 y may-26, porque el bono
quedó fijo en $70.000 (actualizado por IPC desde marzo 2024 sería $194.268 en ago-26). D2 divide el
haber con la corrección duplicada (B3) por la inflación del IIJP.

**B7. Cobertura de la CBT** (`Indicadores sociales!C9`). Divide el haber por la CBT de un adulto
equivalente (varón de 30-60 años). Para una persona mayor el coeficiente de adulto equivalente del
INDEC es menor a 1, así que el cociente subestima la cobertura; conviene usar el coeficiente de la
edad y sexo correspondientes.

## C. Problemas de método

**M1. Ponderaciones fijas sobre variaciones mensuales no es un índice de canasta fija.** El TP
calcula cada mes IIJP_t = Σ wᵢ · πᵢ,t con las ponderaciones de 2017/18. El IPC (y cualquier índice de
canasta fija) valoriza siempre las mismas *cantidades*, de modo que la ponderación efectiva de cada
rubro se mueve con sus precios relativos. Ejemplo: Vivienda pesa 14,5% en la canasta de los hogares
jubilados a precios de 2017/18, pero en noviembre de 2023, tras cuatro años de tarifas congeladas,
pesaba **8,3%** del valor de esa canasta. Aplicarle 13,7% a los aumentos tarifarios de 2024 exagera
su impacto. Abril 2024, con la canasta del TP: IPC 8,8%; canasta fija 9,2%; método del TP 11,3%.
Prueba simple: el método del TP aplicado a las ponderaciones del propio INDEC no reproduce el IPC
oficial (dic-23 → may-26: 317% contra 312%), mientras que la canasta fija lo reproduce con error
máximo de 0,16% en casi 10 años con 12 divisiones, y de 0,08% con la estructura por aperturas del IIJP. Con la canasta del TP, la brecha dic-23 → may-26 es 6,3% con su método
y 2,6% con canasta fija. Es el mismo error que tienen varias estimaciones públicas de un "IPC con la
canasta 2017/18" (por ejemplo, +7,4% para 2024: con ponderaciones fijas sobre variaciones da +7,42%;
con canasta fija, +2,6%).

**M1b. Doce divisiones no alcanzan.** Valorizar la canasta solo por división hereda, dentro de cada
división, la composición de 2004/05 de todos los hogares. Los jubilados gastan dentro de salud más en
medicamentos (54% vs 42%) y menos en prepagas; dentro de vivienda, mucho menos en alquiler (16% vs 35%)
y más en electricidad y gas (51% vs 41%); dentro de transporte, más en transporte público. Esos rubros
tuvieron variaciones muy distintas desde 2023. El IIJP actual valoriza cada gasto con el índice más
específico que publica el INDEC en cada región; por divisiones, la brecha dic-23 → may-26 de los
hogares jubilados sería 2,4% en lugar de 2,7%.

**M2. Se confunde el efecto de la edad con el de una canasta desactualizada.** El IPC oficial usa la
estructura de gasto de la **ENGHo 2004/05**; la canasta del TP es de la **ENGHo 2017/18**. La mayor
ponderación de vivienda que el TP atribuye a los jubilados (13,7% vs 9,4%) es igual a la de *todos*
los hogares en la encuesta nueva (14,5%). Para aislar la edad hay que comparar contra un IPC
recalculado con la misma encuesta:

| Período | IIJP vs IPC oficial | Efecto edad (IIJP vs IPC 2017/18) | Efecto canasta vieja (IPC 2017/18 vs oficial) |
|---|---|---|---|
| dic-16 → ago-26 | +1,20% | **+1,60%** | −0,39% |
| Macri (dic-16 → dic-19) | +3,22% | +2,91% | +0,30% |
| Fernández (dic-19 → nov-23) | −4,86% | −0,57% | −4,31% |
| Milei (nov-23 → ago-26) | +3,06% | −0,70% | +3,78% |

Desde fines de 2023 la canasta de los jubilados subió algo menos que la de todos los hogares, pero el
efecto edad es chico y su signo depende de cómo se defina la población (entre −1,3% y +0,7% en las
variantes). A favor de los jubilados juegan que compran menos ropa (que subió poco) y más electricidad
y gas; en contra, que alquilan mucho menos y compran más medicamentos, que subieron menos que las
prepagas. Lo que hace que el IPC oficial quede abajo es su canasta de 2004/05, que sobrepondera ropa
(9,9%) y subpondera vivienda (9,4%): afecta a todos los hogares, no solo a los jubilados. En cambio, en
todo el período 2016-2026 sí hay un efecto edad positivo y robusto (+1,6%), concentrado en 2016-2019.

**M3. Población.** "Hogares con al menos un mayor de 65" incluye hogares multigeneracionales donde el
gasto lo deciden sobre todo los miembros más jóvenes, y la mezcla 0,69/0,31 pondera por cantidad de
hogares (no por gasto, como el IPC). El IIJP corregido usa **hogares cuya principal fuente de ingreso
son jubilaciones y pensiones** (≥ 50%). La tabla de variantes (hoja `Variantes` del Excel) prueba once
definiciones alternativas (entre ellas la población del TP, hogares con algún mayor de 65): la brecha
dic-23 → ago-26 va de 2,4% a 4,6% según la definición y siempre es positiva.

**M4. Una brecha de un período no es una corrección permanente.** El 3,84% surge casi entero del
ajuste de precios relativos de 2024. En dic-19 → nov-23 la brecha fue −4,9%. La diferencia media
mensual 2016-2026 es 0,010 p.p. con IC 95% (Newey-West) de −0,045 a +0,066: no hay evidencia de una
brecha persistente mes a mes; la acumulada del período es +1,2% y no se sostiene en todas las variantes.

**M5. La pérdida del haber se atribuye al índice.** El ejercicio "IIJP desde diciembre 2023" compara
una indexación mensual hipotética con el haber efectivo, que en enero y febrero de 2024 no aumentó
(regía la fórmula trimestral de la Ley 27.609). Con el mismo ejercicio por IPC, el haber de mayo
2026 sería 19,3% mayor; por IIJP, 22,9%. La transición de fórmula explica la mayor parte de la
diferencia; el índice, 3,0%. De los $1,79 M acumulados, $0,24 M corresponden al índice.

**M6. Proyección 2050.** El escenario "IIJP" (148 billones) contra "IPC" (94 billones) implica que el
gasto con IIJP es 58% mayor: el IIJP tendría que superar al IPC en 1,9 p.p. **todos los años**
durante 24 años. Además, el desvío "lineal en pesos" mezcla magnitudes nominales y reales, y la
demografía no cambia el costo *relativo* (escala igual los dos escenarios). El código no se entregó.
Alternativa: tabla de sensibilidad del costo de un desvío permanente de d p.p. por año
(`fiscal_desvio_permanente`): con d = 0,1 p.p./año, en 25 años el costo es 2,5% del gasto previsional
(0,17% del PIB).

**M7. Costo fiscal.** En lugar de multiplicar diferencias del haber mínimo por cantidades de
beneficiarios con supuestos de haber medio (2,6 × mínimo) y proporciones fijas (48/52), alcanza con
el gasto efectivo en jubilaciones y pensiones de la IMIG por el factor relativo de haber
(IIJP/IPC − 1): incluye automáticamente aguinaldos, todas las categorías de beneficio y la
distribución real de haberes.

## D. Qué conclusiones se sostienen

- La canasta de los hogares jubilados es distinta (más alimentos y salud, menos educación,
  transporte, ropa y restaurantes), también dentro de cada división. ✔
- En períodos sin grandes cambios de precios relativos el IIJP y el IPC convergen. ✔
- Desde fines de 2023 el IPC oficial subestima la inflación de los jubilados (≈ 3,1%)… pero también la
  de todos los hogares (≈ 3,8%), porque su canasta es de 2004/05. La primera recomendación de política
  es **actualizar la canasta del IPC** (la ENGHo 2017/18 está disponible). El índice específico agrega
  información en plazos largos (efecto edad +1,6% en 2016-2026, concentrado en 2016-2019) y, sobre
  todo, para los jubilados de haber mínimo (+3,8% sobre el IPC y +2,6% sobre el IIJP en 2016-2026).
- El costo fiscal de indexar por IIJP es bajo (~0,02% del PIB por año en 2024-2025). La pérdida de
  poder adquisitivo de la jubilación mínima se explica sobre todo por el **bono congelado** y por la
  transición de fórmula de comienzos de 2024, no por el índice de actualización.
