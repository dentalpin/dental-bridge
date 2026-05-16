-- 06_sample_extracts.sql
-- Extracción de 10 pacientes representativos con todas sus dependencias.
-- Sirve como dataset de prueba del asistente de migración Windows.
-- USE SOURCE_DB

SET NOCOUNT ON;

DECLARE @sample TABLE (IdPac int PRIMARY KEY);

-- Selección heurística: 10 pacientes con perfiles distintos
-- (mucha actividad, poca, recientes, antiguos, con presupuesto, con deuda...)
INSERT INTO @sample (IdPac)
SELECT TOP 10 IdPac FROM (
    -- 2 con más tratamientos
    SELECT TOP 2 tm.IdPac, 1 AS bucket, COUNT(*) AS w
    FROM TtosMed tm GROUP BY tm.IdPac ORDER BY COUNT(*) DESC
) a
UNION SELECT IdPac FROM (
    -- 2 con presupuestos rechazados
    SELECT TOP 2 IdPac, 2 AS bucket, COUNT(*) AS w
    FROM Presu WHERE FecRechaz IS NOT NULL GROUP BY IdPac ORDER BY COUNT(*) DESC
) b
UNION SELECT IdPac FROM (
    -- 2 con deuda alta
    SELECT TOP 2 IdPac, 3 AS bucket, SUM(Pendiente) AS w
    FROM DeudaCli GROUP BY IdPac ORDER BY SUM(Pendiente) DESC
) c
UNION SELECT IdPac FROM (
    -- 2 nuevos (último año)
    SELECT TOP 2 IdPac, 4 AS bucket, FecAlta AS w
    FROM Pacientes WHERE FecAlta > DATEADD(year, -1, GETDATE()) ORDER BY FecAlta DESC
) d
UNION SELECT IdPac FROM (
    -- 2 antiguos (alta antes del 2000)
    SELECT TOP 2 IdPac, 5 AS bucket, FecAlta AS w
    FROM Pacientes WHERE FecAlta < '2000-01-01' AND FecAlta IS NOT NULL ORDER BY FecAlta ASC
) e;

PRINT '=== Pacientes seleccionados ===';
SELECT p.IdPac, p.NumPac, p.Apellidos + ', ' + ISNULL(p.Nombre,'') AS paciente,
       p.FecAlta, p.FecNacim, p.Sexo, p.IdCentro
FROM Pacientes p
WHERE p.IdPac IN (SELECT IdPac FROM @sample);

PRINT '=== Sus PacCli (relaciones con clientes/pagadores) ===';
SELECT pc.IdPac, pc.IdCli, c.RazonSocial, c.Apellidos + ', ' + ISNULL(c.Nombre,'') AS cliente,
       pc.Poliza, pc.FecAlta, pc.FecCaduc, pc.Inactivo
FROM PacCli pc
JOIN Clientes c ON c.IdCli = pc.IdCli
WHERE pc.IdPac IN (SELECT IdPac FROM @sample);

PRINT '=== Sus citas (últimas 20 por paciente) ===';
WITH q AS (
    SELECT dc.*, ROW_NUMBER() OVER (PARTITION BY dc.IdPac ORDER BY dc.IdCita DESC) AS rn
    FROM DCitas dc
    WHERE dc.IdPac IN (SELECT IdPac FROM @sample)
)
SELECT IdPac, IdCita, Fecha, Hora, Duracion, IdSitC, BOX, IdCol, IdCentro, Texto
FROM q WHERE rn <= 20
ORDER BY IdPac, IdCita DESC;

PRINT '=== Sus tratamientos aplicados ===';
SELECT tm.IdPac, tm.Ident, tm.IdTto, t.DescripMed, tm.FecIni, tm.FecFin,
       tm.StaTto, tm.Importe, tm.Pendiente, tm.IdCol, tm.IdCentro,
       tm.ZonasPieza, tm.PiezasAdu, tm.IdTipoOdg
FROM TtosMed tm
LEFT JOIN Tratamientos_Tarifas tt ON tt.IdTratamientoTarifa = tm.IdTto
LEFT JOIN Tratamientos t ON t.IdTratamiento = tt.IdTratamiento
WHERE tm.IdPac IN (SELECT IdPac FROM @sample)
ORDER BY tm.IdPac, tm.FecIni DESC;

PRINT '=== Sus fases ===';
SELECT tmf.IdTtosMedFase, tmf.IdTtosMed, tmf.NumFase, tmf.Fecha, tmf.Estado, tmf.IdCol
FROM TtosMedFases tmf
JOIN TtosMed tm ON tm.Ident = tmf.IdTtosMed
WHERE tm.IdPac IN (SELECT IdPac FROM @sample)
ORDER BY tmf.IdTtosMed, tmf.NumFase;

PRINT '=== Sus presupuestos ===';
SELECT IdPac, Ident, NumSerie, NumPre, FecPresup, FecAcepta, FecRechaz, Estado, IdCol, IdCentro
FROM Presu
WHERE IdPac IN (SELECT IdPac FROM @sample)
ORDER BY IdPac, Ident;

PRINT '=== Líneas de sus presupuestos ===';
SELECT pt.Id_Presu, pt.LinPre, pt.IdPac, pt.IdTto, t.DescripMed,
       pt.Unidades, pt.ImportePre, pt.BaseImponible, pt.ImporteIVA, pt.Dto
FROM PresuTto pt
LEFT JOIN Tratamientos_Tarifas tt ON tt.IdTratamientoTarifa = pt.IdTto
LEFT JOIN Tratamientos t ON t.IdTratamiento = tt.IdTratamiento
WHERE pt.IdPac IN (SELECT IdPac FROM @sample)
ORDER BY pt.IdPac, pt.Id_Presu, pt.LinPre;

PRINT '=== Sus pagos ===';
SELECT pc.IdPagoCli, pc.IdCli, pc.Pagado, pc.FecPago, pc.IdForPago, pc.IdAnulado
FROM PagoCli pc
JOIN PacCli pcc ON pcc.IdCli = pc.IdCli
WHERE pcc.IdPac IN (SELECT IdPac FROM @sample);

PRINT '=== Sus deudas ===';
SELECT IdDeudaCli, IdPac, IdCli, FecPlazo, Adeudo, Pendiente, Liquidado
FROM DeudaCli
WHERE IdPac IN (SELECT IdPac FROM @sample)
ORDER BY IdPac, FecPlazo;

PRINT '=== Sus recetas ===';
SELECT IdRecetaIdent, IdPac, Fecha, Diagnostico, TipoReceta, Dispensada, Anulada
FROM RecetasCab
WHERE IdPac IN (SELECT IdPac FROM @sample)
ORDER BY IdPac, Fecha DESC;

PRINT '=== Sus consentimientos firmados ===';
SELECT IdConsin, IdPac, Titulo, FechaFirma, Firmado, IdColFirma
FROM TConsinCab
WHERE IdPac IN (SELECT IdPac FROM @sample) AND Firmado = 1
ORDER BY IdPac, FechaFirma DESC;

PRINT '=== Sus documentos adjuntos ===';
SELECT IdDocPac, IdPac, FechaDoc, Descripcion, Original, TipoDoc, Firmado
FROM TDocumentosPac
WHERE IdPac IN (SELECT IdPac FROM @sample)
ORDER BY IdPac, FechaDoc DESC;

PRINT '=== Sus alertas ===';
SELECT Id, IdPac, Texto, Marcado FROM AlertPac WHERE IdPac IN (SELECT IdPac FROM @sample);

PRINT '=== Sus recalls ===';
SELECT Id, IdPac, Fecha, IdMotivo, Asistido, Citado FROM Recalls WHERE IdPac IN (SELECT IdPac FROM @sample) ORDER BY IdPac, Fecha DESC;

PRINT '=== Su medicación crónica (TTratamientos) ===';
SELECT IdPac, IdTrat, DescFarmaco, Fecha, FecFin, Dosis, ViaAdmin, Frecuencia
FROM TTratamientos
WHERE IdPac IN (SELECT IdPac FROM @sample)
ORDER BY IdPac, Fecha DESC;
