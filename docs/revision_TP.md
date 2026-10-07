# Revisión del TP "Índice de Precios de Jubilados y Pensionados" (INECO · UADE, Grupo 2)

Materiales revisados: informe (PDF, 17 págs.), presentación (21 diapositivas) y planilla
(hojas `Canasta`, `Indicadores sociales` e `Impacto fiscal`). Los archivos originales **no se
versionan** en este repo (tienen nombres y legajos); las series que calcula la planilla están en
[`data/reference/tp_original_series.csv`](../data/reference/tp_original_series.csv) para poder
comparar. Todas las cifras "corregidas" salen de `python scripts/construir.py` (datos hasta
ago-2026) y se pueden reproducir con los notebooks.

## Resumen

La ventana "dic-23 → may-26" del TP incluye la inflación de diciembre 2023, es decir, va del nivel de
noviembre 2023 al de mayo 2026; las cifras corregidas usan esa misma ventana.

| Afirmación del TP | Resultado con el método corregido | Causa principal de la diferencia |
|---|---|---|
| Brecha IIJP vs IPC dic-23 → may-26: **+3,84%** | **+2,39%** (IC 95% muestral: 2,06 a 2,75) | Método de agregación (M1) y febrero 2024 sin Vivienda (B1) |
| La brecha se debe al patrón de consumo de los jubilados | Desde nov-23 el **efecto edad es −0,7%**; la brecha viene de que el IPC oficial usa la canasta de 2004/05 (+3,4%) | No separa edad de canasta vieja (M2) |
| Corregir permanentemente un 3,8% | La brecha cambia de signo por período (Macri +2,8%, Fernández −4,0%, Milei +2,7%) y en 2016-2026 la media mensual no es distinta de 0 | Generaliza un episodio (M4) |
| Pérdida de poder adquisitivo de la mínima dic-23 → may-26: **−9,77%** | Haber **sin bono: +13,2%** (vs dic-23) / +9,1% (vs nov-23). **Con bono: −9,7%** (vs nov-23) | Fechas mezcladas (B6); el bono congelado es lo que explica la pérdida |
| Indexando por IIJP desde dic-23 la mínima sería $484.827 en may-26 (pérdida ~19%, $1,8 M acumulados) | De esa diferencia, **19,3 de 22,4 puntos son la transición de fórmula** (ene-feb 2024 sin aumento); el efecto del índice es **2,6%** | Atribuye al índice un efecto de la fórmula (M5) |
| Desde jun-24, mínima por IIJP $15.276 (3,9%) mayor en may-26 | Con la regla vigente desde abr-24: **+0,5%** en may-26 y +0,9% en sep-26 | Método (M1) y la "corrección" duplicada (B3) |
| Costo fiscal may-26: $186.167 M, 38,9% del resultado financiero | **$26.892 M**, 0,47% del gasto previsional, 5,6% del resultado financiero del mes | Brecha sobreestimada y supuestos de beneficiarios (M7) |
| Brecha de sostenibilidad 2050: $54,6 billones (148 vs 94) | Ese resultado exige que el IIJP supere al IPC en **1,9 p.p. por año durante 24 años**: 14 veces el promedio histórico (0,14 p.p./año, no significativo) | Supuesto no respaldado por los datos (M6) |

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
quedó fijo en $70.000 (actualizado por IPC desde marzo 2024 sería $194.145 en ago-26). D2 divide el
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
pesaba **8,1%** del valor de esa canasta. Aplicarle 13,7% a los aumentos tarifarios de 2024 exagera
su impacto. Abril 2024: IPC 8,8%; IIJP canasta fija 9,3%; método del TP 11,3%.
Prueba simple: el método del TP aplicado a las ponderaciones del propio INDEC no reproduce el IPC
oficial (dic-23 → may-26: 317% contra 312%), mientras que la canasta fija lo reproduce con error
máximo de 0,16% en casi 10 años. Con el método del TP la brecha dic-23 → may-26 es 6,3%; con canasta
fija, 2,4%.

**M2. Se confunde el efecto de la edad con el de una canasta desactualizada.** El IPC oficial usa la
estructura de gasto de la **ENGHo 2004/05**; la canasta del TP es de la **ENGHo 2017/18**. La mayor
ponderación de vivienda que el TP atribuye a los jubilados (13,7% vs 9,4%) es igual a la de *todos*
los hogares en la encuesta nueva (14,5%). Para aislar la edad hay que comparar contra un IPC
recalculado con la misma encuesta:

| Período | IIJP vs IPC oficial | Efecto edad (IIJP vs IPC 2017/18) | Efecto canasta vieja (IPC 2017/18 vs oficial) |
|---|---|---|---|
| dic-16 → ago-26 | +1,32% | +0,79% | +0,53% |
| Macri (dic-16 → dic-19) | +2,77% | +1,48% | +1,27% |
| Fernández (dic-19 → nov-23) | −4,01% | +0,01% | −4,02% |
| Milei (nov-23 → ago-26) | +2,71% | **−0,69%** | +3,43% |

Desde fines de 2023 la canasta de los jubilados subió *menos* que la de todos los hogares: pondera
más alimentos y equipamiento, que subieron menos que el promedio, y menos educación, transporte y
restaurantes, que subieron más. Lo único que empuja el IIJP hacia arriba de forma apreciable es que
los jubilados compran menos ropa, que subió poco. Salud, el rubro "típico" de los jubilados, subió casi como el promedio y aporta poco. Lo que
hace que el IPC oficial quede abajo es que sobrepondera ropa (9,9%) y subpondera vivienda (9,4%):
afecta a todos los hogares, no solo a los jubilados.

**M3. Población.** "Hogares con al menos un mayor de 65" incluye hogares multigeneracionales donde el
gasto lo deciden sobre todo los miembros más jóvenes, y la mezcla 0,69/0,31 pondera por cantidad de
hogares (no por gasto, como el IPC). El IIJP corregido usa **hogares cuya principal fuente de ingreso
son jubilaciones y pensiones** (≥ 50%). Los resultados son robustos a la definición (canasta del TP,
hogares solo de mayores, jubilados de menores y mayores ingresos: ver `brecha_periodos.csv`).

**M4. Una brecha de un período no es una corrección permanente.** El 3,84% surge casi entero del
ajuste de precios relativos de 2024. En dic-19 → nov-23 la brecha fue −4,0%. La diferencia media
mensual 2016-2026 es 0,011 p.p. con IC 95% (Newey-West) de −0,035 a +0,058: no hay evidencia de una
brecha sistemática.

**M5. La pérdida del haber se atribuye al índice.** El ejercicio "IIJP desde diciembre 2023" compara
una indexación mensual hipotética con el haber efectivo, que en enero y febrero de 2024 no aumentó
(regía la fórmula trimestral de la Ley 27.609). Con el mismo ejercicio por IPC, el haber de mayo
2026 sería 19,3% mayor; por IIJP, 22,4%. La transición de fórmula explica casi toda la diferencia;
el índice, 2,6%. De los $1,77 M acumulados, $0,22 M corresponden al índice.

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
  transporte, ropa y restaurantes). ✔
- En períodos sin grandes cambios de precios relativos el IIJP y el IPC convergen. ✔
- Desde fines de 2023 el IPC oficial subestima la inflación de los jubilados (≈ 2,7%)… pero también la
  de todos los hogares (≈ 3,4%), porque su canasta es de 2004/05. La recomendación de política que
  surge de los datos es **actualizar la canasta del IPC** (la ENGHo 2017/18 está disponible); un
  índice específico para jubilados agrega poco encima de eso.
- El costo fiscal de indexar por IIJP es bajo (~0,01% del PIB por año en 2024-2025). La pérdida de
  poder adquisitivo de la jubilación mínima se explica sobre todo por el **bono congelado** y por la
  transición de fórmula de comienzos de 2024, no por el índice de actualización.
