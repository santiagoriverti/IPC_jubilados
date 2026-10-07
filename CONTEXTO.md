# CONTEXTO — definiciones, decisiones, fuentes y trampas

## 1. Definiciones

- **IIJP**: índice de canasta fija (Lowe) con la estructura de gasto de los **hogares jubilados** de la
  ENGHo 2017/18, valorizada con los índices por división del IPC nacional. Base dic-2016 = 100.
  IIJPₜ = Σᵢ qᵢ Iᵢ,ₜ con qᵢ = wᵢ / Īᵢ (Īᵢ = promedio nov-2017 a nov-2018).
- **Hogar jubilado**: (Σ `ijubilacion` + Σ `ipensionesnc` de sus miembros) / `ingtoth` ≥ 0,5.
- **IPC ENGHo 17/18**: mismo cálculo con la canasta de todos los hogares. Sirve para separar:
  - *efecto edad* = IIJP vs IPC 17/18;
  - *efecto canasta vieja* = IPC 17/18 vs IPC oficial (canasta ENGHo 2004/05).
- **Brecha** entre índices en un período: (1 + infl. A) / (1 + infl. B) − 1.
- **Ventanas**: `indices.acumulada(nivel, desde, hasta)` no incluye la inflación del mes `desde`.
  "Dic-23 → may-26" en la jerga del TP = `acumulada(nivel, '2023-11', '2026-05')`.
- **Períodos** (`indices.PERIODOS`): Completo (dic-16 → último), Macri (dic-16 → dic-19), Fernández
  (dic-19 → nov-23), Milei (nov-23 → último), Shock tarifario (nov-23 → dic-24), Desde 2025
  (dic-24 → último), Ventana del TP (nov-23 → may-26).
- **Método del TP**: Σ wᵢ πᵢ,t con ponderaciones fijas sobre variaciones mensuales publicadas. Solo se
  calcula para mostrar el sesgo (`IIJP método TP`).
- **Descomposición por división** (`indices.descomposicion`): aporte = (ω_A − ω_B)(Rᵢ − R_B)/R_B con
  ponderaciones efectivas al inicio del período; los aportes suman la brecha en %.
- **Contrafactual de haberes**: misma regla de movilidad (IPC t−2) con el IIJP desde abr-2024
  (`haber_cf_iijp`); `factor_iijp` = haber IIJP / haber IPC. Ejercicio del TP desde dic-2023:
  `haber_cf_*_dic23` (separa la transición de fórmula del efecto índice).
- **Costo fiscal**: (jubilaciones contributivas + PNC de la IMIG) × (factor − 1). Cota superior
  (incluye el bono, que no se indexa).

## 2. Decisiones metodológicas (tomadas en la sesión 1; revisables con el usuario)

- Población de referencia = hogares jubilados (≥ 50% del ingreso). Variantes calculadas: canasta del
  TP, hogares con 65+, solo 65+, jubilados de menores/mayores ingresos (corte en la mediana ponderada
  del ingreso per cápita del grupo), canasta e índices regionales.
- Ponderaciones plutocráticas (como el IPC); democráticas como sensibilidad.
- Precio de referencia de la canasta: promedio de los índices durante el relevamiento (nov-17/nov-18).
- Bootstrap: 500 réplicas en `construir.py`, 300 en los notebooks (semilla 2018), remuestreo de
  hogares estratificado por región.
- Test de brecha sistemática: media de la diferencia mensual en logaritmos, error de Newey-West
  (rezagos = ⌊4 (T/100)^(2/9)⌋).

## 3. Fuentes

| Dato | Origen | Función |
|---|---|---|
| IPC por división y región | `indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv` (sep `;`, latin-1, coma decimal) | `fuentes.leer_ipc_divisiones` |
| ENGHo 2017/18 | `indec.gob.ar/ftp/cuadros/menusuperior/engho/engho2018_{hogares,personas,gastos}.zip` (txt sep `\|`) | `fuentes.leer_engho` |
| Haber mínimo | datos.gob.ar `58.1_MP_0_M_24` | `fuentes.leer_haber_minimo` |
| Bono | manual, `data/reference/bono_previsional.csv` (decretos) | `fuentes.leer_bono` |
| Ponderaciones IPC oficial | manual, `data/reference/ponderaciones_ipc_indec.csv` (INDEC, metodología 2019) | `ponderaciones.pond_ipc_oficial` |
| IMIG (gasto previsional, resultados) | `cuentas_publicas/output/imig_consolidado.csv` (disco o GitHub raw) | `fuentes.imig_mensual` |
| PIB nominal | datos.gob.ar `4.4_OGP_2004_T_17` (trimestral **anualizado**: anual = suma/4) | `fuentes.leer_pib_anual` |
| Series del TP original | `data/reference/tp_original_series.csv` (solo para documentar la revisión) | `pipeline` (`R['tp_original']`) |

## 4. Salidas

- `pipeline.calcular()` devuelve un dict `R`; claves principales: `ponderaciones`, `niveles` (columnas:
  IPC oficial, IPC ENGHo 17/18, IIJP, IIJP canasta TP, IIJP solo 65+, IIJP jub. bajos/altos, IIJP
  regional, IIJP método TP), `var_mensual`, `periodos`, `brecha_estadistica`, `descomposicion`
  (`nov23_ultimo`, `dic16_ultimo`), `bootstrap_*`, `haberes`, `regla_movilidad`, `fiscal_*`, `meta`.
- `src/exportar.py`: `exportar(R, dir_salida, dir_datos)` (Excel `IIJP_resultados.xlsx` con una hoja
  por tabla + 6 PNG + 14 CSV) y `zip_resultados(R, nombre)` (lo mismo + `LEEME.txt` en
  `_descargas/<nombre>.zip`; usado por los notebooks). La hoja Notas y el LEEME traen el commit.
- `scripts/construir.py` → `output/` y `data/processed/` (versionados). `scripts/comparar_zip.py`
  compara ZIPs de Colab contra esas salidas.
- Gráficos (`src/graficos.py`): g01 ponderaciones, g02 brecha desde nov-23 (con banda bootstrap y TP),
  g03 brecha histórica y componentes, g04 descomposición, g05 haber real, g06 costo fiscal.

## 5. Trampas conocidas

- **Regiones ENGHo ≠ orden del IPC**: 1 GBA, 2 Pampeana, 3 Noroeste, 4 Noreste, 5 Cuyo, 6 Patagonia
  (`fuentes.REGIONES_ENGHO`).
- `gc_07` (transporte) puede ser negativo (venta de vehículos). Plutocrático: se netea; democrático:
  se recorta a 0.
- La suma `gc_01..gc_12` = `gastot` (no `gascomp`). El archivo de hogares solo abre la división 09
  (`gc09_*`); para más detalle hay que ir al archivo de gastos por artículo.
- Las ponderaciones del TP se reproducen con la mezcla 0,69/0,31 (columna D de la planilla); el
  texto del TP dice 0,691/0,309.
- **Movilidad**: el haber de t sube la variación del IPC de t−2 **calculada desde los niveles y
  redondeada a 2 decimales** (no la publicada a 1 decimal: con esa el error llega a 0,05 p.p.; con 2
  decimales es 0 en todos los meses desde mayo 2024). Abril 2024 fue de transición (+27,4%). El
  contrafactual por IIJP usa el mismo redondeo (`pipeline.var_movilidad`).
- El haber se conoce hasta 2 meses después del último IPC; la IMIG suele llegar 1 mes después del haber.
- La IMIG de junio y diciembre incluye aguinaldo (el factor relativo aplica igual).
- En la IMIG algunos conceptos aparecen con dos descripciones (p. ej. RESULTADO_FINANCIERO): se
  deduplica por (fecha, código).
- La descomposición "vs IPC oficial" usa como B el Laspeyres replicado con las ponderaciones oficiales
  (difiere ≤ 0,16% del oficial): por eso suma +2,66% y no +2,71%.
- El bootstrap solo mide el error muestral de la ENGHo, no la incertidumbre por la definición de la
  población (para eso están las variantes).
- Colab: sesiones reutilizadas pueden tener el repo con cambios locales y módulos viejos en memoria
  (resuelto en la celda de configuración; ver CLAUDE.md).
