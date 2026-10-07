# CONTEXTO — definiciones, fuentes y trampas

## 1. Definiciones

- **IIJP**: índice de canasta fija (Lowe) con la estructura de gasto de los **hogares jubilados** de la
  ENGHo 2017/18, valorizada con los índices por división del IPC nacional. Base dic-2016 = 100.
- **Hogar jubilado**: (Σ `ijubilacion` + Σ `ipensionesnc` de sus miembros) / `ingtoth` ≥ 0,5.
- **IPC ENGHo 17/18**: mismo cálculo con la canasta de todos los hogares. Sirve para separar:
  - *efecto edad* = IIJP vs IPC 17/18;
  - *efecto canasta vieja* = IPC 17/18 vs IPC oficial (canasta ENGHo 2004/05).
- **Brecha** entre índices en un período: (1 + infl. A) / (1 + infl. B) − 1.
- **Ventanas**: `acumulada(nivel, desde, hasta)` no incluye la inflación del mes `desde`.
  "Dic-23 → may-26" en la jerga del TP = `acumulada(nivel, '2023-11', '2026-05')`.
- **Método del TP**: Σ wᵢ πᵢ,t con ponderaciones fijas sobre variaciones mensuales. Solo se calcula
  para mostrar el sesgo (`IIJP método TP`).

## 2. Fuentes

| Dato | Origen | Función |
|---|---|---|
| IPC por división y región | `indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv` (sep `;`, latin-1, coma decimal) | `fuentes.leer_ipc_divisiones` |
| ENGHo 2017/18 | `indec.gob.ar/ftp/cuadros/menusuperior/engho/engho2018_{hogares,personas,gastos}.zip` (txt sep `|`) | `fuentes.leer_engho` |
| Haber mínimo | datos.gob.ar `58.1_MP_0_M_24` | `fuentes.leer_haber_minimo` |
| Bono | manual, `data/reference/bono_previsional.csv` | `fuentes.leer_bono` |
| Ponderaciones IPC oficial | manual, `data/reference/ponderaciones_ipc_indec.csv` (INDEC, metodología 2019) | `ponderaciones.pond_ipc_oficial` |
| IMIG (gasto previsional, resultados) | `cuentas_publicas/output/imig_consolidado.csv` | `fuentes.imig_mensual` |
| PIB nominal | datos.gob.ar `4.4_OGP_2004_T_17` (trimestral **anualizado**: anual = suma/4) | `fuentes.leer_pib_anual` |

## 3. Trampas conocidas

- **Regiones ENGHo ≠ orden del IPC**: 1 GBA, 2 Pampeana, 3 Noroeste, 4 Noreste, 5 Cuyo, 6 Patagonia
  (`fuentes.REGIONES_ENGHO`).
- `gc_07` (transporte) puede ser negativo (venta de vehículos). Plutocrático: se netea; democrático:
  se recorta a 0.
- La suma `gc_01..gc_12` = `gastot` (no `gascomp`).
- Las ponderaciones del TP se reproducen con la mezcla 0,69/0,31 (columna D de la planilla); el
  texto del TP dice 0,691/0,309.
- **Movilidad**: el haber de t sube la variación del IPC de t−2 **publicada a 1 decimal**. Abril 2024
  fue de transición (+27,4%). El contrafactual por IIJP también redondea a 1 decimal.
- El haber se conoce hasta 2 meses después del último IPC; la IMIG suele llegar 1 mes después del haber.
- La IMIG de junio y diciembre incluye aguinaldo (el factor relativo aplica igual).
- En la IMIG algunos conceptos aparecen con dos descripciones (p. ej. RESULTADO_FINANCIERO): se
  deduplica por (fecha, código).
- La descomposición "vs IPC oficial" usa como B el Laspeyres replicado con las ponderaciones oficiales
  (difiere ≤ 0,16% del oficial): por eso suma +2,66% y no +2,71%.
- El bootstrap solo mide el error muestral de la ENGHo, no la incertidumbre por la definición de la
  población (para eso están las variantes).
