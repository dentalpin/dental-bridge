# Diagrama ER simplificado — núcleo Gesdén

Diagrama Mermaid limitado al core para la migración a Dentalpin. Excluye catálogos hoja, auditoría y tablas vacías. Para FKs completas, ver `sql/exploration/02_foreign_keys.sql`.

> Render en GitHub, VSCode con extensión Mermaid, o Metabase Markdown card.

## Vista paciente / clínico / financiero

```mermaid
erDiagram
    Centros {
        int IdCentro PK
        varchar CodCentro
        varchar Descripcio
    }
    TUsers {
        int IdUser PK
        varchar Login
        varchar Nombre
        varchar Apellidos
        int IdCol FK
    }
    TColabos {
        int IdCol PK
        varchar Codigo
        varchar Apellidos
        varchar Nombre
        varchar NIF
        int IdTipoColab
    }
    Pacientes {
        int IdPac PK
        int IdCli FK
        int IdCol FK
        int IdCentro FK
        varchar NumPac
        varchar Nombre
        varchar Apellidos
        varchar NIF
        datetime FecNacim
        datetime FecAlta
        smalldatetime Inactivo
        bit AceptaGDPR
    }
    Clientes {
        int IdCli PK
        int IdCentro FK
        int IdBanco FK
        varchar Nombre
        varchar Apellidos
        varchar NIF
        varchar Email
        varchar TARIFA
    }
    PacCli {
        int IdPac PK,FK
        int IdCli PK,FK
        varchar Poliza
        smalldatetime FecAlta
        smalldatetime FecCaduc
    }
    DCitas {
        bigint IdCita PK
        int IdPac FK
        int IdCli FK
        int IdCentro FK
        int IdCol FK
        int IdSitC FK
        int Fecha "int formato Gesdén"
        int Hora "int formato Gesdén"
        int Duracion
    }
    Tratamientos {
        int IdTratamiento PK
        varchar Codigo
        varchar DescripMed
        int IdTipoEspec
    }
    Tratamientos_Tarifas {
        int IdTratamientoTarifa PK
        int IdTratamiento FK
        int IdTarifa
        varchar CodTto
    }
    TtosMed {
        int Ident PK
        int IdPac FK
        int IdCli FK
        int IdCol FK
        int IdCentro FK
        int IdTto FK
        int IdTipoOdg
        smalldatetime FecIni
        tinyint StaTto
        float Importe
        numeric ZonasPieza
    }
    TtosMedFases {
        int IdTtosMedFase PK
        int IdTtosMed FK
        int IdTratamientoFase FK
        int NumFase
        datetime Fecha
        int Estado
    }
    Presu {
        int Ident PK
        int IdPac FK
        int IdCol FK
        int IdCentro FK
        int NumSerie
        int NumPre
        smalldatetime FecPresup
        smalldatetime FecAcepta
        smalldatetime FecRechaz
        int Estado
    }
    PresuTto {
        int Ident PK
        int Id_Presu FK
        int IdPac FK
        int IdTto FK
        int LinPre
        float ImportePre
        float BaseImponible
    }
    PagoCli {
        int IdPagoCli PK
        int IdCli FK
        int IdCentro FK
        int IdForPago FK
        float Pagado
        smalldatetime FecPago
        int IdAnulado FK
    }
    DeudaCli {
        int IdDeudaCli PK
        int IdPac FK
        int IdCli FK
        int IdentTM FK
        smalldatetime FecPlazo
        float Adeudo
        bit Liquidado
    }
    DeudaPago {
        int IdDeudaPago PK
        int IdDeudaCli FK
        int IdPagoCli FK
        float Pagado
        smalldatetime FecPago
    }
    DocAdmin {
        int Ident PK
        int IdCli FK
        varchar Doc
        varchar Serie
        varchar NumDoc
        smalldatetime FecDoc
        int IdDocAdminOrigen FK
    }
    LinAdmin {
        int IdLinAdmin PK
        int IdDocAdmin FK
        int IdDeudaCli FK
        int IdPagoCli FK
        float Importe
    }
    Recalls {
        int Id PK
        int IdPac FK
        int IdCol FK
        int Id_Presu FK
        int Id_TtosMed FK
        smalldatetime Fecha
        int IdMotivo
        bit Citado
    }
    AlertPac {
        int Id PK
        int IdPac FK
        int IdCentro FK
        varchar Texto
        bit Marcado
    }
    TDocumentosPac {
        int IdDocPac PK
        int IdPac FK
        datetime FechaDoc
        varchar Descripcion
        varchar Original
    }
    RecetasCab {
        int IdRecetaIdent PK
        int IdPac FK
        int IdUsu FK
        int IdCol FK
        datetime Fecha
    }
    RecetasDet {
        int IdRecetaDet PK
        int IdReceta FK
        int IdTrat FK
        varchar Pauta
    }
    TConsinCab {
        int IdConsin PK
        int IdPac FK
        int IdCol FK
        datetime FechaFirma
        int Firmado
    }
    TConsinDet {
        int IdConsin PK,FK
        int IdDet PK
        varchar Objeto
        varchar Valor
    }
    TTratamientos {
        int IdPac PK,FK
        int IdTrat PK
        varchar DescFarmaco
        varchar Pauta
        datetime Fecha
    }

    Centros        ||--o{ Pacientes : "tiene"
    Centros        ||--o{ Clientes : "tiene"
    Centros        ||--o{ DCitas : "agenda"
    Centros        ||--o{ TtosMed : "ubicación"
    Centros        ||--o{ Presu : "emite"
    Centros        ||--o{ PagoCli : "recauda"
    Centros        ||--o{ AlertPac : "scope"
    TUsers         }o--|| TColabos : "puede ser"
    Clientes       ||--o{ Pacientes : "paga"
    Pacientes      }o--o{ Clientes : "PacCli"
    Pacientes      ||--o{ PacCli : ""
    Clientes       ||--o{ PacCli : ""
    Pacientes      ||--o{ DCitas : "asiste"
    Clientes       ||--o{ DCitas : "responsable"
    TColabos       ||--o{ DCitas : "doctor"
    TColabos       ||--o{ Pacientes : "doctor default"
    TColabos       ||--o{ TtosMed : "ejecuta"
    Pacientes      ||--o{ TtosMed : "recibe"
    Clientes       ||--o{ TtosMed : "paga"
    Tratamientos   ||--o{ Tratamientos_Tarifas : "tarifica"
    Tratamientos_Tarifas ||--o{ TtosMed : "instancia"
    TtosMed        ||--o{ TtosMedFases : "fases"
    Pacientes      ||--o{ Presu : "destinatario"
    TColabos       ||--o{ Presu : "elabora"
    Presu          ||--o{ PresuTto : "líneas"
    Tratamientos_Tarifas ||--o{ PresuTto : "ítem"
    PresuTto       }o--o| TtosMed : "ejecuta"
    Clientes       ||--o{ PagoCli : "paga"
    TtosMed        ||--o{ PagoCli : "concepto"
    PagoCli        ||--o{ DeudaPago : "aplica"
    DeudaCli       ||--o{ DeudaPago : "salda"
    Pacientes      ||--o{ DeudaCli : "debe"
    Clientes       ||--o{ DeudaCli : "deudor"
    TtosMedFases   ||--o{ DeudaCli : "genera"
    Clientes       ||--o{ DocAdmin : "facturado"
    DocAdmin       ||--o{ LinAdmin : "líneas"
    DeudaCli       ||--o{ LinAdmin : "factura"
    PagoCli        ||--o{ LinAdmin : "imputa"
    Pacientes      ||--o{ Recalls : "tiene"
    Pacientes      ||--o{ AlertPac : "tiene"
    Pacientes      ||--o{ TDocumentosPac : "archivo"
    Pacientes      ||--o{ RecetasCab : "receta"
    RecetasCab     ||--o{ RecetasDet : "línea"
    Pacientes      ||--o{ TConsinCab : "firma"
    TConsinCab     ||--o{ TConsinDet : "campos"
    Pacientes      ||--o{ TTratamientos : "medicación"
```

## Lectura rápida

- **Centro y Profesional** son los dos ejes verticales que tocan a casi todo.
- **Paciente ↔ Cliente** es M:N vía `PacCli`. Crítico para facturación.
- **TtosMed** (tratamiento aplicado) es el "evento clínico" central. Hereda de un presupuesto (`PresuTto.IdTtoMedOrig` ↔ `TtosMed.IdPresuTto`) y descompone en sesiones (`TtosMedFases`).
- **Cadena financiera**: `TtosMedFases` → `DeudaCli` → `DeudaPago` ← `PagoCli` → `LinAdmin` → `DocAdmin`. Una factura agrupa deudas y pagos aplicados.
- **Comunicaciones y clínica secundaria** (`AlertPac`, `Recalls`, `RecetasCab/Det`, `TConsinCab/Det`, `TDocumentosPac`, `TTratamientos`) cuelgan directamente del paciente.
