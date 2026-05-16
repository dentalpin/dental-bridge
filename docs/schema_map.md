# Schema map — Gesdén `SOURCE_DB` → Dentalpin

Documento de referencia para diseñar el asistente Windows de migración. Resume tablas de origen, FKs descubiertas y campos relevantes para cada entidad lógica de Dentalpin.

> Volúmenes expresados como **órdenes de magnitud** sobre una BBDD de
> desarrollo de tamaño medio. No son conteos exactos de ninguna clínica
> identificable. Para refrescar contra tu propia copia local ejecuta
> `sql/exploration/01_inventory.sql`.

## Convenciones de origen (Gesdén)

| Prefijo  | Significado                                |
|----------|--------------------------------------------|
| `T*`     | Catálogo / tabla maestra                   |
| `D*`     | Detalle (`DCitas` = detalle citas)         |
| `_*`     | Migración / helpers internos Gesdén        |
| `Z*`     | Metadatos del propio schema Gesdén         |
| `S1_*`   | Auth interno Gesdén                        |
| `IS4_*`  | IdentityServer4 (auth Gesdén)              |
| `CDM*`   | Dashboards / widgets Gesdén                |
| `ATMT_*` | Automatizaciones / plantillas              |
| `PLG_*`  | Plugins de terceros                        |
| `Sch_*`  | Scheduler nuevo (no usado, 0 filas)        |

Sufijos de auditoría en (casi) todas las tablas: `_version`, `_fechaReg`, `_idUserReg`, `_fechaModif`, `_idUserModif`, `Guid_Tenant`.

## Resumen de mapeo

| Dentalpin (entidad)           | Gesdén (tabla principal)       | PK origen                  | Magnitud     | Auxiliares                                                                                |
|-------------------------------|--------------------------------|----------------------------|--------------|-------------------------------------------------------------------------------------------|
| Clínica / Sede                | `Centros`                      | `IdCentro` int             | unidades     | `TUCentros`                                                                               |
| Usuario sistema               | `TUsers`                       | `IdUser` int               | decenas      | `S1_Roles`, `S1_PermisosApp`                                                              |
| Profesional (doctor/auxiliar) | `TColabos`                     | `IdCol` int                | decenas      | `Centros_TColabos`, `TProfesi`, `TEspecOMC`                                               |
| Paciente                      | `Pacientes`                    | `IdPac` int                | ~10⁴         | `AlertPac`, `PacientesLog`, `PacCli`, `Pacientes_Tarifas`                                 |
| Cliente / Pagador             | `Clientes`                     | `IdCli` int                | ~10⁴         | `PacCli`, `Bancos`                                                                        |
| Relación paciente↔pagador     | `PacCli`                       | `(IdPac, IdCli)`           | ~10⁴         | —                                                                                         |
| Cita                          | `DCitas`                       | `IdCita` bigint            | ~10⁵         | `DCitasOp`, `DCitasF`, `TUsuAgd`, `TSitCita`, `TBoxes`                                    |
| Catálogo tratamiento          | `Tratamientos`                 | `IdTratamiento` int        | centenas     | `TratamientosFases`, `Tratamientos_Tarifas`, `Tratamientos_Tarifas_Precios`               |
| Tratamiento aplicado          | `TtosMed`                      | `Ident` int identity       | ~10⁵         | `TtosMedFases`                                                                            |
| Presupuesto                   | `Presu`                        | `Ident` int identity       | ~10⁴         | `PresuTto`, `PresuTipoTto`, `PresuTtoDto`                                                 |
| Factura / Recibo              | `DocAdmin`                     | `Ident` int identity       | ~10⁴         | `LinAdmin`, `TSeries`                                                                     |
| Pago                          | `PagoCli`                      | `IdPagoCli` int            | ~10⁴         | `TForPago`, `Bancos`                                                                      |
| Deuda                         | `DeudaCli`                     | `IdDeudaCli` int           | ~10⁵         | `DeudaPago`, `PlanEcoL`                                                                   |
| Conciliación tesorería        | `RegApun`                      | `IdRegApun` int            | ~10⁵         | `TRegApun`, `BancoMov`                                                                    |
| Receta                        | `RecetasCab`                   | `IdRecetaIdent` int        | ~10⁴         | `RecetasDet`, `TAuxFarmacos`                                                              |
| Historial farmacológico       | `TTratamientos` (no catálogo)  | `(IdPac, IdTrat)` + CId    | ~10⁴         | —                                                                                         |
| Consentimiento                | `TConsinCab`                   | `IdConsin` int             | ~10⁴         | `TConsinDet` (pares clave-valor)                                                          |
| Documento / adjunto           | `TDocumentosPac`               | `IdDocPac` int             | ~10⁴         | `DocsFirmados`, `MailboxSignedDocuments`                                                  |
| Recall                        | `Recalls`                      | `Id` int                   | millares     | `RecallsLog`, `TMRecall`, `TRRecall`                                                      |
| Alerta paciente               | `AlertPac`                     | `Id` int                   | ~10⁴         | —                                                                                         |
| Comunicaciones (email)        | `EdMailL`                      | —                          | ~10⁴         | `EdMail`, `EdDocs`, `PacMensajes`                                                         |
| Periodontograma               | `ExplPerio`                    | —                          | escaso       | (validar uso real)                                                                        |

## Catálogos auxiliares

| Tabla                  | Función                                |
|------------------------|----------------------------------------|
| `Centros`              | Sedes (incluye centinela `-1` "sin centro") |
| `TUsers`               | Usuarios login                         |
| `TColabos`             | Profesionales                          |
| `TProfesi`             | Categorías profesionales               |
| `TEspecOMC`            | Especialidades OMC                     |
| `Tratamientos`         | Actos catálogo                         |
| `Tratamientos_Tarifas` | Versión por tarifa                     |
| `TForPago`             | Formas de pago                         |
| `Bancos`               | Bancos                                 |
| `TPoblaci`             | Poblaciones                            |
| `TProvin`              | Provincias                             |
| `TPaises`              | Países                                 |
| `TRefer`               | Procedencias                           |
| `TProced`              | Procedimientos clínicos                |
| `TSitCita`             | Estados de cita                        |
| `TBoxes`               | Boxes / sillones                       |
| `TMRecall`             | Motivos de recall                      |
| `TRRecall`             | Resultados de recall                   |
| `Emisores`             | Emisores factura                       |
| `TiposCliente`         | Tipos de cliente                       |
| `TTrato`               | Tratos formales (Sr/Sra/Dr…)           |
| `TECivil`              | Estado civil                           |
| `TTipoOdg`             | Tipos de odontograma                   |
| `IconoTratAgenda`      | Iconos visuales agenda                 |

## Estados (`TtosMed.StaTto`) — observados

| Valor | Frecuencia relativa | Hipótesis              |
|------:|:--------------------|------------------------|
| 5     | dominante           | Realizado / facturable |
| 3     | frecuente           | Presupuestado          |
| 8     | minoritario         | (validar)              |
| 2     | residual            | (validar)              |
| 4     | residual            | (validar)              |
| 6     | residual            | (validar)              |
| 1     | residual            | (validar)              |

> Validar con `SELECT * FROM TStaTto` si la tabla existe en tu instalación;
> si no, contrastar la semántica de cada valor contra la UI de Gesdén.

## Tipos de odontograma (`TTipoOdg`) — 46 valores

`1` Piezas Iniciales · `2` Posición Diente · `3` Rotación Diente · `4` Pieza Niño · `5` Pieza Adulto · `6` SuperNumeraria · `7` Bandas · `8` Brackets · `9` Nuevo Paciente · `10` Visita No Atendida · `11` Anotación · `12` Nota Económica · `13` Primera Visita · `14` Bonos · `21` Endodoncia · `22` Obturaciones · `23` Apicectomía · `24` Implante · `25` Perno-Muñón · `26` Corona · `27` Puente · `28` Prótesis Removible · `29` Injertos · `30` Membranas · `31` Fibras · `32` Sellado · `33` Carilla · `34` Raspado · `35` Cirugía · `36` Extracción Corona · `37` Extracción Pieza · `38` Higiene · `39` Panorámicas · `40` Teleradio · `41` Fluorización · `42` Genérico · `44` Rechazo Implante · `45` Retirada Implante · `46` Reposición Implante

## FKs descubiertas (núcleo)

Generadas vía `sys.foreign_keys`. Solo las relevantes al core; lista completa en `sql/exploration/02_foreign_keys.sql`.

```
Pacientes.IdCli                → Clientes.IdCli
Pacientes.IdCliPac             → Clientes.IdCli
Pacientes.IdCliDefec           → Clientes.IdCli
Pacientes.IdCliTutor           → Clientes.IdCli
Pacientes.IdCol                → TColabos.IdCol
Pacientes.IdCentro             → Centros.IdCentro
Pacientes.IdMutDefec           → Tarifas.IdTarifa
Pacientes.IdPacReferidor       → Pacientes.IdPac (auto)
Pacientes.IdPoblacio           → TPoblaci.IdPoblacio
Pacientes.IdRefDes/IdRefOri    → TRefer.IdRef
Pacientes.IdProfesio           → TProfesi.IdProfesio
Pacientes.IdEcivil             → TECivil.IdECivil
Pacientes.IdEstado             → TEstados.IdEstado
Pacientes.IdTrato              → TTrato.IdTrato
Pacientes.IdPaisIdent          → TPaises.IdPais
PacCli.IdPac                   → Pacientes.IdPac
PacCli.IdCli                   → Clientes.IdCli
Clientes.IdCIA                 → Clientes.IdCli (auto)
Clientes.IdBanco               → Bancos.IdBanco
Clientes.IdEmisor              → Emisores.IdEmisor
Clientes.Id_TipoCliente        → TiposCliente.Id
DCitas.IdPac                   → Pacientes.IdPac
DCitas.IdCli                   → Clientes.IdCli
DCitas.IdCentro                → Centros.IdCentro
DCitas.IdSitC                  → TSitCita.IdSitC
DCitas.IdBox                   → TBoxes.IdBox
DCitas.IdUsu                   → TUsuAgd.IdUsu
DCitas.IdUserIns               → TUsers.IdUser
DCitas.IdCitasP                → DCitasPeriod.IdCitasP
DCitas.IdRef                   → TRefer.IdRef
DCitas.IdProced                → TProced.IdProced
DCitas.IdPartner               → Partners.IdPartner
DCitas.IdIcono                 → IconoTratAgenda.IdIcono
DCitas.IdTarifa                → Tarifas.IdTarifa
DCitas.IdGrAgdOpc              → TGrAgdOpc.IdGrAgdOpc
TtosMed.IdPac                  → Pacientes.IdPac
TtosMed.IdCli                  → Clientes.IdCli
TtosMed.IdCol                  → TColabos.IdCol
TtosMed.IdCentro               → Centros.IdCentro
TtosMed.IdTto                  → Tratamientos_Tarifas.IdTratamientoTarifa
TtosMed.IdTipoEspec            → TEspecOMC.IdTipoEspec
TtosMed.IdTipoOdg              → TTipoOdg.IdTipoOdg
TtosMed.IdRef                  → TRefer.IdRef
TtosMed.IdProced               → TProced.IdProced
TtosMed.IdEmisor               → Emisores.IdEmisor
TtosMed.IdCCDiagnostico        → CCDiagnosticos.Id
TtosMed.IdUserEdit             → TUsers.IdUser
TtosMed.NumTransaccion         → TransaccionTratamiento.Id
TtosMed.IdPlanEcoCuota         → PlanEcoL.Id
TtosMedFases.IdTtosMed         → TtosMed.Ident
TtosMedFases.IdTratamientoFase → TratamientosFases.IdTratamientoFase
TtosMedFases.IdCol/IdColAux    → TColabos.IdCol
TtosMedFases.IdLiqComisionDet  → LiqComisionDet.IdLiqComisionDet
Presu.IdPac                    → Pacientes.IdPac
Presu.IdCol                    → TColabos.IdCol
Presu.IdCentro                 → Centros.IdCentro
Presu.IdUserElabora            → TUsers.IdUser
Presu.IdUserPresentacion       → TUsers.IdUser
Presu.IdUserResponsable        → TUsers.IdUser
Presu.IdUserRechaz             → TUsers.IdUser
Presu.AlternativaDe            → Presu.Ident (auto)
Presu.Id_PresuOriginal         → Presu.Ident (auto)
Presu.IdCanastaDiagnostico     → Canastas_TDiagnosticos.Id
Presu.IdTipoPresupuesto        → TiposPresupuestos.IdTipoPresupuesto
Presu.Id_MotivoRechaz          → TMotivoAsignacion.Ident
PresuTto.Id_Presu              → Presu.Ident
PresuTto.IdTto                 → Tratamientos_Tarifas.IdTratamientoTarifa
PresuTto.IdTtoMedOrig          → TtosMed.Ident
PresuTto.IdPac/IdCli/IdCol     → Pacientes/Clientes/TColabos
PagoCli.IdCli                  → Clientes.IdCli
PagoCli.IdCentro               → Centros.IdCentro
PagoCli.IdForPago              → TForPago.IdForPago
PagoCli.IdentTM                → TtosMed.Ident
PagoCli.IdAnulado              → PagoCli.IdPagoCli (auto)
PagoCli.IdMotivo               → TMotivoAsignacion.Ident
PagoCli.IdPagoCliRelacionado   → PagoCli.IdPagoCli (auto)
PagoCli.IdPasarelaPago         → PasarelaPago.Id
PagoCli.IdRemesaBancaria       → RemesasBancarias.Id
PagoCli.NumTransaccion         → TransaccionTratamiento.Id
PagoCli.IdPlanEcoCuota         → PlanEcoL.Id
DeudaCli.IdPac                 → Pacientes.IdPac
DeudaCli.IdCli                 → Clientes.IdCli
DeudaCli.IdCentro              → Centros.IdCentro
DeudaCli.IdentTM               → TtosMedFases.IdTtosMedFase
DeudaCli.IdLiqComisionDet      → LiqComisionDet.IdLiqComisionDet
DeudaPago.IdDeudaCli           → DeudaCli.IdDeudaCli
DeudaPago.IdPagoCli            → PagoCli.IdPagoCli
DeudaPago.IdDocAdminDeuda      → DocAdmin.Ident
Recalls.IdPac                  → Pacientes.IdPac
Recalls.IdCol                  → TColabos.IdCol
Recalls.IdCentro               → Centros.IdCentro
Recalls.IdMotivo               → TMRecall.IdMotivo
Recalls.IdResultado            → TRRecall.IdTRRecall
Recalls.IdOrdenCita            → DCitas.IdOrden
Recalls.Id_Presu               → Presu.Ident
Recalls.Id_TtosMed             → TtosMed.Ident
Recalls.IdRecallOrigen         → Recalls.Id (auto)
AlertPac.IdPac                 → Pacientes.IdPac
AlertPac.IdCentro              → Centros.IdCentro
TDocumentosPac.IdPac           → Pacientes.IdPac
```

## Campos de auditoría comunes

| Campo                 | Tipo                | Significado                                          |
|-----------------------|---------------------|------------------------------------------------------|
| `_version`            | int                 | Versión de fila (lock optimista)                     |
| `_fechaReg`/`_fechareg` | datetime          | Creación                                             |
| `_idUserReg`/`_iduser` | int                | Usuario que creó                                     |
| `_fechaModif`         | datetime            | Última modificación                                  |
| `_idUserModif`        | int                 | Usuario que modificó                                 |
| `Guid_Tenant`         | uniqueidentifier    | Tenant (multi-tenant)                                |
| `ExternalId`          | uniqueidentifier    | ID externo (sync con servicios cloud Gesdén)         |
| `CId`                 | nvarchar            | Correlation ID para pasarelas/transacciones          |

## Tablas a IGNORAR

- `_LiqComision_mig`, `_TAuxRelTToConActo` — helpers internos Gesdén.
- `Z*` (`ZSistema`, `ZUpdatBD`, `ZUpdatDT`) — metadatos schema.
- `S1_*`, `IS4_*` — auth Gesdén (Dentalpin tiene su propio sistema).
- `CDM*`, `Widgets` — dashboards.
- `ATMT_*` — automatizaciones Gesdén.
- `dtproperties`, `sysdiagrams` — SQL Server.
- `*_History`, `*_Historico`, `*Log` — auditoría (opcional, solo si exige el cliente).
- `PLG_*` — plugins terceros (caso por caso).
- Tablas con 0 filas: `TVisita*`, `Sch_*`, `Stocks_*`, `ATMT_*`, `PLG_0013_HISTORIAL`, `TipusVisita*`, `*_History`.

## Riesgos / gotchas

Ver `gesden_explorer/docs/odontograma_decoding.md` para el detalle del codificado de piezas.

| # | Riesgo                                                                    | Mitigación                                                          |
|--:|---------------------------------------------------------------------------|---------------------------------------------------------------------|
| 1 | `DCitas.Fecha`/`Hora` son **enteros** formato Gesdén                       | Helper de conversión dedicado (`int → DateTime`) antes de cargar    |
| 2 | Odontograma codificado bit-mask en `ZonasPieza`/`PiezasAdu`/`PiezasLec`    | Algoritmo en `odontograma_decoding.md`; validar contra UI Gesdén    |
| 3 | `TTratamientos` ≠ `Tratamientos` (historial farmacológico vs catálogo)    | Documentación explícita; nombres distintos en código del asistente  |
| 4 | Paciente↔Cliente N:N vía `PacCli`                                          | No asumir 1:1, modelar M:N en destino                               |
| 5 | Multi-tenant `Guid_Tenant`                                                | Verificar valor único antes de cargar                               |
| 6 | `IdCentro = -1` = "sin centro"                                            | Reasignar a centro destino o excluir                                |
| 7 | Importes mezclados `float`/`numeric`                                      | Estandarizar a `decimal(18,4)` en pipeline                          |
| 8 | Anulaciones encadenadas (`PagoCli.IdAnulado`, `DocAdmin.IdDocAdminOrigen`) | Procesar en orden topológico (original → anulación → abono)         |
| 9 | Columnas `text` (deprecated SQL Server)                                   | Convertir a `nvarchar(max)` al exportar                             |
|10 | Collation `SQL_Latin1_General_CP1_CI_AS`                                  | Verificar acentos/ñ al leer (read as UTF-8 con conversión 1252)     |
|11 | Campos `Edu10..Edu24` en `TtosMed`                                        | Vacíos en este DB (sum=0). Probablemente legacy. **Ignorar.**       |
|12 | `ZonasBoca`, `Cuadrantes`, `Arcadas` en `TtosMed`                         | Siempre 0 en este DB. **Ignorar al migrar.**                        |
|13 | **Adjuntos viven fuera de la BBDD**: `TDocumentosPac.Original` lleva **solo nombre de fichero** (`APELLIDOS, NOMBRE.pdf`), no la carpeta. La carpeta raíz no está en la BBDD en claro: `CfgDatos` contiene valores `#ENC#...` cifrados con clave propietaria de Gesdén; `Centros.RutaFichMutuas` está NULL; `TConsinCab.LicenciaPath` solo tiene rutas locales por PC (`F:\GELITE\...`, `Z:\GELITE\...`). | **Tres opciones combinables**: (1) **preguntar al cliente** la ruta UNC `\\servidor\carpeta`; (2) si el asistente corre en máquina con Gesdén instalado, leer **registro Windows** (`HKCU\Software\Infomed\Gesden\...`) y `config.ini` de la instalación; (3) heurística: la estructura habitual es `<raíz>\GELITE\<subcarpeta>\...`. Recomendado: (2) auto-detect + fallback a (1) prompt al usuario. |
|14 | **Hash legal de facturas/presupuestos**: `DocAdmin.Hash`/`HashControl`, `Presu.Hash`, `CodigoATCUD`, `CodigoQR` (Verifactu / TicketBAI / ATCUD). | Migrar como **registros inmutables históricos**. Nunca re-emitir/re-firmar — rompe cadena fiscal y duplica numeración oficial. Si Dentalpin no soporta el formato exacto, almacenar el blob de hash como referencia. |
|15 | `Saldos` es una **caché precalculada** de `DeudaCli - PagoCli`. | **No migrar.** Recalcular en Dentalpin tras cargar `DeudaCli` y `PagoCli`. Migrarla produce descuadres dobles. |
|16 | **Calendarios laborables**: `TCalDias`, `TCalHor`, `TCalCa` → horarios por centro/box/doctor. Sin ellos, la agenda Dentalpin no sabe qué huecos son válidos. | **Crítico para agenda funcional.** Migrar antes que `DCitas`. |
|17 | **Citas recurrentes**: `DCitasPeriod` (cabecera de la serie) ↔ `DCitas.IdCitasP`. | Migrar primero `DCitasPeriod`. Sin la madre, las hijas pierden el contexto de recurrencia. |
|18 | **Multi-centro por colaborador**: `Centros_TColabos` (62). Un doctor puede trabajar en varios centros. | Si Dentalpin asume 1 centro/doctor, decidir centro principal o duplicar al colaborador por centro. |
|19 | **Self-FKs encadenadas**: `Pacientes.IdPacReferidor`, `Clientes.IdCIA`, `PagoCli.IdAnulado`, `PagoCli.IdPagoCliRelacionado`, `DocAdmin.IdDocAdminOrigen`, `Presu.AlternativaDe`, `Presu.Id_PresuOriginal`, `Recalls.IdRecallOrigen`. | Cargar en **dos pasadas**: 1ª INSERT con la self-FK a NULL, 2ª UPDATE con el back-reference resuelto vía mapping `id_origen→id_destino`. |
|20 | **Doble vínculo `TtosMed ↔ PresuTto`**: `TtosMed.IdPresuTto` y `PresuTto.IdTtoMedOrig` se referencian mutuamente. | Insertar `Presu` + `PresuTto` con `IdTtoMedOrig=NULL` → insertar `TtosMed` con `IdPresuTto` resuelto → UPDATE `PresuTto.IdTtoMedOrig`. |
|21 | **`TConsinDet` (784k pares clave-valor)** depende de plantillas de consentimiento que **no están en BBDD** (probablemente PDF/RTF en disco). Solo `TConsinCab.Texto`/`Html` tienen el render firmado. | Migrar **únicamente el render** de `TConsinCab` (texto/html), no la descomposición clave-valor. Esa descomposición no es reutilizable sin la plantilla original. |
|22 | **`Pacientes_Tarifas_log`** — historial de tarifa por paciente. | Si Dentalpin solo guarda tarifa actual, perderás auditoría de cómo se llegó al precio en presupuestos antiguos. Decidir explícito: migrar como tabla histórica o descartar. |
|23 | **Passwords `TUsers.Pass` / `TUsers.Password`** — dos columnas, hashes propios Gesdén (dos generaciones). | **No migrar passwords.** Crear usuarios en Dentalpin y forzar reset por email. |
|24 | **Conectores externos en DCitas**: `IdCitaConector`, `IdPacExt`, `OrigenExt`, `IdPartner`. Citas que vienen del portal web Gesdén / partners externos. | Conservar el campo `OrigenExt` como etiqueta de procedencia. Descartar los IDs externos: huérfanos en Dentalpin. |
|25 | **Remesas SEPA y pasarelas TPV**: `PagoCli.IdRemesaBancaria`, `IdPasarelaPago`, `NumTransaccion`. | Migrar **únicamente como histórico inmutable**. Nunca relanzar la transacción — duplica cargo al cliente real. |
|26 | **Fechas centinela** `1900-01-02` / `1900-01-25` aparecen como mínimo en `Presu.FecPresup` y `TtosMed.FecIni`. | Filtrar (`< '1950-01-01'`) y mapear a NULL al exportar. |
|27 | **Encoding**: `SQL_Latin1_General_CP1_CI_AS` (CP1252) vs UTF-8 del pipeline. | Antes del bulk, probar lectura de un `Apellidos` con ñ/acentos conocido. Forzar `Encoding.GetEncoding(1252)` o `N''` literals al exportar. |
|28 | **`LiqComisionDet`** — comisiones de colaboradores ligadas a `TtosMedFases`, `DeudaCli`, `PagoCli`. | Decisión explícita: si Dentalpin tiene módulo de comisiones, mapear; si no, skip documentado. |
|29 | **`PlanEcoL` (137)** — planes de financiación con cuotas vinculadas a `TtosMed`/`PagoCli`. | Si Dentalpin no tiene el concepto "plan financiero", aplanar a deudas individuales pero documentar la agrupación contractual perdida. |
|30 | **Pacientes menores con `IdCliTutor`** — el tutor también puede ser cliente/paciente. | Deduplicar tutores antes de cargar `Pacientes` para evitar insertar el mismo individuo como cliente y como paciente sin enlace. |
