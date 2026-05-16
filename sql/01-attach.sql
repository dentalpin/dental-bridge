IF DB_ID('SOURCE_DB') IS NULL
BEGIN
    CREATE DATABASE SOURCE_DB ON
        (FILENAME = '/var/opt/mssql/gesden/SOURCE_DB.MDF'),
        (FILENAME = '/var/opt/mssql/gesden/SOURCE_DB.LDF')
    FOR ATTACH;
END
GO

ALTER DATABASE SOURCE_DB SET RECOVERY SIMPLE;
GO

ALTER DATABASE SOURCE_DB SET COMPATIBILITY_LEVEL = 130;
GO

SELECT name, state_desc, compatibility_level, collation_name
FROM sys.databases
WHERE name = 'SOURCE_DB';
GO
