-- 04_schema_dump.sql
-- Volcado del schema (columnas, tipos, nullability) para las tablas core.
-- Útil para generar mappers de tipos en el asistente de migración.
-- USE SOURCE_DB

SET NOCOUNT ON;

PRINT '=== Schema de tablas core ===';
SELECT
    t.name AS tabla,
    c.column_id,
    c.name AS columna,
    ty.name AS tipo,
    CASE
        WHEN ty.name IN ('varchar','nvarchar','char','nchar')
            THEN '(' + CAST(CASE WHEN c.max_length = -1 THEN -1
                                 WHEN ty.name IN ('nvarchar','nchar') THEN c.max_length / 2
                                 ELSE c.max_length END AS varchar) + ')'
        WHEN ty.name IN ('decimal','numeric')
            THEN '(' + CAST(c.precision AS varchar) + ',' + CAST(c.scale AS varchar) + ')'
        ELSE ''
    END AS dim,
    c.is_nullable AS nullable,
    c.is_identity AS is_identity,
    OBJECT_DEFINITION(c.default_object_id) AS default_value
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
JOIN sys.types  ty ON ty.user_type_id = c.user_type_id
WHERE t.name IN (
    'Pacientes', 'Clientes', 'PacCli',
    'DCitas', 'DCitasOp',
    'TtosMed', 'TtosMedFases', 'TratamientosFases',
    'Tratamientos', 'Tratamientos_Tarifas', 'Tratamientos_Tarifas_Precios',
    'Presu', 'PresuTto', 'PresuTipoTto',
    'PagoCli', 'DeudaCli', 'DeudaPago',
    'DocAdmin', 'LinAdmin', 'RegApun',
    'Recalls', 'AlertPac', 'TDocumentosPac',
    'RecetasCab', 'RecetasDet', 'TTratamientos',
    'TConsinCab', 'TConsinDet',
    'Centros', 'TColabos', 'TUsers', 'TUCentros',
    'TForPago', 'TPoblaci', 'TProvin', 'TPaises',
    'TEspecOMC', 'TProfesi', 'TTipoOdg', 'TSitCita',
    'Bancos', 'BancoMov', 'TRefer', 'TProced'
)
ORDER BY t.name, c.column_id;

PRINT '=== Identidad (columnas IDENTITY) ===';
SELECT t.name AS tabla, c.name AS columna
FROM sys.tables t
JOIN sys.columns c ON c.object_id = t.object_id
WHERE c.is_identity = 1
ORDER BY t.name;

PRINT '=== Claves primarias ===';
SELECT
    t.name           AS tabla,
    i.name           AS pk_name,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columnas
FROM sys.tables t
JOIN sys.indexes i ON i.object_id = t.object_id AND i.is_primary_key = 1
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
GROUP BY t.name, i.name
ORDER BY t.name;
