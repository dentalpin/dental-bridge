-- 03_core_counts.sql
-- Conteos por entidad clave, segmentados por centro y rangos de fecha.
-- USE SOURCE_DB

SET NOCOUNT ON;

PRINT '=== Conteo global por entidad core ===';
SELECT 'Pacientes'      AS entidad, COUNT(*) AS n FROM Pacientes
UNION ALL SELECT 'Clientes',         COUNT(*) FROM Clientes
UNION ALL SELECT 'PacCli',           COUNT(*) FROM PacCli
UNION ALL SELECT 'DCitas',           COUNT(*) FROM DCitas
UNION ALL SELECT 'TtosMed',          COUNT(*) FROM TtosMed
UNION ALL SELECT 'TtosMedFases',     COUNT(*) FROM TtosMedFases
UNION ALL SELECT 'Presu',            COUNT(*) FROM Presu
UNION ALL SELECT 'PresuTto',         COUNT(*) FROM PresuTto
UNION ALL SELECT 'PagoCli',          COUNT(*) FROM PagoCli
UNION ALL SELECT 'DeudaCli',         COUNT(*) FROM DeudaCli
UNION ALL SELECT 'DeudaPago',        COUNT(*) FROM DeudaPago
UNION ALL SELECT 'DocAdmin',         COUNT(*) FROM DocAdmin
UNION ALL SELECT 'LinAdmin',         COUNT(*) FROM LinAdmin
UNION ALL SELECT 'RegApun',          COUNT(*) FROM RegApun
UNION ALL SELECT 'BancoMov',         COUNT(*) FROM BancoMov
UNION ALL SELECT 'RecetasCab',       COUNT(*) FROM RecetasCab
UNION ALL SELECT 'RecetasDet',       COUNT(*) FROM RecetasDet
UNION ALL SELECT 'TTratamientos',    COUNT(*) FROM TTratamientos
UNION ALL SELECT 'TConsinCab',       COUNT(*) FROM TConsinCab
UNION ALL SELECT 'TConsinDet',       COUNT(*) FROM TConsinDet
UNION ALL SELECT 'TDocumentosPac',   COUNT(*) FROM TDocumentosPac
UNION ALL SELECT 'Recalls',          COUNT(*) FROM Recalls
UNION ALL SELECT 'AlertPac',         COUNT(*) FROM AlertPac
UNION ALL SELECT 'Centros',          COUNT(*) FROM Centros
UNION ALL SELECT 'TColabos',         COUNT(*) FROM TColabos
UNION ALL SELECT 'TUsers',           COUNT(*) FROM TUsers
UNION ALL SELECT 'Tratamientos',     COUNT(*) FROM Tratamientos
ORDER BY n DESC;

PRINT '=== Pacientes por centro ===';
SELECT
    p.IdCentro,
    c.Descripcio AS centro,
    COUNT(*)     AS pacientes
FROM Pacientes p
LEFT JOIN Centros c ON c.IdCentro = p.IdCentro
GROUP BY p.IdCentro, c.Descripcio
ORDER BY pacientes DESC;

PRINT '=== Tratamientos aplicados por centro ===';
SELECT
    tm.IdCentro,
    c.Descripcio AS centro,
    COUNT(*)     AS tratamientos,
    SUM(tm.Importe) AS importe_total
FROM TtosMed tm
LEFT JOIN Centros c ON c.IdCentro = tm.IdCentro
GROUP BY tm.IdCentro, c.Descripcio
ORDER BY tratamientos DESC;

PRINT '=== Rango de fechas por entidad ===';
SELECT 'Pacientes.FecAlta' AS campo, MIN(FecAlta) AS min_d, MAX(FecAlta) AS max_d FROM Pacientes
UNION ALL SELECT 'DCitas.FecAlta',   MIN(FecAlta), MAX(FecAlta) FROM DCitas
UNION ALL SELECT 'TtosMed.FecIni',   MIN(FecIni),  MAX(FecIni)  FROM TtosMed WHERE FecIni > '1950-01-01'
UNION ALL SELECT 'TtosMed.FecFin',   MIN(FecFin),  MAX(FecFin)  FROM TtosMed WHERE FecFin > '1950-01-01'
UNION ALL SELECT 'Presu.FecPresup',  MIN(FecPresup), MAX(FecPresup) FROM Presu WHERE FecPresup > '1950-01-01'
UNION ALL SELECT 'PagoCli.FecPago',  MIN(FecPago), MAX(FecPago) FROM PagoCli
UNION ALL SELECT 'DocAdmin.FecDoc',  MIN(FecDoc),  MAX(FecDoc)  FROM DocAdmin;

PRINT '=== Distinct Guid_Tenant (debe ser único para migración single-tenant) ===';
SELECT Guid_Tenant, COUNT(*) AS pacientes
FROM Pacientes
GROUP BY Guid_Tenant
ORDER BY pacientes DESC;

PRINT '=== Estados de tratamiento (TtosMed.StaTto) ===';
SELECT StaTto, COUNT(*) AS n
FROM TtosMed
GROUP BY StaTto
ORDER BY n DESC;

PRINT '=== Estados de cita (DCitas.IdSitC) ===';
SELECT
    dc.IdSitC,
    ts.Descripcio AS estado,
    COUNT(*) AS n
FROM DCitas dc
LEFT JOIN TSitCita ts ON ts.IdSitC = dc.IdSitC
GROUP BY dc.IdSitC, ts.Descripcio
ORDER BY n DESC;
