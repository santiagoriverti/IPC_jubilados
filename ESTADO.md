# ESTADO — IPC_jubilados (IIJP)

**Última actualización:** 2026-10-06 (sesión 1: armado del proyecto a partir del TP del Grupo 2).

## 1. Cobertura de datos

| Fuente | Último dato |
|---|---|
| IPC por división (INDEC) | ago-2026 |
| Haber mínimo (datos.gob.ar) | sep-2026 |
| Bono previsional (`data/reference/bono_previsional.csv`, manual) | sep-2026 ($70.000) |
| IMIG (vía `cuentas_publicas`) | ago-2026 |
| PIB nominal anual completo | 2025 |
| ENGHo | 2017/18 (canasta fija) |

## 2. Cifras vigentes (construir.py, bootstrap 500)

- Brecha IIJP vs IPC oficial: dic-16 → ago-26 **+1,32%**; nov-23 → ago-26 **+2,71%** (IC 2,37-3,09);
  ventana del TP nov-23 → may-26 **+2,39%** (TP: 3,84%).
- Efecto edad nov-23 → ago-26: **−0,69%** (IC −1,01 a −0,37); efecto canasta vieja +3,43%.
- Ago-2026: IPC 1,66% · IIJP 1,74% · IPC ENGHo 17/18 1,69%.
- Haber mínimo real (base nov-23): sin bono +10,1%, con bono −9,7% (IPC) en ago-26.
- Contrafactual IIJP desde abr-24: haber +0,87% en sep-26. Costo fiscal: 2024 (abr-dic) 0,23% del
  gasto previsional; 2025 0,13% (0,009% PIB); 2026 ene-ago 0,55%.

## 3. Próximos pasos posibles (a decidir con el usuario)

1. Devolución a los alumnos: `docs/revision_TP.md` está escrita como devolución; ¿compartirla así o
   resumida?
2. Subíndices dentro de Salud (medicamentos, prepagas) con `serie_ipc_aperturas.csv` del INDEC: el
   archivo de hogares de la ENGHo solo abre la división 09 (`gc09_*`); para separar medicamentos y
   prepagas hay que usar el archivo de gastos por artículo (`engho2018_gastos.zip`, ya en cache).
3. Canasta por nivel de haber usando el archivo de gastos por artículo (`engho2018_gastos.zip`, ya
   en cache) y precios por categoría.
4. Proyección demográfica 2050 (si se quiere rehacer la del TP): población 65+ del Banco Mundial
   (HNP) + tabla de desvío permanente; recordar que el costo relativo no depende de la demografía.
5. Página interactiva / dashboard: no por ahora.

## 4. Rutina mensual (cuando el INDEC publica el IPC)

1. Actualizar `cuentas_publicas` (IMIG) si Hacienda publicó el mes.
2. Si hay decreto de bono nuevo: agregar la fila en `data/reference/bono_previsional.csv`
   (aunque siga en $70.000).
3. `python scripts/construir.py --refrescar`
4. `python scripts/control_calidad.py` → 0 ALERTAS.
5. Actualizar §1-§2 de este archivo y, si cambian, las cifras del README. Commit + push.

## 5. PC nueva

```bash
git clone https://github.com/santiagoriverti/IPC_jubilados.git
cd IPC_jubilados
pip install -r requirements.txt
python scripts/construir.py   # baja IPC, ENGHo (~13 MB), haber y PIB a data/cache/
```

Si `cuentas_publicas` no está clonado al lado, el costo fiscal baja la IMIG desde GitHub.
