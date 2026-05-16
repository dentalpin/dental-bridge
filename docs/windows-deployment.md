# Windows deployment guide

Step-by-step instructions for running `dental-bridge` on a clinic's
Windows server (where Gesdén lives). Intended for IT integrators and
clinic system administrators.

## 1. Target environment

A `dental-bridge` binary supports:

- Windows Server 2012 R2 or later, or Windows 10 / 11.
- 64-bit only (x64).
- SQL Server 2008 R2 → 2022, instance running locally or reachable over
  TCP/IP on port 1433 (default) or a custom port.
- Microsoft **ODBC Driver 18 for SQL Server**.

## 2. Install Microsoft ODBC Driver 18

Required. The tool refuses to start without it and points at the
download page in its error message.

1. Open
   <https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server>.
2. Download the latest **x64** MSI for "ODBC Driver 18 for SQL Server".
3. Run the installer (admin rights required). Accept defaults.
4. Confirm registration:
   ```powershell
   Get-OdbcDriver -Name 'ODBC Driver 18 for SQL Server'
   ```

## 3. Download the dental-bridge binary

Each release ships an unsigned `dental-bridge-<version>-windows-x64.exe`
plus a companion `.sha256` text file. Get both from the
[Releases page](https://github.com/dentalpin/dental-bridge/releases).

### Verify the SHA-256 before running

The first thing to do with any unsigned executable is verify it. From
PowerShell, in the folder where you downloaded the file:

```powershell
Get-FileHash .\dental-bridge-0.1.0-windows-x64.exe -Algorithm SHA256
Get-Content .\dental-bridge-0.1.0-windows-x64.exe.sha256
```

The hex output of the first command MUST match the hash inside the
`.sha256` file character-for-character. If it does not match, do not
run the binary — re-download or report the discrepancy on the issue
tracker.

## 4. First run — SmartScreen warning

Because the v0.x binaries are **not code-signed**, Windows SmartScreen
shows a warning the first time the executable runs:

> Windows protected your PC
> Microsoft Defender SmartScreen prevented an unrecognised app from starting.

Steps to proceed:

1. Click **More info** (this expands the dialog).
2. Verify the file name and publisher fields show what you expect.
3. Click **Run anyway**.

SmartScreen remembers the decision per filename. Re-downloading the
file under a different name resets the prompt.

If you prefer to bypass via PowerShell:

```powershell
Unblock-File .\dental-bridge-0.1.0-windows-x64.exe
```

This removes the "Mark of the Web" zone identifier that triggers the
prompt; subsequent runs will not warn.

## 5. Antivirus false positives

Some AV engines flag PyInstaller-bundled binaries because the bundling
pattern resembles malware packers. If your AV quarantines the file:

1. Confirm the SHA-256 matches the published value (step 3 above).
2. Restore the file from quarantine.
3. Add an exclusion for the folder where the executable lives.

We submit each release to the major AV vendors for review, but unsigned
builds will likely keep generating false positives until the project
moves to a code-signed pipeline.

## 6. Connecting to Gesdén

A typical local Gesdén install runs SQL Server Express on the
`SQLEXPRESS` named instance. The DSN format is:

```
gesden://<host>[\<instance>][:<port>]/<database>
```

Examples:

```powershell
# Local SQLEXPRESS, SQL Authentication
$env:DENTAL_BRIDGE_PWD = "<sa-password>"
.\dental-bridge.exe analyze `
    --source "gesden://localhost\SQLEXPRESS/SOURCE_DB" `
    --user sa `
    --trust-server-certificate

# Windows authentication, custom port
.\dental-bridge.exe analyze `
    --source "gesden://server:1450/SOURCE_DB" `
    --trusted-connection `
    --trust-server-certificate
```

### TLS and legacy SQL Server

ODBC Driver 18 enforces TLS by default. Older SQL Server installs
(2008 R2 - 2014) often present a self-signed certificate, which the
driver will refuse to accept unless you pass `--trust-server-certificate`.
On a private LAN that is the right choice — the clinic's SQL Server is
not exposed publicly.

## 7. Finding the Gesdén image folder

`dental-bridge` records every patient document and signed consent in
the DPMF file, but the binaries (radiographs, PDFs, signed consents)
live on the clinic's filesystem. The default location is
`<Gesdén install>\GELITE\<subfolder>`. The tool attempts to
auto-detect the install path via:

1. Registry keys `HKLM\SOFTWARE\Infomed\Gesden` and
   `HKCU\Software\Infomed\Gesden`.
2. Heuristic probing of conventional install paths.
3. An interactive prompt when the operator runs `extract` with
   `--collect-files`.

A separate sync agent (planned for v0.2) will handle the actual
upload of the binaries; v0.1 emits the `_files` manifest and stops.

## 8. State directory

`dental-bridge` keeps the resumable-checkpoint database under
`%APPDATA%\dental-bridge\state.db`. You can reset it safely between
runs:

```powershell
Remove-Item "$env:APPDATA\dental-bridge\state.db"
```

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `OdbcDriverMissingError` | Step 2 not done | Install ODBC Driver 18 |
| Connection times out | Firewall / SQL Server not listening on TCP | Enable TCP/IP in SQL Server Configuration Manager; open the port |
| `SSL Provider: The certificate chain was issued by an authority that is not trusted` | Self-signed cert on old SQL Server | Add `--trust-server-certificate` |
| `Login failed for user 'sa'` | SQL Authentication disabled, or wrong password | Use `--trusted-connection` (Windows Auth) or verify the SA password |
| AV quarantines the binary | False positive on unsigned PyInstaller binary | Verify SHA-256, restore from quarantine, add folder exclusion |
| `analyze` succeeds but `extract` fails partway | Likely transient SQL hiccup or memory pressure | Re-run with the default checkpoint enabled — only new rows will be re-emitted |

## 10. Where to file issues

<https://github.com/dentalpin/dental-bridge/issues>. Please include:

- Output of `dental-bridge --version`.
- Output of the failing command (redact passwords/PII).
- The detected schema fingerprint (printed by `analyze`).
