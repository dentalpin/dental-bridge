# Orden de migración Gesdén → Dentalpin

Orden topológico de carga derivado de las FKs reales (ver `docs/schema_map.md`). Respetarlo evita violaciones de FK al insertar en Dentalpin (asumiendo modelo destino similar al origen). Si Dentalpin tiene un modelo distinto, este orden sigue siendo correcto **a nivel de extracción** desde Gesdén.

## Niveles

Cada nivel es independiente; dentro del nivel las tablas pueden cargarse en paralelo. Pasar al siguiente nivel solo cuando el anterior haya terminado.

### Nivel 0 — Catálogos sin dependencias externas

- `TPaises`
- `TProvin`
- `TPoblaci`
- `TECivil`
- `TTrato`
- `TProfesi`
- `TEspecOMC`
- `TiposCliente`
- `TEstados`
- `TForPago`
- `Bancos`
- `Emisores`
- `Idioma`
- `TRefer`
- `TProced`
- `TSitCita`
- `TBoxes`
- `TMRecall`
- `TRRecall`
- `TMotivoAsignacion`
- `TTipoOdg`
- `IconoTratAgenda`
- `TiposPresupuestos`
- `TSeries`
- `TGrAgdOpc`
- `Partners`

### Nivel 1 — Estructura organizativa

- `Centros` (necesita `TPoblaci`)
- `TUsers` (necesita `TEspecOMC`, `Emisores`, `TColabos` para `IdCol`)
- `Tarifas`
- `TCalCa` (calendarios por centro — base)
- `TCalDias` (días laborables / festivos)
- `TCalHor` (franjas horarias)

### Nivel 2 — Profesionales y catálogo clínico

- `TColabos` (necesita `TProfesi`, `TPoblaci`, `TEspecOMC`, `Emisores`)
- `Centros_TColabos` (necesita ambos)
- `TUCentros` (necesita `TUsers` + `Centros`)
- `Tratamientos` (necesita `TEspecOMC`, `TTipoOdg`)
- `TratamientosFases` (necesita `Tratamientos`)
- `Tratamientos_Tarifas` (necesita `Tratamientos` + `Tarifas`)
- `Tratamientos_Tarifas_Precios` (necesita `Tratamientos_Tarifas`)
- `TAuxFarmacos`

### Nivel 3 — Pagadores y pacientes

- `Clientes` (necesita Nivel 0 + `Centros` + `Bancos` + `Emisores`)
- `Pacientes` (necesita `Clientes` + `TColabos` + `Centros` + catálogos Nivel 0)
- `PacCli` (necesita `Pacientes` + `Clientes`)
- `Pacientes_Tarifas` (necesita `Pacientes` + `Tarifas`)

### Nivel 4 — Agenda

- `TUsuAgd` (necesita `TUsers`)
- `DCitasPeriod` (cabecera de citas recurrentes — debe ir antes de `DCitas` con `IdCitasP` no nulo)
- `DCitas` (necesita `Pacientes`, `Clientes`, `Centros`, `TColabos`, `TBoxes`, `TSitCita`, `TUsuAgd`, `TRefer`, `TProced`, `Tarifas`, `Partners`, `TGrAgdOpc`, `DCitasPeriod`)
- `DCitasOp` (necesita `DCitas`)
- `DCitasF` (cerradas/históricas — si decides incluirlas)

### Nivel 5 — Presupuestos y tratamientos

- `Presu` (necesita `Pacientes`, `TColabos`, `Centros`, `TUsers`, `TiposPresupuestos`, `TMotivoAsignacion`, `Canastas_TDiagnosticos`)
- `PresuTto` (necesita `Presu` + `Tratamientos_Tarifas` + `Pacientes` + `Clientes` + `TColabos`)
- `PresuTipoTto`, `PresuTtoDto` (necesitan `Presu`)
- `TtosMed` (necesita `Pacientes`, `Clientes`, `TColabos`, `Centros`, `Tratamientos_Tarifas`, `TEspecOMC`, `TTipoOdg`, `TRefer`, `TProced`, `Emisores`, `CCDiagnosticos`, `TUsers`)
- `TtosMedFases` (necesita `TtosMed` + `TratamientosFases` + `TColabos`)

### Nivel 6 — Facturación y tesorería

- `DocAdmin` (necesita `Clientes`, `Emisores`, `TSeries`, `TUsers`, `TMotivoAsignacion`)
- `PagoCli` (necesita `Clientes`, `Centros`, `TForPago`, `Bancos`, `TUsers`, `TtosMed`, `TMotivoAsignacion`, `PasarelaPago`, `RemesasBancarias`, `PlanEcoL`)
- `DeudaCli` (necesita `Pacientes`, `Clientes`, `Centros`, `TtosMedFases`)
- `DeudaPago` (necesita `DeudaCli`, `PagoCli`, `DocAdmin`)
- `LinAdmin` (necesita `DocAdmin`, `DeudaCli`, `PagoCli`, `DeudaPago`, `Pacientes`)
- `RegApun` (necesita `TUsers`, `TRegApun`, `TForPago`, `Pacientes`, `Clientes`, `TColabos`, `Centros`)
- `BancoMov` (necesita `Bancos`)

### Nivel 7 — Datos clínicos secundarios

- `TTratamientos` (medicación / antecedentes — necesita `Pacientes`, `TUsers`, `Centros`)
- `RecetasCab` (necesita `Pacientes`, `TUsers`, `TColabos`, `Emisores`, `Centros`)
- `RecetasDet` (necesita `RecetasCab`)
- `TConsinCab` (necesita `Pacientes`, `TUsers`, `TColabos`)
- `TConsinDet` (necesita `TConsinCab`)
- `TDocumentosPac` (necesita `Pacientes`, `TUsers`)
- `ExplPerio` (periodontograma — si existe contenido relevante)
- `OrtDefaulds` (ortodoncia)

### Nivel 8 — Recall y comunicaciones

- `Recalls` (necesita `Pacientes`, `TColabos`, `Centros`, `TMRecall`, `TRRecall`, `DCitas`, `Presu`, `TtosMed`)
- `AlertPac` (necesita `Pacientes`, `Centros`)
- `EdMail`, `EdMailL`, `EdDocs`, `PacMensajes`

## Reglas transversales

1. **Generar tabla de remapeo de IDs** durante la carga: por cada tabla origen, mantener mapping `id_origen → id_destino` (en SQLite local del asistente). Usar este mapping al insertar tablas hijas.
2. **Validar `Guid_Tenant`** antes de empezar: el asistente debe asumir 1 solo tenant; si encuentra varios, parar y avisar.
3. **Filtrar `IdCentro = -1`** o reasignar al centro destino elegido por el usuario.
4. **Anulaciones encadenadas**: en `PagoCli` y `DocAdmin`, ordenar `IdAnulado IS NULL` y `IdDocAdminOrigen IS NULL` primero, después el resto.
5. **Borrados lógicos**: respetar `Inactivo`/`FecBaja`/`Anulacion` — mapear a flag de soft-delete en Dentalpin.
6. **Fechas centinela**: descartar `1900-01-01` y similares (vistas en `TtosMed.FecIni` mín, `Presu.FecPresup` mín). Mapear a NULL.
7. **Pacientes fallecidos** (`Pacientes.Exitus`): trasladar pero marcar como inactivo en Dentalpin.
8. **`DCitas.Fecha`/`Hora`** como int: aplicar conversión antes de insertar.
9. **Self-FKs en dos pasadas**: tablas con auto-referencia (`Pacientes.IdPacReferidor`, `Clientes.IdCIA`, `PagoCli.IdAnulado`/`IdPagoCliRelacionado`, `DocAdmin.IdDocAdminOrigen`, `Presu.AlternativaDe`/`Id_PresuOriginal`, `Recalls.IdRecallOrigen`) se cargan con la self-FK a NULL en la 1ª pasada y se actualizan en una 2ª pasada usando el mapping origen→destino.
10. **Doble vínculo `Presu`/`PresuTto` ↔ `TtosMed`**: insertar `Presu` + `PresuTto` con `IdTtoMedOrig=NULL` → insertar `TtosMed` resolviendo `IdPresuTto` → UPDATE `PresuTto.IdTtoMedOrig`.
11. **Adjuntos en filesystem**: antes de migrar, verificar acceso a la carpeta donde Gesdén guarda los archivos referenciados por `TDocumentosPac.Original` y `Pacientes.Foto`. Sin esto, esos campos quedan como referencia rota.
12. **Documentos fiscales** (`DocAdmin`, `Presu` con `Hash`/`CodigoATCUD`/`CodigoQR`): cargar como **registros inmutables**, sin pasarlos por el motor de numeración/firma de Dentalpin. Etiquetar como `origen='gesden_legacy'`.
13. **No migrar `Saldos`**: recalcular tras cargar `DeudaCli` y `PagoCli`.
14. **No migrar passwords**: forzar reset email para todos los `TUsers` creados en Dentalpin.
15. **No re-lanzar pagos**: `PagoCli` con `IdPasarelaPago`/`IdRemesaBancaria`/`NumTransaccion` solo como histórico.
16. **Encoding CP1252**: forzar codepage 1252 al leer strings de Gesdén; validar con `Apellidos LIKE '%ñ%'` antes del bulk.
17. **`TConsinDet`**: migrar solo el render de `TConsinCab.Texto`/`Html`; los pares clave-valor son inútiles sin la plantilla original (no está en BBDD).
18. **Calendarios laborables** (`TCalDias`, `TCalHor`, `TCalCa`) cargar antes que `DCitas`, en Nivel 1 ó 2.
19. **Citas periódicas**: `DCitasPeriod` antes que `DCitas` (ya en Nivel 4, pero respetar el subgrafo).
20. **Multi-centro por colaborador**: poblar `Centros_TColabos` después de `TColabos` y `Centros`. Si Dentalpin solo permite 1 centro/doctor, decidir centro principal en pre-fly check.
21. **Tutores duplicados**: antes de cargar `Pacientes`, deduplicar el conjunto `Clientes ∪ Pacientes` por NIF para evitar que `IdCliTutor` apunte a un cliente que también es paciente cargado por separado.

## Verificación post-carga

Por cada nivel, comparar conteos origen vs destino (filtrado por tenant/centro elegido):

```sql
-- ejemplo
SELECT 'origen' AS src, COUNT(*) FROM SOURCE_DB.dbo.Pacientes WHERE Guid_Tenant = @t
UNION ALL
SELECT 'destino', COUNT(*) FROM dentalpin.patients WHERE clinic_id = @c;
```

Discrepancias > 1 % → revisar log de errores del asistente y la tabla
`LogErrores` de la base de datos origen (suele contener pistas de
problemas históricos acumulados).
