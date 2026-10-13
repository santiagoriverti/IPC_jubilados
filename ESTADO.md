# ESTADO — IPC_jubilados (IIJP)

**Última actualización:** 2026-10-13 (sesión 2: rediseño metodológico). Punto de entrada para retomar:
este archivo → `CLAUDE.md` (reglas) → `CONTEXTO.md` (método y trampas) → `.claude/memory/project.md`
(historial).

## 0. Estado en una línea

El IIJP se valoriza **por región y al nivel de aperturas del IPC**, con los restos no publicados
deducidos de las ponderaciones oficiales del INDEC y una concordancia ENGHo → IPC (expensas). Incluye un
subíndice **haber mínimo**, intervalos regionales y una **tabla de 20 variantes**. Datos a ago-2026.
Colab verificado con `b419fa3` (versión con la concordancia de las expensas): los 3 ZIP = local. README
y revision_TP al día. **Pendiente**: reescribir la sección LaTeX del informe INECO.

## 1. Cobertura de datos

| Fuente | Último dato | Cómo se actualiza |
|---|---|---|
| IPC por división y por aperturas regionales (INDEC) | ago-2026 | automático (`--refrescar`) |
| Ponderaciones oficiales por región (`data/reference/ponderadores_ipc_regiones.csv`) | dic-2016 | fijas (cambian solo con un IPC nuevo) |
| Haber mínimo (datos.gob.ar `58.1_MP_0_M_24`) | sep-2026 | automático |
| Bono previsional (`data/reference/bono_previsional.csv`) | sep-2026 ($70.000) | **manual**, una fila por mes |
| IMIG (vía repo `cuentas_publicas`) | ago-2026 | actualizar ese repo primero |
| PIB nominal anual completo (datos.gob.ar) | 2025 | automático |
| ENGHo | 2017/18 (canasta fija) | no cambia |

## 2. Cifras vigentes (`python scripts/construir.py`, bootstrap 500)

- **Ago-2026**: IPC 1,66% m/m y 33,5% i.a. · IIJP 1,59% y 34,8% · IIJP haber mínimo 1,80% y 36,5% ·
  IPC ENGHo 17/18 1,51% y 34,6%.
- **Brecha IIJP vs IPC oficial**: dic-16 → ago-26 **+1,20%** (IC 0,78-1,62); Macri +3,22%; Fernández
  −4,86%; Milei (nov-23 → ago-26) **+3,06%** (IC 2,45-3,56); shock tarifario +2,53%; desde dic-24 +0,52%;
  ventana del TP +2,74%.
- **IIJP haber mínimo**: vs IPC oficial completo +3,80% (IC 3,17-4,47), Milei +4,55% (IC 3,76-5,42); vs
  IIJP completo +2,57% (IC 1,99-3,19), Milei +1,45% (IC 0,67-2,25). Con topes de 1 a 2 haberes mínimos,
  vs IIJP: completo +1,8 a +2,8%, Milei +1,0 a +1,5%.
- **Efecto edad** (IIJP vs IPC 17/18): completo **+1,60%** (IC 1,24-2,00); Macri +2,91%; Fernández −0,57%;
  Milei −0,70% (IC −1,18 a −0,20); desde dic-24 −0,93%. Contra los hogares no jubilados: completo +1,92%,
  Milei −0,84%. **Efecto canasta vieja** (IPC 17/18 vs oficial): completo −0,39%; Milei +3,78%.
- **Firmeza (20 variantes)**: mantienen el signo en todas la brecha vs IPC oficial en Macri, Fernández y
  Milei (2,4 a 6,5%), el efecto edad del período completo (0,2 a 4,2%) y de Macri, y el aumento del haber
  si se indexara por IIJP (0,3 a 6,2%). **No son firmes**: la brecha del período completo (−0,2 a 3,8%) y
  desde 2025, y el signo del efecto edad en Fernández, Milei (−1,3 a +0,7) y desde 2025.
- Lo que explica la brecha en Milei (por apertura): prendas (los jubilados compran menos ropa, que subió
  menos) y electricidad y gas, a favor; alquiler, restaurantes y recreación, en contra. Medicamentos
  resta en el efecto edad (subieron menos que prepagas).
- **Regiones** (IIJP vs IPC de la región, Milei, IC 95%): GBA +2,7% (1,8-3,7), Pampeana +2,0% (1,1-2,8),
  NOA +5,7% (4,4-7,1), NEA +9,0% (7,1-11,0), Cuyo +3,2% (1,9-4,7), Patagonia +5,3% (3,7-7,1).
- **Canasta** (hogares jubilados, 5.350 en la muestra, 2,96 M expandidos): alimentos 26,4%, vivienda
  14,5% (dentro de vivienda: alquiler 16%, expensas y gastos comunes 12%, electricidad y gas 51%), salud
  11,4% (medicamentos 54%, prepagas 29%), transporte 11,3% (transporte público 27%). Haber mínimo (2.081
  hogares, 40% de los jubilados): alimentos 32,9%, vivienda 16,5%, medicamentos 72% de salud, transporte
  público 43%. Precios: 83% de la canasta con aperturas publicadas, 16,5% con restos derivados, 0,5% con
  el índice del agregado.
- **Haber mínimo real** (base nov-23, ago-26): sin bono +10,1% (IPC) / +6,8% (IIJP) / +5,3% (IIJP haber
  mínimo); con bono −9,7% / −12,4% / −13,7%. Bono actualizado por IPC desde mar-24: $194.268.
- **Contrafactual desde abr-24** (sep-26): con IIJP el haber sería +1,10% ($4.698/mes en la mínima); con
  IIJP haber mínimo, +2,61% ($11.188).
- **Costo fiscal** (indexar por IIJP): 2024 (abr-dic) $127.947 M = 0,42% del gasto previsional (0,022% PIB);
  2025 $125.308 M = 0,22% (0,015% PIB); 2026 ene-ago $297.570 M = 0,63%. Mayo 2026: $42.559 M.
- Movilidad: ANSES usa el IPC(t−2) desde niveles con 2 decimales (error 0 en 29/29 meses).

## 3. Dónde se citan las cifras (actualizar todo junto si cambian)

| Documento | Estado |
|---|---|
| `ESTADO.md` §2 | al día: todas |
| `README.md` | al día: tabla de períodos (brecha, efecto edad, haber mínimo), puntos 1-7, nota metodológica (5.350 / 2.081 hogares, 254 componentes, 0,08%, cobertura 83/16,5/0,5%) |
| `docs/revision_TP.md` | al día: tabla resumen (ventana del TP, haberes may-26/sep-26, ejercicio dic-23, costo may-26, 2050), M1, M1b, M2 (tabla edad/canasta), M3, M4, M5, D |
| `docs/informe_indicadores/seccion_iijp.tex` | **desactualizada** (comentario en la cabecera): reescribir con la metodología nueva |
| Markdown de `scripts/gen_notebooks.py` | sin cifras fijas (las imprime el código) |

## 4. Verificación (2026-10-13)

- `python -m pytest tests -q` → 14 passed (7 de `tests/test_estructura.py`, incluida la concordancia).
- `python scripts/control_calidad.py` → 0 ALERTAS: réplica del IPC nacional con la estructura de
  aperturas 0,081% (regiones ≤ 0,257%); agregados completos ≤ 0,056%; restos estables ante el redondeo
  (≤ 4,1%); 100% del gasto asignado; canastas suman 1; haber mínimo 39,6% de los jubilados; canasta
  valorizada con el índice del agregado 0,51%; canasta del TP 0,0006; regla de movilidad 29/29;
  contrafactual = haber efectivo; bono cargado; IMIG sin huecos.
- Notebooks ejecutados en local (`_local_run/`, bootstrap 30) y sus ZIP comparados con `construir.py`:
  0 diferencias no esperadas (`comparar_zip.py` ignora las columnas de intervalos p2.5/p97.5).
- Colab: con `7c770cf` falló (API de datos.gob.ar vacía; corregido en `6e7aab1`); con `6e7aab1` y con
  `b419fa3` (concordancia de expensas) los 3 ZIP = local: 0 diferencias no esperadas.

## 5. Próximos pasos posibles (a decidir con el usuario)

1. (Hecho) Corrida en Colab de los 3 notebooks con `b419fa3`.
2. Sección LaTeX del informe INECO (metodología por aperturas, tabla de firmeza, subíndice haber mínimo)
   y, si se quiere, una versión resumida de la devolución a los alumnos.
3. Precios propios de los jubilados (limitación conceptual): cobertura de PAMI en medicamentos, tarifa
   social de transporte, segmentación de subsidios energéticos, geriátricos y residencias (sin precio en
   el IPC). Requiere datos fuera del IPC.
3b. Efecto de diseño de la ENGHo: calibrar el ancho de los intervalos con los coeficientes de variación
   que publique el INDEC (el bootstrap sin conglomerados es una cota inferior).
4. Decidir si el umbral del haber mínimo (1,1 mínimos) y la inclusión de PNC quedan como están.
5. Si el INDEC publica el IPC con canasta ENGHo 2017/18 (postergado sin fecha en feb-2026) o una ENGHo
   nueva: cambiar la referencia de ponderaciones.

## 6. Rutina mensual (cuando el INDEC publica el IPC)

1. `git pull`. Actualizar `cuentas_publicas` (IMIG) si Hacienda publicó el mes.
2. Si hubo decreto de bono: agregar la fila en `data/reference/bono_previsional.csv` (aunque siga en
   $70.000; el control de calidad avisa si falta un mes).
3. `python scripts/construir.py --refrescar` (baja divisiones y aperturas).
4. `python scripts/control_calidad.py` → 0 ALERTAS; `python -m pytest tests -q`.
5. Actualizar §1-§2 (y los documentos de §3 cuando estén redactados). Commit + push.
6. Si el usuario corre los notebooks en Colab y pasa los ZIP: `python scripts/comparar_zip.py <zips>`.

## 7. PC nueva

```bash
git clone https://github.com/santiagoriverti/IPC_jubilados.git
cd IPC_jubilados
pip install -r requirements.txt
python scripts/construir.py          # baja IPC (divisiones y aperturas), ENGHo (~14 MB), haber y PIB (~1-2 min)
python scripts/control_calidad.py    # 0 ALERTAS
```

- Windows: `PYTHONUTF8=1` (o `set PYTHONUTF8=1`) antes de correr Python.
- Si `cuentas_publicas` no está clonado al lado (`../cuentas_publicas`), la IMIG se baja de GitHub.
  También se puede indicar con la variable de entorno `CUENTAS_PUBLICAS_DIR`.
- Probado con Python 3.14 (local) y 3.13 (Colab).
- Los archivos originales del TP (PDF, PPTX, XLSX) no están en el repo: si hacen falta, pedirlos al
  usuario y ponerlos en `docs/tp_original/` (ignorado por git).
