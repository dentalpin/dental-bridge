# Decodificación del odontograma Gesdén

Gesdén guarda el odontograma **embebido en la línea del tratamiento** (`TtosMed` y `PresuTto`) usando varios campos numéricos a modo de bit-mask. No hay tabla maestra de "diente".

## Campos involucrados

| Campo         | Tipo            | Observación en `SOURCE_DB`                           |
|---------------|-----------------|---------------------------------------------------------|
| `PiezasAdu`   | `numeric`       | Bit-mask de **piezas adultas** (permanente). Pocos valores no nulos. |
| `PiezasLec`   | `numeric`       | Bit-mask de **piezas leche** (decidua). Casi siempre 0 en este DB.   |
| `PiezasNum`   | `numeric`       | Casi siempre 0; 2 valores observados (1 y 1024). Probablemente legacy. |
| `ZonasPieza`  | `numeric`       | Bit-mask **principal**. Codifica tooth × surface. Valores grandes (hasta 4.136.042.496 ≈ 2^32). |
| `ZonasBoca`   | `tinyint`       | Siempre 0 en este DB → **ignorar**.                                     |
| `Cuadrantes`  | `numeric`       | Siempre 0 → **ignorar**.                                                |
| `Arcadas`     | `numeric`       | Siempre 0 → **ignorar**.                                                |
| `Edu10..Edu24`| `tinyint` × 10  | Vacíos (sum=0) → **ignorar (legacy)**.                                  |
| `DespX`, `DespY`, `Rotacion` | `int` | Desplazamiento/rotación visual del símbolo. Migrar opcionalmente. |
| `IdTipoOdg`   | `int` → `TTipoOdg` | Tipo de marca odontográfica (46 valores: obturación, corona, extracción, higiene, etc.) |

## Frecuencia observada de `ZonasPieza`

(top 20 valores por frecuencia, ver `sql/exploration/05_odontograma_samples.sql`
para reproducirlo en tu propia instalación)

```
1073741824 → 2^30
16777216   → 2^24
67108864   → 2^26
268435456  → 2^28
1073872896 → bits 30+17+...
75563008   → bits combinados
302252032  → bits combinados
301989888  → bits 28+29
16908288   → bits 24+17+...
8388608    → 2^23
75497472   → bits combinados
33554432   → 2^25
131072     → 2^17
3758096384 → bits 30+31+...
536870912  → 2^29
2147483648 → 2^31
604045312  → bits combinados
58720256   → bits combinados
2415919104 → bits 30+31
2416181248 → bits combinados
```

Conclusión: **`ZonasPieza` lleva la información dental real en este DB**. `PiezasAdu`/`PiezasLec`/`PiezasNum` están infrautilizados.

## Hipótesis de codificación

Sin documentación oficial. Estado actual:

1. `ZonasPieza` es un entero de 32 bits (cabe en `numeric` sin problema).
2. Los bits no parecen ser "1 bit por diente" puro (con 32 dientes adultos sería justo, pero los valores combinados como `1073872896` activarían múltiples bits que no encajan con un único diente).
3. Más probable: **bits agrupados en bloques de N por diente**, donde cada bloque codifica las superficies (M-O/I-D-V-L = 5) o un subconjunto.
4. Hipótesis a verificar: **6 bits × 5 dientes** ≈ 30 bits útiles (mesial, distal, oclusal, vestibular, lingual + presencia). Cubre los valores hasta 2^30. Pero los valores >2^31 (`3758096384`, `4136042496`) descartan esto.
5. Hipótesis alternativa: cada bit representa una "(diente, cara)" del **cuadrante específico al que aplica este tratamiento** (campo separado que aún no se ha encontrado). Esto explicaría que un mismo `ZonasPieza` aparezca con distintos significados según `IdTipoOdg`.

**Acción requerida**: validación con la UI de Gesdén original — abrir un paciente con tratamientos conocidos y comparar visualmente con los valores numéricos. Sin ese contraste, decodificar a ciegas es arriesgado.

## Plan de validación

1. Identificar 10 pacientes con tratamientos representativos (1 obturación simple, 1 endodoncia, 1 corona, 1 extracción, 1 implante, 1 higiene, 1 protesis, 1 ortodoncia, 1 carilla, 1 sellado). Query candidatos en `sql/exploration/06_odontograma_validation_candidates.sql`.
2. Anotar `ZonasPieza`, `PiezasAdu`, `PiezasLec`, `IdTipoOdg`, `IdTto` para cada uno.
3. Abrir Gesdén Windows con la BBDD original y capturar pantalla del odontograma de cada paciente.
4. Mapear visualmente: "este bit corresponde a este (diente, cara)".
5. Documentar tabla `bit → (FDI, surface)` en este fichero.
6. Implementar función de decodificación en el asistente Windows con tests unitarios contra estos 10 casos.

## Posición / rotación

- `DespX`, `DespY` (int): desplazamiento del símbolo dentro de la celda del diente.
- `Rotacion` (int): rotación visual (grados o índice de orientación).

Estos no son críticos para Dentalpin si su odontograma usa otro paradigma; pueden migrar como metadata.

## Tipos de operación (`TTipoOdg`) — relevantes para el odontograma

Ver `docs/schema_map.md` para la lista completa. Para decodificación, el subconjunto crítico es:

| ID  | Descripción          | Implicación visual                           |
|----:|----------------------|----------------------------------------------|
| 4   | Pieza Niño           | Diente decidua presente                      |
| 5   | Pieza Adulto         | Diente permanente presente                   |
| 6   | SuperNumeraria       | Diente extra                                 |
| 21  | Endodoncia           | Marca raíz                                   |
| 22  | Obturaciones         | Marca superficie(s) M/O/D/V/L                |
| 24  | Implante             | Reemplazo de raíz                            |
| 26  | Corona               | Corona completa                              |
| 27  | Puente               | Puente entre dientes (multi-pieza)           |
| 33  | Carilla              | Cara V (vestibular)                          |
| 36  | Extracción Corona    | Solo corona extraída                         |
| 37  | Extracción Pieza     | Diente completo ausente                      |
| 38  | Higiene              | Sin pieza concreta (boca completa)           |

`IdTipoOdg` debería usarse junto con `ZonasPieza` para interpretar correctamente el bit-mask: una "obturación 22" marca caras; una "extracción 37" marca diente entero; una "higiene 38" no marca ningún diente.

## Conclusión operativa

Para el asistente Windows:

- **No bloquear la migración por el odontograma**. Migrar primero pacientes, citas, presupuestos, pagos y deudas (datos administrativos/contables). Validable con números agregados.
- Marcar el odontograma como **fase 2** de la migración, con flag "odontograma_pendiente" en cada `TtosMed` migrado.
- Hacer la validación contra Gesdén UI antes de la fase 2.
- Si Dentalpin permite cargar un odontograma "tal cual" sin decodificar (campo BLOB / JSON), volcarlo como está y dejar la traducción visual para el frontend.
