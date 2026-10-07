# ESTADO — IPC_jubilados (IIJP)

**Última actualización:** 2026-10-06 (cierre de la sesión 1). Punto de entrada para retomar: este
archivo → `CLAUDE.md` (reglas) → `CONTEXTO.md` (método y trampas) → `.claude/memory/project.md` (historial).

## 0. Estado en una línea

Proyecto funcionando y verificado (local + Colab). Datos a ago-2026. Sin trabajo a medias: lo único
pendiente es que el usuario vuelva a correr en Colab los notebooks 01 y 02 (sus ZIP anteriores son de
una versión vieja) y decidir los próximos pasos (§5).

## 1. Cobertura de datos

| Fuente | Último dato | Cómo se actualiza |
|---|---|---|
| IPC por división (INDEC) | ago-2026 | automático (`--refrescar`) |
| Haber mínimo (datos.gob.ar `58.1_MP_0_M_24`) | sep-2026 | automático |
| Bono previsional (`data/reference/bono_previsional.csv`) | sep-2026 ($70.000) | **manual**, una fila por mes |
| IMIG (vía repo `cuentas_publicas`) | ago-2026 | actualizar ese repo primero |
| PIB nominal anual completo (datos.gob.ar) | 2025 | automático |
| ENGHo | 2017/18 (canasta fija) | no cambia |

## 2. Cifras vigentes (`python scripts/construir.py`, bootstrap 500)

- **Ago-2026**: IPC 1,66% m/m y 33,5% i.a. · IIJP 1,74% y 34,5% · IPC ENGHo 17/18 1,69% y 34,5%.
- **Brecha IIJP vs IPC oficial**: dic-16 → ago-26 +1,32% (IC 1,07-1,57); Macri +2,77%;
  Fernández −4,01%; Milei (nov-23 → ago-26) +2,71% (IC 2,37-3,09); desde dic-24 +0,53%;
  ventana del TP (nov-23 → may-26) +2,39% (IC 2,06-2,75; el TP decía 3,84%).
- **Efecto edad** (IIJP vs IPC 17/18): completo +0,79%; Milei −0,69% (IC −1,01 a −0,37).
  **Efecto canasta vieja** (IPC 17/18 vs oficial): Milei +3,43%.
- Diferencia media mensual 2016-2026: 0,011 p.p. (IC Newey-West −0,035 a 0,058): no sistemática.
- **Canasta** (hogares jubilados, 5.350 en la muestra, 2,96 M expandidos): alimentos 26,4%, vivienda
  14,5%, salud 11,4%, transporte 11,3%, educación 0,8% (todos los hogares: 22,7 / 14,5 / 6,4 / 14,3 / 3,1).
- **Haber mínimo real** (base nov-23, ago-26): sin bono +10,1% (IPC) / +7,2% (IIJP); con bono −9,7%
  (IPC) / −12,1% (IIJP). Bono actualizado por IPC desde mar-24 sería $194.268.
- **Contrafactual IIJP desde abr-24**: haber +0,77% en sep-26 ($3.285/mes en la mínima).
- **Costo fiscal**: 2024 (abr-dic) $84.393 M = 0,28% del gasto previsional (0,014% PIB); 2025
  $98.318 M = 0,17% (0,012% PIB); 2026 ene-ago $205.402 M = 0,43%. Mayo 2026: $22.815 M.
- Movilidad: ANSES usa el IPC(t−2) desde niveles con 2 decimales (error 0 en 29/29 meses).

## 3. Dónde se citan las cifras (actualizar todo junto si cambian)

| Documento | Qué cifras |
|---|---|
| `README.md` | tabla de períodos, puntos 1-5 de Resultados, nota metodológica (5.350 hogares, 0,16%) |
| `docs/revision_TP.md` | tabla resumen (ventana del TP, haberes may-26/sep-26, costo may-26), M2 (tabla edad/canasta), B6 (bono) |
| `docs/informe_indicadores/seccion_iijp.tex` | sección LaTeX del informe INECO: ago-26 m/m e i.a., cuadro de períodos, canasta, haberes, costo |
| `ESTADO.md` §2 | todas |
| Markdown de `scripts/gen_notebooks.py` | lecturas cualitativas (+3,7 p.p. alimentos, 2,4% ventana TP, ±10% haber) |

## 4. Verificación

- `python -m pytest tests -q` → 7 passed.
- `python scripts/control_calidad.py` → 0 ALERTAS (réplica IPC 0,158%; canasta del TP 0,0006; regla de
  movilidad 29/29; contrafactual IPC = haber efectivo; bono cargado; IMIG sin huecos).
- Colab (2026-10-06): NB03 con commit `ea4ffc3` → `python scripts/comparar_zip.py <zip>` da 0
  diferencias no esperadas. **Pendiente**: el usuario vuelve a correr NB01 y NB02 (sus ZIP previos se
  generaron con módulos viejos en memoria: hojas Haberes/Fiscal con la regla de 1 decimal).

## 5. Próximos pasos posibles (a decidir con el usuario)

1. Devolución a los alumnos: `docs/revision_TP.md` está escrita como devolución (¿así o resumida?).
2. Informe INECO: la sección del IIJP está en `docs/informe_indicadores/seccion_iijp.tex`. Opcionales:
   sumar el gráfico `g03_brecha_historica.png`, una línea de crédito al TP del Grupo 2, o cambiar la
   sigla (IIJP vs una que siga el título "Índice de Precios de Jubilados Argentinos").
3. Subíndices de Salud (medicamentos vs prepagas) con `serie_ipc_aperturas.csv` del INDEC + archivo de
   gastos por artículo de la ENGHo (`engho2018_gastos.zip`, ya se descarga a cache): el archivo de
   hogares solo abre la división 09 (`gc09_*`).
4. Canasta por nivel de haber con el archivo de gastos por artículo.
5. Proyección 2050 (si se quiere rehacer la del TP): población 65+ del Banco Mundial (HNP) + tabla de
   desvío permanente; el costo relativo no depende de la demografía.
6. Página interactiva / dashboard: no por ahora.

## 6. Rutina mensual (cuando el INDEC publica el IPC)

1. `git pull`. Actualizar `cuentas_publicas` (IMIG) si Hacienda publicó el mes.
2. Si hubo decreto de bono: agregar la fila en `data/reference/bono_previsional.csv` (aunque siga en
   $70.000; el control de calidad avisa si falta un mes).
3. `python scripts/construir.py --refrescar`
4. `python scripts/control_calidad.py` → 0 ALERTAS; `python -m pytest tests -q`.
5. Actualizar §1-§2 y los documentos de §3 si cambian las cifras. Commit + push.
6. Si el usuario corre los notebooks en Colab y pasa los ZIP: `python scripts/comparar_zip.py <zips>`.

## 7. PC nueva

```bash
git clone https://github.com/santiagoriverti/IPC_jubilados.git
cd IPC_jubilados
pip install -r requirements.txt
python scripts/construir.py          # baja IPC, ENGHo (~13 MB), haber y PIB a data/cache/ (~1 min)
python scripts/control_calidad.py    # 0 ALERTAS
```

- Windows: `PYTHONUTF8=1` (o `set PYTHONUTF8=1`) antes de correr Python.
- Si `cuentas_publicas` no está clonado al lado (`../cuentas_publicas`), la IMIG se baja de GitHub.
  También se puede indicar con la variable de entorno `CUENTAS_PUBLICAS_DIR`.
- Probado con Python 3.14 (local) y 3.13 (Colab).
- Los archivos originales del TP (PDF, PPTX, XLSX) no están en el repo: si hacen falta, pedirlos al
  usuario y ponerlos en `docs/tp_original/` (ignorado por git).
