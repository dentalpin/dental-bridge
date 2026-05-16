-- 01_inventory.sql
-- Inventario de tablas con conteo de filas. Usar para refrescar el mapeo
-- en docs/schema_map.md tras cualquier actualización de la BBDD.
-- USE SOURCE_DB

SET NOCOUNT ON;

PRINT '=== Top 50 tablas por número de filas ===';
SELECT TOP 50
    t.name AS tabla,
    p.rows AS filas
FROM sys.tables t
JOIN sys.partitions p
    ON t.object_id = p.object_id
   AND p.index_id IN (0, 1)
WHERE p.rows > 0
ORDER BY p.rows DESC;

PRINT '=== Conteo total de tablas (con datos / vacías) ===';
SELECT
    SUM(CASE WHEN p.rows > 0 THEN 1 ELSE 0 END) AS tablas_con_datos,
    SUM(CASE WHEN p.rows = 0 THEN 1 ELSE 0 END) AS tablas_vacias,
    COUNT(*) AS total
FROM sys.tables t
JOIN sys.partitions p
    ON t.object_id = p.object_id
   AND p.index_id IN (0, 1);

PRINT '=== Filas por prefijo (categorización) ===';
SELECT
    CASE
        WHEN t.name LIKE 'T%' AND t.name NOT LIKE 'Tto%' AND t.name NOT LIKE 'Trat%' THEN 'T* (catalogos)'
        WHEN t.name LIKE 'D%' THEN 'D* (detalle)'
        WHEN t.name LIKE 'Z%' THEN 'Z* (sistema)'
        WHEN t.name LIKE 'S1[_]%' THEN 'S1_* (auth)'
        WHEN t.name LIKE 'IS4[_]%' THEN 'IS4_* (identity)'
        WHEN t.name LIKE 'CDM%' THEN 'CDM* (dashboards)'
        WHEN t.name LIKE 'ATMT[_]%' THEN 'ATMT_* (autom.)'
        WHEN t.name LIKE 'PLG[_]%' THEN 'PLG_* (plugins)'
        WHEN t.name LIKE 'Pac%' THEN 'Pac* (paciente)'
        WHEN t.name LIKE 'Cli%' THEN 'Cli* (cliente)'
        WHEN t.name LIKE 'Tto%' OR t.name LIKE 'Trat%' THEN 'Tto/Trat* (clínico)'
        WHEN t.name LIKE 'Presu%' THEN 'Presu* (presupuestos)'
        WHEN t.name LIKE 'Pago%' OR t.name LIKE 'Deuda%' THEN 'Pago/Deuda* (financiero)'
        WHEN t.name LIKE 'Sch[_]%' THEN 'Sch_* (scheduler nuevo)'
        WHEN t.name LIKE '[_]%' THEN '_* (helpers migración)'
        ELSE 'otros'
    END AS categoria,
    COUNT(*) AS num_tablas,
    SUM(p.rows) AS filas_totales
FROM sys.tables t
JOIN sys.partitions p
    ON t.object_id = p.object_id
   AND p.index_id IN (0, 1)
GROUP BY
    CASE
        WHEN t.name LIKE 'T%' AND t.name NOT LIKE 'Tto%' AND t.name NOT LIKE 'Trat%' THEN 'T* (catalogos)'
        WHEN t.name LIKE 'D%' THEN 'D* (detalle)'
        WHEN t.name LIKE 'Z%' THEN 'Z* (sistema)'
        WHEN t.name LIKE 'S1[_]%' THEN 'S1_* (auth)'
        WHEN t.name LIKE 'IS4[_]%' THEN 'IS4_* (identity)'
        WHEN t.name LIKE 'CDM%' THEN 'CDM* (dashboards)'
        WHEN t.name LIKE 'ATMT[_]%' THEN 'ATMT_* (autom.)'
        WHEN t.name LIKE 'PLG[_]%' THEN 'PLG_* (plugins)'
        WHEN t.name LIKE 'Pac%' THEN 'Pac* (paciente)'
        WHEN t.name LIKE 'Cli%' THEN 'Cli* (cliente)'
        WHEN t.name LIKE 'Tto%' OR t.name LIKE 'Trat%' THEN 'Tto/Trat* (clínico)'
        WHEN t.name LIKE 'Presu%' THEN 'Presu* (presupuestos)'
        WHEN t.name LIKE 'Pago%' OR t.name LIKE 'Deuda%' THEN 'Pago/Deuda* (financiero)'
        WHEN t.name LIKE 'Sch[_]%' THEN 'Sch_* (scheduler nuevo)'
        WHEN t.name LIKE '[_]%' THEN '_* (helpers migración)'
        ELSE 'otros'
    END
ORDER BY filas_totales DESC;
