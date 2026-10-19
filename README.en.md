# 🗄️ pkg-asisdb

[🇪🇸 Español](README.md) | [🇺🇸 English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://www.python.org/) [![Platform: 32/64-bit](https://img.shields.io/badge/platform-32%20%7C%2064--bit-blue.svg)](#-installation) [![Architecture: Multi--Engine%20%26%20DBF](https://img.shields.io/badge/architecture-multi--engine%20%26%20DBF-orange.svg)](#️-security-architecture-and-connection-management) [![Security: Memory Encryption](https://img.shields.io/badge/security-memory%20encryption-brightgreen.svg)](#3-secure-management-and-dynamic-password-encryption-encryptedpassword)

This package provides a lightweight foundational solution for **multi-engine database management (SQLAlchemy) and FoxPro/dBase table access (DBF)**, primarily focused on standardizing secure credentials, connection testing, and essential data access utilities for Python projects (desktop applications such as PyQt/CustomTkinter, CLI tools, scripts, or microservices).

In its current version, **pkg-asisdb** constitutes a foundational component designed to be progressively enhanced and expanded to become an integral part of the **Asisnet** ecosystem. For now, it is focused on key diagnostic and connectivity verification tasks, inviting users to stay tuned to upcoming releases as advanced capabilities are incorporated.

--------------------------------------------------------------------------------

#### 📋 Table of Contents

1. [🎯 Why pkg-asisdb? (Purpose and Intent)](#-why-pkg-asisdb-purpose-and-intent)
2. [🚀 Key Capabilities and Features](#-key-capabilities-and-features)
3. [📦 Installation](#-installation)
4. [🏗️ Security Architecture and Connection Management](#️-security-architecture-and-connection-management)
5. [📁 Project Structure and Canonical Data Schema](#-project-structure-and-canonical-data-schema)
6. [🛠️ Quick Developer Guide](#️-quick-developer-guide)
   - [1. Build URL and Get SQLAlchemy Engine (`ConnectionConfig`)](#1-build-url-and-get-sqlalchemy-engine-connectionconfig)
   - [2. Executing Queries and Statements (`execute_query` and `execute_statement`)](#2-executing-queries-and-statements-execute_query-and-execute_statement)
   - [3. Secure Management and Dynamic Password Encryption (`EncryptedPassword`)](#3-secure-management-and-dynamic-password-encryption-encryptedpassword)
   - [4. Connection Testing and Diagnostics (`test_connection`)](#4-connection-testing-and-diagnostics-test_connection)
   - [5. Canonical Configuration via Dictionaries (`from_dict`)](#5-canonical-configuration-via-dictionaries-from_dict)
   - [6. Managing Multiple Simultaneous Engines](#6-managing-multiple-simultaneous-engines)
   - [7. Direct Reading and Caching of FoxPro / dBase Tables (`DBFReader` and `DBFCacheManager`)](#7-direct-reading-and-caching-of-foxpro--dbase-tables-dbfreader-and-dbfcachemanager)
   - [8. Canonical Parameter and Wildcard Interpolation](#8-canonical-parameter-and-wildcard-interpolation)
7. [🧪 Automated Tests](#-automated-tests)
8. [👥 Contact and Support](#-contact-and-support)
9. [📄 License](#-license)

--------------------------------------------------------------------------------

#### 🎯 Why pkg-asisdb? (Purpose and Intent)
In the development of enterprise applications, corporate services, and data synchronization systems, connection management and data access typically face **critical challenges and recurring vulnerabilities**:
*   **Plaintext credentials exposed**: Passwords traveling in plaintext variables readable in console logs, memory dumps, accidental serializations, or exception tracebacks.
*   **Heterogeneity of drivers and engines**: Disparate connection syntax across Microsoft SQL Server, PostgreSQL, MySQL, and SQLite, plus the need to detect which SQL Server ODBC driver is actually installed on the client machine.
*   **Fragile and scattered connection strings**: Manual construction of SQLAlchemy URLs with inconsistent parameters, uncontrolled aliases, or unescaped special characters.
*   **Coexistence with legacy FoxPro / dBase (DBF) tables**: Difficulty querying large legacy tables without relying on obsolete 32-bit OLE DB drivers or heavy, slow external libraries.
*   **Lack of secure diagnostics**: Inability to test connectivity and troubleshoot network incidents without leaking passwords into diagnostic logs.

**pkg-asisdb was created to tackle these needs at their root through an agile and modular approach**, providing a reliable foundation for connection testing, with a roadmap aligned with the complete ecosystem:
1.  **Dynamic In-Memory Password Encryption (`EncryptedPassword`)**: Automatic and universal password protection using ephemeral 256-bit session keys, ensuring passwords are never exposed in plaintext in memory, string representations, or dumps.
2.  **Unified Multi-Engine Layer**: Seamless assembly of connection URLs for MSSQL (ODBC / pymssql), PostgreSQL, MySQL, and SQLite under a strict canonical contract (`ConnectionConfig`).
3.  **Intelligent ODBC Driver Detection**: Dynamic detection and cache persistence of the best native SQL Server driver available on the operating system.
4.  **High-Performance Native DBF Reader**: Direct access and reverse streaming without external drivers, featuring $O(1)$ indexed in-memory caching (`DBFCacheManager`).
5.  **Deterministic Diagnostics with Zero Credential Leaks**: Testing and validation suite (`test_connection`) that automatically masks credentials in logs and URLs.

--------------------------------------------------------------------------------

#### 🚀 Key Capabilities and Features
*   **Unified SQL Engine Management**: Direct, standardized support for MSSQL (native ODBC / `pymssql`), SQLite, PostgreSQL, and MySQL through SQLAlchemy.
*   **Dynamic and Universal Password Encryption (`EncryptedPassword`)**:
    *   Immutable container that obfuscates any textual representation (`__repr__` as `<EncryptedPassword: PROTECTED>` and `__str__` as `********`).
    *   Decoupled 256-bit ephemeral encryption key (`_SESSION_KEYS`), preventing the object from being decrypted outside the active session context.
    *   Universal and transparent encryption when instantiating `ConnectionConfig` or invoking connection utilities.
    *   Strictly-in-time decryption at the very last moment when interacting with the driver connector, eradicating intermediate plaintext variables.
*   **Automatic Detection and Prioritization of MSSQL ODBC Drivers**: Dynamic detection on Windows/Linux of the most modern ODBC driver available (`ODBC Driver 18 for SQL Server`, `17`, `SQL Server Native Client`, etc.), with cache persistence to avoid re-scanning.
*   **Streaming Reader and Cache for FoxPro / dBase (DBF) Tables**:
    *   100% compatible with both **32-bit and 64-bit** architectures, permanently eliminating dependency on the legacy 32-bit OLE DB driver (`VFPOLEDB.dll`).
    *   `DBFReader`: Reading DBF tables of any size via reverse streaming and direct record scanning using fixed byte offsets.
    *   `DBFCacheManager`: Indexed in-memory caching for instant queries with $O(1)$ performance.
*   **Canonical Parameter and Wildcard Interpolation**: Secure support for placeholders in connection strings (`{database}`, `{host}`, `{user}`, `{puerto}`) and dynamic temporal wildcards (`{DATEYEAR}`, `{TIMESTAMP}`).
*   **Strict `ConnectionConfig` Contract**: Canonical configuration without ambiguities, free of assumed business defaults.
*   **Multi-Instance Engine Pool**: Cached management of multiple simultaneously active engines (`primary`, `auditoria`, `historico`), with dedicated functions for selective closing (`close_engine`) and full reset (`reset_engine`).
*   **Native Internationalization with `pkg-i18n`**: Diagnostic messages and warnings integrated with Asisnet's corporate translation catalog under the canonical `[asisdb]` prefix.

--------------------------------------------------------------------------------

#### 📦 Installation

##### 1. Direct Installation from GitHub (Recommended)
Installing the base core in your virtual environment via pip:
```powershell
pip install git+https://github.com/borispinto/pkg-asisdb.git
```

With specific connectors for your database engine (extras):
```powershell
# For Microsoft SQL Server (Asisnet Environment)
pip install "pkg-asisdb[mssql] @ git+https://github.com/borispinto/pkg-asisdb.git"

# For PostgreSQL
pip install "pkg-asisdb[postgres] @ git+https://github.com/borispinto/pkg-asisdb.git"

# For MySQL
pip install "pkg-asisdb[mysql] @ git+https://github.com/borispinto/pkg-asisdb.git"

# All engines and testing tools
pip install "pkg-asisdb[all] @ git+https://github.com/borispinto/pkg-asisdb.git"
```

Or declared in your `pyproject.toml` file:
```toml
[project]
dependencies = [
    "pkg-asisdb[mssql] @ git+https://github.com/borispinto/pkg-asisdb.git",
]
```

--------------------------------------------------------------------------------

##### 2. Installation from Local Source Code and Requirements per Engine
Cloning and standard installation in editable mode:
```powershell
git clone https://github.com/borispinto/pkg-asisdb.git
cd pkg-asisdb
pip install -e .
```

Modular installation according to the required database engine:
```powershell
# A. Base Core (SQLite and FoxPro DBF)
pip install -r requirements.txt

# B. Microsoft SQL Server (pyodbc + pymssql - Asisnet Standard)
pip install -r requirements-mssql.txt

# C. PostgreSQL (psycopg2-binary)
pip install -r requirements-postgres.txt

# D. MySQL and MariaDB (pymysql)
pip install -r requirements-mysql.txt

# E. Development and Testing Environment (pytest)
pip install -r requirements-dev.txt

# F. Full Installation (all engines and tools)
pip install -r requirements-all.txt
```

>[!NOTE] **Architecture and Dependency Compatibility**:
>*   **32-bit and 64-bit Architectures**: `pkg-asisdb` is entirely architecture-agnostic and operates identically in **32-bit and 64-bit** Python environments. DBF table reading is executed in pure Python via `dbfread>=2.0.7` and direct binary offset access, completely doing away with external OLE DB or ODBC drivers.
>*   **Production Core**: Requires `SQLAlchemy>=2.0.0`, `dbfread>=2.0.7`, and `pkg-i18n>=1.0.0`.
>*   **SQL Connectors**: Installed predictably and modularly via the corresponding `requirements-*.txt` file for the engine used by your project.

--------------------------------------------------------------------------------

#### 🏗️ Security Architecture and Connection Management

`pkg-asisdb` implements a defense-in-depth architecture to prevent inadvertent credential leakage or exposure and ensure robustness in high-concurrency environments:

| Component / Layer | Mechanism | Operational Benefit |
| :--- | :--- | :--- |
| **`EncryptedPassword`** | Immutable container encrypted with ephemeral 256-bit session key | Prevents reading the password in memory via dumps or debuggers |
| **Universal Obfuscation** | `__repr__` (`<EncryptedPassword: PROTECTED>`) and `__str__` (`********`) methods | Complete shield against `print()`, accidental JSON serializations, or log dumps |
| **In-Line Decryption** | Decryption at the exact moment of socket or connection establishment | Eradicates local plaintext variables from the execution stack |
| **Deterministic Masking** | Sanitization of passwords and fields explicitly defined in `encrypted_fields` | Completely safe diagnostics and generated URLs in logs |
| **Multi-Engine Pool** | Indexed engine caching by key (`key="primary"`, `key="replica"`) | Granular lifecycle control and database resource reclamation |

--------------------------------------------------------------------------------

#### 📁 Project Structure and Canonical Data Schema

##### Recommended structure in your consumer project
```text
my_project/
├── pyproject.toml / requirements.txt   # Declares dependency on pkg-asisdb
└── src/
    ├── app.py                         # Engine initialization and queries
    └── repository/
        └── customers.py               # Data logic using asisdb
```

##### Canonical Key Schema (`ConnectionConfig`)
`ConnectionConfig` and `ConnectionConfig.from_dict()` strictly accept the following canonical keys:
*   `driver`: Target engine (`"sqlite"`, `"mssql"`, `"postgresql"`, `"mysql"`).
*   `host`: Server IP address or hostname.
*   `port`: Network port for the database service.
*   `database`: Database name or file path (SQLite).
*   `user`: Username with access permissions.
*   `password`: Authentication password (automatically encrypted to `EncryptedPassword`).
*   `explicit_url`: Complete SQLAlchemy connection URL (optional, takes precedence if defined).
*   `odbc_driver`: Specific ODBC driver name (e.g., `"ODBC Driver 18 for SQL Server"`).
*   `sql_driver_autodetect`: Enables auto-detection of the best installed ODBC driver (`True`/`False`).
*   `tds_version`: TDS protocol version for direct FreeTDS/pymssql connections.

--------------------------------------------------------------------------------

#### 🛠️ Quick Developer Guide

##### 1. Build URL and Get SQLAlchemy Engine (`ConnectionConfig`)
The canonical `ConnectionConfig` class centralizes connection parameters and resolves the appropriate URL for SQLAlchemy:

```python
from asisdb import ConnectionConfig, get_db_engine

# Connection to SQLite
cfg_sqlite = ConnectionConfig(
    driver="sqlite",
    database="my_database.db"
)
engine_sqlite = get_db_engine(config=cfg_sqlite)

# Connection to Microsoft SQL Server
cfg_mssql = ConnectionConfig(
    driver="mssql",
    host="192.168.1.100",
    database="ERP_PROD",
    user="sa",
    password="MySecurePassword2026!",
    sql_driver_autodetect=True
)
engine_mssql = get_db_engine(config=cfg_mssql)
```

--------------------------------------------------------------------------------

##### 2. Executing Queries and Statements (`execute_query` and `execute_statement`)
`pkg-asisdb` provides direct utilities for executing read queries and transactional statements:

```python
from asisdb import execute_query, execute_statement

# 1. SELECT Query: Returns a list of dictionaries with column names
customers = execute_query(
    "SELECT id, name, balance FROM customers WHERE active = :active",
    params={"active": 1}
)
for customer in customers:
    print(customer["name"], customer["balance"])

# 2. DML Statement (INSERT / UPDATE / DELETE): Executes within an auto-commit transaction
rows_affected = execute_statement(
    "UPDATE customers SET active = :active WHERE balance <= :limit",
    params={"active": 0, "limit": 0.0}
)
print(f"Updated rows: {rows_affected}")
```

--------------------------------------------------------------------------------

##### 3. Secure Management and Dynamic Password Encryption (`EncryptedPassword`)
For `asisdb`, the source of the `password` parameter is **completely transparent**: whether provided as a plaintext string, an already protected object, or retrieved from an external manager, `ConnectionConfig` automatically encapsulates and encrypts it in memory as an immutable instance of `EncryptedPassword`.

```python
from asisdb import ConnectionConfig, encrypt_password

# Case 1: Direct assignment (automatic, transparent in-memory encryption)
cfg_direct = ConnectionConfig(
    driver="postgresql",
    host="192.168.1.100",
    database="accounting",
    user="postgres",
    password="MySecurePassword2026!"  # asisdb immediately transforms it to EncryptedPassword
)

print(repr(cfg_direct.password))  # <EncryptedPassword: PROTECTED>
print(str(cfg_direct.password))   # ********

# Case 2: Recommended integration with configuration managers (pkg-asiscfg)
# Retrieves resolved credentials in a decoupled manner and asisdb encapsulates them securely
cfg_corporate = ConnectionConfig(
    driver="mssql",
    host="SRV-SQL",
    database="ERP_PROD",
    user="sa",
    password=config.valorpass_parent(...),  # Provided by pkg-asiscfg
    sql_driver_autodetect=True
)

# Case 3: Explicit or manual prior encryption
encrypted_pass = encrypt_password("MySecurePassword2026!")
cfg_manual = ConnectionConfig(
    driver="sqlite",
    database="secure.db",
    password=encrypted_pass
)
```

>[!TIP] **Transparent Encryption and Integration with `pkg-asiscfg`**:
>`asisdb` guarantees that passwords **never remain in plaintext in memory or logs**, encrypting them automatically and idempotently regardless of whether they originate from a direct value, an environment variable, or an external function.
>
>For production projects and enterprise deployments, it is recommended to manage credentials and connection parameters in a decoupled way—for example, using [`pkg-asiscfg`](https://github.com/borispinto/pkg-asiscfg) (via methods such as `config.valorpass(...)`, `config.valorpass_profile(...)`, and `config.valorpass_parent(...)`), avoiding hardcoded passwords in scripts or source code.
>
>Even if a developer accidentally runs `logger.info("Configuration: %s", cfg.__dict__)`, the `password` attribute will print `<EncryptedPassword: PROTECTED>`, preventing actual passwords from being indexed in observability systems.

--------------------------------------------------------------------------------

##### 4. Connection Testing and Diagnostics (`test_connection`)
Verifies database server connectivity without exposing credentials in diagnostic logs:

```python
from asisdb import test_connection, test_db_connection, ConnectionConfig

# 1. Universal test with detailed diagnostics
success, message, diag = test_connection(
    driver="mssql",
    host="SRV-SQL",
    database="ERP_PROD",
    user="sa",
    password="super_password",
    encrypted_fields=["custom_token"]  # Additional fields to mask
)

print(success)            # True / False
print(message)            # Descriptive result message
print(diag["target_url"]) # Generated URL with masked password: mssql+pyodbc://sa:********@SRV-SQL/ERP_PROD...

# 2. Simplified test from a ConnectionConfig instance
cfg = ConnectionConfig(driver="sqlite", database="test.db")
ok, msg = test_db_connection(cfg)
```

--------------------------------------------------------------------------------

##### 5. Canonical Configuration via Dictionaries (`from_dict`)
You can initialize configurations directly from canonical dictionaries obtained from environment variables, JSON/YAML files, or your own configuration manager:

```python
from asisdb import ConnectionConfig, get_db_engine, encrypt_password

# 1. Standard dictionary (password is automatically encrypted in memory)
connection_data = {
    "driver": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "warehouse",
    "user": "root",
    "password": "Password123"
}
cfg = ConnectionConfig.from_dict(connection_data)
engine = get_db_engine(config=cfg)

# 2. Dictionary with previously encrypted password
secure_data = {
    "driver": "postgresql",
    "host": "10.0.0.5",
    "database": "payroll",
    "user": "admin",
    "password": encrypt_password("MyCorporatePassword!")
}
cfg_secure = ConnectionConfig.from_dict(secure_data)
engine_secure = get_db_engine(config=cfg_secure)
```

--------------------------------------------------------------------------------

##### 6. Managing Multiple Simultaneous Engines
The manager allows caching multiple database engines associated with different logical keys:

```python
from asisdb import ConnectionConfig, get_db_engine, close_engine, reset_engine

# 1. Primary engine (Operational ERP)
engine_erp = get_db_engine(
    config=ConnectionConfig(driver="mssql", host="SRV-ERP", database="ERP_PROD"),
    key="primary"
)

# 2. Audit engine (Local SQLite database)
engine_audit = get_db_engine(
    config=ConnectionConfig(driver="sqlite", database="audit.db"),
    key="audit"
)

# 3. Release a specific engine when the task is complete
close_engine(key="audit")

# 4. Release all cached engines and active security keys upon app shutdown
reset_engine()
```

--------------------------------------------------------------------------------

##### 7. Direct Reading and Caching of FoxPro / dBase Tables (`DBFReader` and `DBFCacheManager`)
`pkg-asisdb` includes native, optimized utilities to query DBF tables without installing heavy third-party libraries:

```python
from asisdb import DBFReader, DBFCacheManager

# 1. Direct streaming read of a single record
record = DBFReader.find_one("CUSTOMERS.DBF", lambda row: row.get("CODE") == "C001")
if record:
    print(record["NAME"], record["BALANCE"])

# 2. Indexed in-memory cache for O(1) performance
cache = DBFCacheManager.get_instance()
customers_table = cache.get_table("CUSTOMERS.DBF", index_field="CODE")
customer = customers_table.get("C001")
```

--------------------------------------------------------------------------------

##### 8. Canonical Parameter and Wildcard Interpolation
Enables dynamic parameterization of connection strings or database names using predefined wildcards:

```python
from asisdb import interpolate_db_url_placeholders

template = "mssql+pyodbc://{user}:{password}@{host}/{database}_{DATEYEAR}"
params = {
    "user": "sa",
    "password": "super_secret_password",
    "host": "192.168.1.10",
    "database": "COMPANY"
}

final_url = interpolate_db_url_placeholders(template, params)
# Generates: mssql+pyodbc://sa:super_secret_password@192.168.1.10/COMPANY_2026
```

--------------------------------------------------------------------------------

#### 🧪 Automated Tests

The unit and integration test suite of `pkg-asisdb` ensures password security, URL assembly, and multi-engine compatibility:

```powershell
py -m pytest
```

Or specifying the test suite path:
```powershell
python -m pytest tests/
```

--------------------------------------------------------------------------------

#### 👥 Contact and Support
This project is developed and maintained by **Boris Pinto**, in collaboration with **Asisnet Computación, CA**.

##### 🛠️ Authorship and Personal Brand
If you would like to collaborate on open source projects or connect professionally:
*   **Developer:** Boris Pinto
*   **Personal Email:** [borispinto@gmail.com](mailto:borispinto@gmail.com)
*   **GitHub Profile:** [@borispinto](https://github.com/borispinto)

##### 🏢 Enterprise Solutions and Connectivity
Need to adapt this tool to your business, require corporate technical support, or look for custom technological infrastructure? At **Asisnet Computación, CA**, we integrate software and hardware to optimize your operations.
*   **Our Services:**
    *   **Administrative Software:** Custom systems for business management and control.
    *   **Networks and Communications:** Design, installation, and technical support for networks, infrastructure, and connectivity.
    *   **Technological Equipment:** Sales, support, and maintenance of hardware.
*   **Business Inquiries:** [proyectos@asisnet.net](mailto:proyectos@asisnet.net)

--------------------------------------------------------------------------------

#### 📄 License
This project is licensed under the [MIT License](LICENSE). It is free and open-source software, fully authorized for use, modification, and integration into commercial and enterprise solutions.

Copyright (c) 2026 Boris Pinto. All rights reserved.
