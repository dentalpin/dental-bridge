-- 02_foreign_keys.sql
-- Lista todas las FKs del schema. Útil para generar diagramas ER y validar
-- el orden topológico de migración (docs/migration_order.md).
-- USE SOURCE_DB

SET NOCOUNT ON;

PRINT '=== Todas las FKs ===';
SELECT
    OBJECT_NAME(fk.parent_object_id)     AS tabla_hija,
    c1.name                              AS columna_hija,
    OBJECT_NAME(fk.referenced_object_id) AS tabla_padre,
    c2.name                              AS columna_padre,
    fk.name                              AS constraint_name,
    CASE WHEN fk.parent_object_id = fk.referenced_object_id THEN 'AUTO' ELSE '' END AS auto
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc
    ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c1
    ON c1.object_id = fkc.parent_object_id
   AND c1.column_id = fkc.parent_column_id
JOIN sys.columns c2
    ON c2.object_id = fkc.referenced_object_id
   AND c2.column_id = fkc.referenced_column_id
ORDER BY tabla_hija, columna_hija;

PRINT '=== FKs solo del core (pacientes, citas, tratamientos, presupuestos, pagos) ===';
SELECT
    OBJECT_NAME(fk.parent_object_id)     AS tabla_hija,
    c1.name                              AS columna_hija,
    OBJECT_NAME(fk.referenced_object_id) AS tabla_padre,
    c2.name                              AS columna_padre
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc
    ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c1
    ON c1.object_id = fkc.parent_object_id
   AND c1.column_id = fkc.parent_column_id
JOIN sys.columns c2
    ON c2.object_id = fkc.referenced_object_id
   AND c2.column_id = fkc.referenced_column_id
WHERE OBJECT_NAME(fk.parent_object_id) IN (
    'Pacientes', 'Clientes', 'PacCli',
    'DCitas', 'DCitasOp',
    'TtosMed', 'TtosMedFases',
    'Presu', 'PresuTto', 'PresuTipoTto',
    'PagoCli', 'DeudaCli', 'DeudaPago',
    'DocAdmin', 'LinAdmin', 'RegApun',
    'Recalls', 'AlertPac', 'TDocumentosPac',
    'RecetasCab', 'RecetasDet',
    'TConsinCab', 'TConsinDet',
    'TTratamientos'
)
ORDER BY tabla_hija, columna_hija;

PRINT '=== Tablas SIN FKs salientes (probables raíces de catálogo) ===';
SELECT t.name
FROM sys.tables t
LEFT JOIN sys.foreign_keys fk ON fk.parent_object_id = t.object_id
WHERE fk.object_id IS NULL
ORDER BY t.name;
