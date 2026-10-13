# ESTADO — IPC_jubilados (IIJP)

**Última actualización:** 2026-10-13 (sesión 2: rediseño metodológico). Punto de entrada para retomar:
este archivo → `CLAUDE.md` (reglas) → `CONTEXTO.md` (método y trampas) → `.claude/memory/project.md`
(historial).

## 0. Estado en una línea

Metodología nueva implementada, verificada en local y pusheada: el IIJP se valoriza **por región y al
nivel de aperturas del IPC**, con los restos no publicados deducidos de las ponderaciones oficiales del
INDEC. Incluye un subíndice **haber mínimo** y una **tabla de 19 variantes** de sensibilidad. Datos a
ago-2026. README y revision_TP al día. **Pendiente**: que el usuario corra los 3 notebooks en Colab y pase
los ZIP; reescribir la sección LaTeX del informe INECO con la metodología nueva.

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

- **Ago-2026**: IPC 1,66% m/m y 33,5% i.a. · IIJP 1,61% y 34,7% · IIJP haber mínimo 1,81% y 36,5% ·
  IPC ENGHo 17/18 1,52% y 34,6%.
- **Brecha IIJP vs IPC oficial**: dic-16 → ago-26 **+2,29%** (IC 1,88-2,70); Macri +3,16%; Fernández
  −4,45%; Milei (nov-23 → ago-26) **+3,78%** (IC 3,19-4,28); shock tarifario +3,33%; desde dic-24 +0,43%;
  ventana del TP +3,43%.
- **IIJP haber mínimo vs IPC oficial**: completo +4,43%; Milei +4,97% (IC 4,14-5,85).
- **Efecto edad** (IIJP vs IPC 17/18): completo **+2,01%** (IC 1,64-2,37); Macri +2,86%; Fernández −0,43%;
  Milei −0,40% (IC −0,89 a +0,10); desde dic-24 −0,87%. **Efecto canasta vieja** (IPC 17/18 vs oficial):
  completo +0,28%; Milei +4,20%.
- **Firmeza (19 variantes)**: mantienen el signo en todas la brecha vs IPC oficial en el período completo
  (1,3 a 4,5%), Macri, Fernández y Milei (2,7 a 8,6%), el efecto edad del período completo (0,8 a 4,1%) y
  de Macri, y el aumento del haber si se indexara por IIJP (0,8 a 7,4%). **No es firme** el signo del
  efecto edad en Milei (−0,75 a +0,78) ni desde 2025.
- Lo que explica la brecha en Milei (por apertura): prendas (los jubilados compran menos ropa, que subió
  menos), electricidad y gas y el resto de vivienda (agua), a favor; alquiler, restaurantes y recreación,
  en contra. Medicamentos resta en el efecto edad (subieron menos que prepagas).
- **Regiones** (IIJP vs IPC de la región, Milei): GBA +4,7%, Pampeana +1,9%, NOA +5,6%, NEA +8,9%,
  Cuyo +3,1%, Patagonia +5,1% (muestras chicas fuera de GBA y Pampeana).
- **Canasta** (hogares jubilados, 5.350 en la muestra, 2,96 M expandidos): alimentos 26,4%, vivienda
  14,5% (dentro de vivienda: alquiler 14%, electricidad y gas 51%), salud 11,4% (medicamentos 54%,
  prepagas 29%), transporte 11,3% (transporte público 27%). Haber mínimo (2.081 hogares, 40% de los
  jubilados): alimentos 32,9%, vivienda 16,5%, medicamentos 72% de salud, transporte público 43%.
- **Haber mínimo real** (base nov-23, ago-26): sin bono +10,1% (IPC) / +6,1% (IIJP) / +4,9% (IIJP haber
  mínimo); con bono −9,7% / −13,0% / −14,0%. Bono actualizado por IPC desde mar-24: $194.268.
- **Contrafactual desde abr-24** (sep-26): con IIJP el haber sería +1,95% ($8.350/mes en la mínima); con
  IIJP haber mínimo, +3,11% ($13.321).
- **Costo fiscal** (indexar por IIJP): 2024 (abr-dic) $391.577 M = 1,28% del gasto previsional (0,067% PIB);
  2025 $659.222 M = 1,16% (0,078% PIB); 2026 ene-ago $674.355 M = 1,42%. Mayo 2026: $88.533 M.
- Movilidad: ANSES usa el IPC(t−2) desde niveles con 2 decimales (error 0 en 29/29 meses).

## 3. Dónde se citan las cifras (actualizar todo junto si cambian)

| Documento | Estado |
|---|---|
| `ESTADO.md` §2 | al día: todas |
| `README.md` | al día: tabla de períodos (brecha, efecto edad, haber mínimo), puntos 1-6, nota metodológica (5.350 / 2.081 hogares, 254 componentes, 0,08%) |
| `docs/revision_TP.md` | al día: tabla resumen (ventana del TP, haberes may-26/sep-26, ejercicio dic-23, costo may-26, 2050), M1, M1b, M2 (tabla edad/canasta), M3, M4, M5, D |
| `docs/informe_indicadores/seccion_iijp.tex` | **desactualizada** (comentario en la cabecera): reescribir con la metodología nueva |
| Markdown de `scripts/gen_notebooks.py` | sin cifras fijas (las imprime el código) |

## 4. Verificación (2026-10-13)

- `python -m pytest tests -q` → 13 passed (6 nuevos de `tests/test_estructura.py`).
- `python scripts/control_calidad.py` → 0 ALERTAS: réplica del IPC nacional con la estructura de
  aperturas 0,081% (regiones ≤ 0,257%); agregados completos ≤ 0,056%; restos estables ante el redondeo
  (≤ 4,1%); 100% del gasto asignado; canastas suman 1; haber mínimo 39,6% de los jubilados; canasta del TP
  0,0006; regla de movilidad 29/29; contrafactual = haber efectivo; bono cargado; IMIG sin huecos.
- Notebooks ejecutados en local (`_local_run/`, bootstrap 30) y sus ZIP comparados con `construir.py`:
  0 diferencias no esperadas.
- Colab con `7c770cf` falló: la API de datos.gob.ar devolvió vacía la serie del haber mínimo (grupo
  haber mínimo = 0 hogares). Corregido (reintentos + CSV de respaldo + validaciones; CONTEXTO §5) y
  probado con una copia del repo sin caché: mismas cifras. **Falta**: volver a correr en Colab.

## 5. Próximos pasos posibles (a decidir con el usuario)

1. Corrida en Colab de los 3 notebooks (comparar los ZIP con `scripts/comparar_zip.py`).
2. Sección LaTeX del informe INECO (metodología por aperturas, tabla de firmeza, subíndice haber mínimo)
   y, si se quiere, una versión resumida de la devolución a los alumnos.
3. Precios propios de los jubilados (limitación conceptual): cobertura de PAMI en medicamentos, tarifa
   social de transporte, segmentación de subsidios energéticos. Requiere datos fuera del IPC.
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
