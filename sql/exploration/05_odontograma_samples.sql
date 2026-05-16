-- 05_odontograma_samples.sql
-- Muestras y agregados para reverse-engineering del codificado de piezas.
-- Ver docs/odontograma_decoding.md.
-- USE SOURCE_DB

SET NOCOUNT ON;

PRINT '=== Frecuencia ZonasPieza (top 50) ===';
SELECT TOP 50 ZonasPieza, COUNT(*) AS n
FROM TtosMed
WHERE ZonasPieza > 0
GROUP BY ZonasPieza
ORDER BY n DESC;

PRINT '=== Distribución por tipo de operación (IdTipoOdg) con ZonasPieza no vacío ===';
SELECT
    tm.IdTipoOdg,
    to_.Descripcio       AS tipo_odontograma,
    COUNT(*)             AS lineas_con_pieza,
    COUNT(DISTINCT tm.ZonasPieza) AS valores_distintos
FROM TtosMed tm
LEFT JOIN TTipoOdg to_ ON to_.IdTipoOdg = tm.IdTipoOdg
WHERE tm.ZonasPieza > 0
GROUP BY tm.IdTipoOdg, to_.Descripcio
ORDER BY lineas_con_pieza DESC;

PRINT '=== Muestras para validación visual contra UI Gesdén ===';
-- 10 ejemplos representativos de cada tipo de operación dental común
;WITH muestras AS (
    SELECT
        tm.IdPac,
        p.NumPac,
        p.Apellidos + ', ' + p.Nombre AS paciente,
        tm.Ident,
        tm.IdTipoOdg,
        to_.Descripcio AS tipo_odg,
        t.Codigo       AS cod_tto,
        t.DescripMed   AS tto,
        tm.ZonasPieza,
        tm.PiezasAdu,
        tm.PiezasLec,
        tm.PiezasNum,
        tm.FecIni,
        tm.Importe,
        ROW_NUMBER() OVER (PARTITION BY tm.IdTipoOdg ORDER BY tm.FecIni DESC) AS rn
    FROM TtosMed tm
    JOIN Pacientes p ON p.IdPac = tm.IdPac
    LEFT JOIN TTipoOdg to_ ON to_.IdTipoOdg = tm.IdTipoOdg
    LEFT JOIN Tratamientos_Tarifas tt ON tt.IdTratamientoTarifa = tm.IdTto
    LEFT JOIN Tratamientos t ON t.IdTratamiento = tt.IdTratamiento
    WHERE tm.ZonasPieza > 0
      AND tm.IdTipoOdg IN (22, 26, 24, 37, 21, 33, 27, 32, 38)  -- obturación, corona, implante, extracción, endodoncia, carilla, puente, sellado, higiene
)
SELECT IdPac, NumPac, paciente, Ident, IdTipoOdg, tipo_odg, cod_tto, tto, ZonasPieza, PiezasAdu, PiezasLec, FecIni, Importe
FROM muestras
WHERE rn <= 2
ORDER BY IdTipoOdg, FecIni DESC;

PRINT '=== Detección de valores poco frecuentes (posibles outliers) ===';
SELECT ZonasPieza, COUNT(*) AS n
FROM TtosMed
WHERE ZonasPieza > 0
GROUP BY ZonasPieza
HAVING COUNT(*) <= 2
ORDER BY ZonasPieza;
