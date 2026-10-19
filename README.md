# 🗄️ pkg-asisdb

[🇪🇸 Español](README.md) | [🇺🇸 English](README.en.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://www.python.org/) [![Platform: 32/64-bit](https://img.shields.io/badge/platform-32%20%7C%2064--bit-blue.svg)](#-instalación) [![Architecture: Multi--Engine%20%26%20DBF](https://img.shields.io/badge/architecture-multi--engine%20%26%20DBF-orange.svg)](#️-arquitectura-de-seguridad-y-gestión-de-conexiones) [![Security: Memory Encryption](https://img.shields.io/badge/security-memory%20encryption-brightgreen.svg)](#3-gestión-segura-y-cifrado-dinámico-de-contraseñas-encryptedpassword)

Este paquete proporciona una solución base y ligera para la **gestión de bases de datos multi-motor (SQLAlchemy) y acceso a tablas FoxPro/dBase (DBF)**, enfocada principalmente en la estandarización de credenciales seguras, pruebas de conexión y utilidades esenciales de acceso a datos para proyectos Python (aplicaciones de escritorio como PyQt/CustomTkinter, herramientas CLI, scripts o microservicios).

En su versión actual, **pkg-asisdb** constituye un componente fundacional concebido para potenciarse y expandirse progresivamente hasta formar parte integral del ecosistema **Asisnet**. Por ahora está orientado a tareas clave de diagnóstico y verificación de conectividad, invitando a estar atentos a las próximas versiones a medida que se incorporen capacidades avanzadas.

--------------------------------------------------------------------------------

#### 📋 Tabla de Contenidos

1. [🎯 ¿Por qué pkg-asisdb? (Propósito e Intención)](#-por-qué-pkg-asisdb-propósito-e-intención)
2. [🚀 Capacidades y Características Clave](#-capacidades-y-características-clave)
3. [📦 Instalación](#-instalación)
4. [🏗️ Arquitectura de Seguridad y Gestión de Conexiones](#️-arquitectura-de-seguridad-y-gestión-de-conexiones)
5. [📁 Estructura del Proyecto y Esquema Canónico de Datos](#-estructura-del-proyecto-y-esquema-canónico-de-datos)
6. [🛠️ Guía Rápida para Desarrolladores](#️-guía-rápida-para-desarrolladores)
   - [1. Construir URL y Obtener Motor SQLAlchemy (`ConnectionConfig`)](#1-construir-url-y-obtener-motor-sqlalchemy-connectionconfig)
   - [2. Ejecución de Consultas y Modificaciones (`execute_query` y `execute_statement`)](#2-ejecución-de-consultas-y-modificaciones-execute_query-y-execute_statement)
   - [3. Gestión Segura y Cifrado Dinámico de Contraseñas (`EncryptedPassword`)](#3-gestión-segura-y-cifrado-dinámico-de-contraseñas-encryptedpassword)
   - [4. Pruebas y Diagnóstico de Conexión (`test_connection`)](#4-pruebas-y-diagnóstico-de-conexión-test_connection)
   - [5. Configuración Canónica mediante Diccionarios (`from_dict`)](#5-configuración-canónica-mediante-diccionarios-from_dict)
   - [6. Gestión de Múltiples Motores Simultáneos](#6-gestión-de-múltiples-motores-simultáneos)
   - [7. Lectura Directa y Caché de Tablas FoxPro / dBase (`DBFReader` y `DBFCacheManager`)](#7-lectura-directa-y-caché-de-tablas-foxpro--dbase-dbfreader-y-dbfcachemanager)
   - [8. Interpolación Canónica de Parámetros y Comodines](#8-interpolación-canónica-de-parámetros-y-comodines)
7. [🧪 Pruebas Automatizadas](#-pruebas-automatizadas)
8. [👥 Contacto y Soporte](#-contacto-y-soporte)
9. [📄 Licencia](#-licencia)

--------------------------------------------------------------------------------

#### 🎯 ¿Por qué pkg-asisdb? (Propósito e Intención)
En el desarrollo de aplicaciones empresariales, servicios corporativos y sistemas de sincronización de datos, la gestión de conexiones y acceso a datos suele afrontar **desafíos críticos y vulnerabilidades recurrentes**:
*   **Credenciales expuestas en texto plano**: Contraseñas que viajan en variables de texto plano legibles en logs de consola, volcados de memoria, serializaciones accidentales o tracebacks de excepciones.
*   **Heterogeneidad de drivers y motores**: Disparidad de sintaxis de conexión entre Microsoft SQL Server, PostgreSQL, MySQL y SQLite, además de la necesidad de detectar cuál driver ODBC de SQL Server está realmente instalado en la máquina del cliente final.
*   **Cadenas de conexión dispersas y frágiles**: Construcción manual de URLs de SQLAlchemy con parámetros inconsistentes, aliases no controlados o caracteres especiales no escapados.
*   **Convivencia con tablas históricas FoxPro / dBase (DBF)**: Dificultad para consultar tablas masivas heredadas sin depender de controladores OLE DB obsoletos de 32 bits o librerías externas lentas y pesadas.
*   **Falta de diagnósticos seguros**: Imposibilidad de probar conectividad y depurar incidencias de red sin filtrar la contraseña en los logs de diagnóstico.

**pkg-asisdb nace para abordar de raíz estas necesidades desde un enfoque ágil y modular**, proveyendo una solución base confiable para pruebas de conexión, con una hoja de ruta orientada al ecosistema completo:
1.  **Cifrado Dinámico de Contraseñas en Memoria (`EncryptedPassword`)**: Protección automática y universal de contraseñas mediante claves de sesión efímeras de 256 bits, garantizando que jamás se exponga la contraseña en texto plano en memoria, representaciones textuales o volcados.
2.  **Capa Unificada Multi-Motor**: Ensamblaje transparente de URLs de conexión para MSSQL (ODBC / pymssql), PostgreSQL, MySQL y SQLite bajo un contrato canónico estricto (`ConnectionConfig`).
3.  **Detección Inteligente de Drivers ODBC**: Selección y persistencia en caché del mejor driver nativo de SQL Server disponible en el sistema operativo.
4.  **Lector DBF Nativo de Alto Rendimiento**: Acceso directo y streaming inverso sin drivers externos, con caché indexada en memoria $O(1)$ (`DBFCacheManager`).
5.  **Diagnósticos Deterministas sin Fuga de Credenciales**: Suite de pruebas y validación (`test_connection`) que enmascara automáticamente credenciales en logs y URLs.

--------------------------------------------------------------------------------

#### 🚀 Capacidades y Características Clave
*   **Gestión Unificada de Motores SQL**: Soporte directo y estandarizado para MSSQL (ODBC nativo / `pymssql`), SQLite, PostgreSQL y MySQL a través de SQLAlchemy.
*   **Cifrado Dinámico y Universal de Contraseñas (`EncryptedPassword`)**:
    *   Contenedor inmutable que ofusca cualquier representación textual (`__repr__` como `<EncryptedPassword: PROTECTED>` y `__str__` como `********`).
    *   Clave de cifrado efímera desacoplada de 256 bits (`_SESSION_KEYS`), impidiendo que el objeto sea descifrable fuera del contexto de sesión activa.
    *   Cifrado universal y transparente al instanciar `ConnectionConfig` o invocar utilidades de conexión.
    *   Descifrado strictly-in-time en el último instante al interactuar con el conector del driver, erradicando variables intermedias en texto plano.
*   **Detección Automática y Priorización de Drivers ODBC MSSQL**: Detección dinámica en Windows/Linux del driver ODBC más moderno disponible (`ODBC Driver 18 for SQL Server`, `17`, `SQL Server Native Client`, etc.), con persistencia en caché para evitar re-escaneos.
*   **Lector Streaming y Caché de Tablas FoxPro / dBase (DBF)**:
    *   Compatible al 100% con arquitecturas de **32 bits y 64 bits**, eliminando definitivamente la dependencia del antiguo controlador OLE DB (`VFPOLEDB.dll`) de 32 bits.
    *   `DBFReader`: Lectura de tablas DBF de cualquier tamaño por streaming inverso y escaneo directo de registros mediante offset fijo.
    *   `DBFCacheManager`: Carga indexada en memoria para consultas inmediatas con rendimiento $O(1)$.
*   **Interpolación Canónica de Parámetros y Comodines**: Soporte seguro de comodines en cadenas de conexión (`{database}`, `{host}`, `{user}`, `{puerto}`) y comodines temporales dinámicos (`{DATEYEAR}`, `{TIMESTAMP}`).
*   **Contrato Estricto `ConnectionConfig`**: Configuración canónica sin ambigüedades, libre de valores de negocio asumidos por defecto.
*   **Pool de Motores Multi-Instancia**: Mantenimiento en caché de múltiples motores activos simultáneamente (`primary`, `auditoria`, `historico`), con funciones dedicadas de cierre selectivo (`close_engine`) y reinicio general (`reset_engine`).
*   **Internacionalización Nativa con `pkg-i18n`**: Mensajes de diagnóstico y advertencias integrados con el catálogo de traducción corporativo de Asisnet bajo el prefijo `[asisdb]`.

--------------------------------------------------------------------------------

#### 📦 Instalación

##### 1. Instalación Directa desde GitHub (Recomendado)
Instalación del núcleo base en el entorno virtual mediante pip:
```powershell
pip install git+https://github.com/borispinto/pkg-asisdb.git
```

Con conectores específicos para tu motor (extras):
```powershell
# Para Microsoft SQL Server (Entorno Asisnet)
pip install "pkg-asisdb[mssql] @ git+https://github.com/borispinto/pkg-asisdb.git"

# Para PostgreSQL
pip install "pkg-asisdb[postgres] @ git+https://github.com/borispinto/pkg-asisdb.git"

# Para MySQL
pip install "pkg-asisdb[mysql] @ git+https://github.com/borispinto/pkg-asisdb.git"

# Todos los motores y pruebas
pip install "pkg-asisdb[all] @ git+https://github.com/borispinto/pkg-asisdb.git"
```

O declarándolo en tu archivo `pyproject.toml`:
```toml
[project]
dependencies = [
    "pkg-asisdb[mssql] @ git+https://github.com/borispinto/pkg-asisdb.git",
]
```

--------------------------------------------------------------------------------

##### 2. Instalación desde el Código Fuente Local y Requirements por Motor
Clonación e instalación estándar en modo editable:
```powershell
git clone https://github.com/borispinto/pkg-asisdb.git
cd pkg-asisdb
pip install -e .
```

Instalación modular según el motor de base de datos requerido:
```powershell
# A. Núcleo Base (SQLite y FoxPro DBF)
pip install -r requirements.txt

# B. Microsoft SQL Server (pyodbc + pymssql - Estándar Asisnet)
pip install -r requirements-mssql.txt

# C. PostgreSQL (psycopg2-binary)
pip install -r requirements-postgres.txt

# D. MySQL y MariaDB (pymysql)
pip install -r requirements-mysql.txt

# E. Entorno de Desarrollo y Pruebas (pytest)
pip install -r requirements-dev.txt

# F. Instalación Completa (todos los motores y herramientas)
pip install -r requirements-all.txt
```

>[!NOTE] **Compatibilidad de Arquitectura y Dependencias**:
>*   **Arquitecturas 32-bit y 64-bit**: `pkg-asisdb` es totalmente agnóstico de arquitectura y opera de forma idéntica en entornos Python de **32 bits y 64 bits**. La lectura de tablas DBF se ejecuta en Python puro mediante `dbfread>=2.0.7` y acceso binario directo por offsets, prescindiendo por completo de controladores OLE DB u ODBC externos.
>*   **Núcleo de Producción**: Requiere `SQLAlchemy>=2.0.0`, `dbfread>=2.0.7` y `pkg-i18n>=1.0.0`.
>*   **Conectores SQL**: Se instalan de forma predecible y modular mediante el archivo `requirements-*.txt` correspondiente al motor utilizado por tu proyecto.

--------------------------------------------------------------------------------

#### 🏗️ Arquitectura de Seguridad y Gestión de Conexiones

`pkg-asisdb` implementa una arquitectura defensiva en profundidad para evitar la fuga o exposición inadvertida de credenciales y garantizar robustez en entornos de alta concurrencia:

| Componente / Capa | Mecanismo | Beneficio Operativo |
| :--- | :--- | :--- |
| **`EncryptedPassword`** | Contenedor inmutable cifrado con clave de sesión efímera de 256 bits | Previene la lectura de la contraseña en memoria mediante volcados o depuradores |
| **Ofuscación Universal** | Métodos `__repr__` (`<EncryptedPassword: PROTECTED>`) y `__str__` (`********`) | Blindaje total frente a `print()`, serializaciones JSON accidentales o volcados de logs |
| **Descifrado In-Line** | Desencriptación en el instante exacto de apertura del socket o conexión | Erradica variables locales en texto plano en la pila de ejecución |
| **Enmascaramiento Determinista** | Sanitización de contraseñas y campos definidos en `encrypted_fields` | Diagnósticos y URLs generadas para logs completamente seguras |
| **Pool Multi-Motor** | Gestión indexada de engines por clave (`key="primary"`, `key="replica"`) | Control granular del ciclo de vida y liberación de recursos de base de datos |

--------------------------------------------------------------------------------

#### 📁 Estructura del Proyecto y Esquema Canónico de Datos

##### Estructura recomendada en tu proyecto consumidor
```text
mi_proyecto/
├── pyproject.toml / requirements.txt   # Declara dependencia a pkg-asisdb
└── src/
    ├── app.py                         # Inicialización de motores y consultas
    └── repository/
        └── clientes.py                # Lógica de datos usando asisdb
```

##### Esquema de Claves Canónicas (`ConnectionConfig`)
`ConnectionConfig` y `ConnectionConfig.from_dict()` aceptan estrictamente las siguientes claves canónicas:
*   `driver`: Motor de destino (`"sqlite"`, `"mssql"`, `"postgresql"`, `"mysql"`).
*   `host`: Dirección IP o nombre de host del servidor.
*   `port`: Puerto de red del servicio de base de datos.
*   `database`: Nombre de la base de datos o ruta de archivo (SQLite).
*   `user`: Nombre de usuario con permisos de acceso.
*   `password`: Contraseña de autenticación (se cifra automáticamente a `EncryptedPassword`).
*   `explicit_url`: URL de conexión completa de SQLAlchemy (opcional, tiene prioridad si se define).
*   `odbc_driver`: Nombre específico del driver ODBC (ej. `"ODBC Driver 18 for SQL Server"`).
*   `sql_driver_autodetect`: Activa la autodetección del mejor driver ODBC instalado (`True`/`False`).
*   `tds_version`: Versión de protocolo TDS para conexiones directas FreeTDS/pymssql.

--------------------------------------------------------------------------------

#### 🛠️ Guía Rápida para Desarrolladores

##### 1. Construir URL y Obtener Motor SQLAlchemy (`ConnectionConfig`)
La clase canónica `ConnectionConfig` centraliza los parámetros de conexión y resuelve la URL adecuada para SQLAlchemy:

```python
from asisdb import ConnectionConfig, get_db_engine

# Conexión a SQLite
cfg_sqlite = ConnectionConfig(
    driver="sqlite",
    database="mi_base_datos.db"
)
engine_sqlite = get_db_engine(config=cfg_sqlite)

# Conexión a Microsoft SQL Server
cfg_mssql = ConnectionConfig(
    driver="mssql",
    host="192.168.1.100",
    database="ERP_PROD",
    user="sa",
    password="MiClaveSegura2026!",
    sql_driver_autodetect=True
)
engine_mssql = get_db_engine(config=cfg_mssql)
```

--------------------------------------------------------------------------------

##### 2. Ejecución de Consultas y Modificaciones (`execute_query` y `execute_statement`)
`pkg-asisdb` provee utilidades directas para ejecutar consultas de lectura y sentencias transaccionales:

```python
from asisdb import execute_query, execute_statement

# 1. Consulta SELECT: Retorna una lista de diccionarios con nombres de columnas
clientes = execute_query(
    "SELECT id, nombre, saldo FROM clientes WHERE activo = :activo",
    params={"activo": 1}
)
for cliente in clientes:
    print(cliente["nombre"], cliente["saldo"])

# 2. Sentencia DML (INSERT / UPDATE / DELETE): Ejecuta en transacción auto-commit
filas_afectadas = execute_statement(
    "UPDATE clientes SET activo = :activo WHERE saldo <= :limite",
    params={"activo": 0, "limite": 0.0}
)
print(f"Filas actualizadas: {filas_afectadas}")
```

--------------------------------------------------------------------------------

##### 3. Gestión Segura y Cifrado Dinámico de Contraseñas (`EncryptedPassword`)
Para `asisdb`, el origen del parámetro `password` es **completamente transparente**: tanto si se suministra una cadena en texto plano como si proviene de un objeto ya protegido o de un gestor externo, `ConnectionConfig` lo encapsula y cifra automáticamente en memoria como una instancia inmutable de `EncryptedPassword`.

```python
from asisdb import ConnectionConfig, encrypt_password

# Caso 1: Asignación directa (cifrado automático y transparente en memoria)
cfg_directo = ConnectionConfig(
    driver="postgresql",
    host="192.168.1.100",
    database="contabilidad",
    user="postgres",
    password="MiClaveSegura2026!"  # asisdb lo transforma inmediatamente a EncryptedPassword
)

print(repr(cfg_directo.password))  # <EncryptedPassword: PROTECTED>
print(str(cfg_directo.password))   # ********

# Caso 2: Integración recomendada con gestores de configuración (pkg-asiscfg)
# Obtiene la credencial resuelta de forma desacoplada y asisdb la encapsula de forma segura
cfg_corporativo = ConnectionConfig(
    driver="mssql",
    host="SRV-SQL",
    database="ERP_PROD",
    user="sa",
    password=config.valorpass_parent(...),  # Proveído por pkg-asiscfg
    sql_driver_autodetect=True
)

# Caso 3: Cifrado manual o explícito previo
clave_cifrada = encrypt_password("MiClaveSegura2026!")
cfg_manual = ConnectionConfig(
    driver="sqlite",
    database="segura.db",
    password=clave_cifrada
)
```

>[!TIP] **Cifrado Transparente e Integración con `pkg-asiscfg`**:
>`asisdb` garantiza que la contraseña **nunca permanezca en texto plano en memoria ni en logs**, cifrándola de forma automática e idempotente sin importar si proviene de un valor directo, una variable de entorno o una función externa.
>
>Para proyectos de producción y despliegues empresariales, se recomienda gestionar las credenciales y parámetros de conexión de manera desacoplada, por ejemplo: utilizando [`pkg-asiscfg`](https://github.com/borispinto/pkg-asiscfg) (mediante métodos como `config.valorpass(...)`, `config.valorpass_profile(...)` y `config.valorpass_parent(...)`), evitando almacenar contraseñas en scripts o código fuente.
>
>Incluso si por error un desarrollador ejecuta `logger.info("Configuración: %s", cfg.__dict__)`, el atributo `password` imprimirá `<EncryptedPassword: PROTECTED>`, impidiendo que contraseñas reales queden indexadas en sistemas de observabilidad.

--------------------------------------------------------------------------------

##### 4. Pruebas y Diagnóstico de Conexión (`test_connection`)
Verifica la conectividad con el servidor de base de datos sin exponer credenciales en logs de diagnóstico:

```python
from asisdb import test_connection, test_db_connection, ConnectionConfig

# 1. Prueba universal con diagnóstico detallado
exito, mensaje, diag = test_connection(
    driver="mssql",
    host="SRV-SQL",
    database="ERP_PROD",
    user="sa",
    password="super_password",
    encrypted_fields=["token_personalizado"]  # Campos adicionales a enmascarar
)

print(exito)              # True / False
print(mensaje)            # Mensaje descriptivo del resultado
print(diag["target_url"]) # URL generada con contraseña enmascarada: mssql+pyodbc://sa:********@SRV-SQL/ERP_PROD...

# 2. Prueba simplificada a partir de una instancia de ConnectionConfig
cfg = ConnectionConfig(driver="sqlite", database="test.db")
ok, msg = test_db_connection(cfg)
```

--------------------------------------------------------------------------------

##### 5. Configuración Canónica mediante Diccionarios (`from_dict`)
Puedes inicializar la configuración directamente a partir de diccionarios canónicos provenientes de variables de entorno, archivos JSON/YAML o tu propio gestor de configuración:

```python
from asisdb import ConnectionConfig, get_db_engine, encrypt_password

# 1. Diccionario estándar (la contraseña se cifra automáticamente en memoria)
datos_conexion = {
    "driver": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "almacen",
    "user": "root",
    "password": "Password123"
}
cfg = ConnectionConfig.from_dict(datos_conexion)
engine = get_db_engine(config=cfg)

# 2. Diccionario con contraseña previamente cifrada
datos_seguros = {
    "driver": "postgresql",
    "host": "10.0.0.5",
    "database": "nominas",
    "user": "admin",
    "password": encrypt_password("MiClaveCorporativa!")
}
cfg_seguro = ConnectionConfig.from_dict(datos_seguros)
engine_seguro = get_db_engine(config=cfg_seguro)
```

--------------------------------------------------------------------------------

##### 6. Gestión de Múltiples Motores Simultáneos
El gestor permite mantener en caché múltiples motores de bases de datos asociados a diferentes claves lógicas:

```python
from asisdb import ConnectionConfig, get_db_engine, close_engine, reset_engine

# 1. Motor principal (ERP Operativo)
engine_erp = get_db_engine(
    config=ConnectionConfig(driver="mssql", host="SRV-ERP", database="ERP_PROD"),
    key="primary"
)

# 2. Motor de auditoría (Base de datos local SQLite)
engine_audit = get_db_engine(
    config=ConnectionConfig(driver="sqlite", database="auditoria.db"),
    key="audit"
)

# 3. Liberar un motor específico cuando termine la tarea
close_engine(key="audit")

# 4. Liberar todos los motores en caché y claves de seguridad activas al cerrar la app
reset_engine()
```

--------------------------------------------------------------------------------

##### 7. Lectura Directa y Caché de Tablas FoxPro / dBase (`DBFReader` y `DBFCacheManager`)
`pkg-asisdb` incluye utilidades nativas optimizadas para consultar tablas DBF sin instalar librerías pesadas:

```python
from asisdb import DBFReader, DBFCacheManager

# 1. Lectura directa streaming de un registro
registro = DBFReader.find_one("CLIENTES.DBF", lambda row: row.get("CODIGO") == "C001")
if registro:
    print(registro["NOMBRE"], registro["SALDO"])

# 2. Caché indexada en memoria para rendimiento O(1)
cache = DBFCacheManager.get_instance()
tabla_clientes = cache.get_table("CLIENTES.DBF", index_field="CODIGO")
cliente = tabla_clientes.get("C001")
```

--------------------------------------------------------------------------------

##### 8. Interpolación Canónica de Parámetros y Comodines
Permite parametrizar cadenas de conexión o nombres de bases de datos dinámicamente mediante comodines predefinidos:

```python
from asisdb import interpolate_db_url_placeholders

plantilla = "mssql+pyodbc://{user}:{password}@{host}/{database}_{DATEYEAR}"
params = {
    "user": "sa",
    "password": "super_secret_password",
    "host": "192.168.1.10",
    "database": "EMPRESA"
}

url_final = interpolate_db_url_placeholders(plantilla, params)
# Genera: mssql+pyodbc://sa:super_secret_password@192.168.1.10/EMPRESA_2026
```

--------------------------------------------------------------------------------

#### 🧪 Pruebas Automatizadas

La suite de pruebas unitarias y de integración de `pkg-asisdb` garantiza la seguridad de contraseñas, ensamblaje de URLs y compatibilidad multi-motor:

```powershell
py -m pytest
```

O especificando la ruta de la suite:
```powershell
python -m pytest tests/
```

--------------------------------------------------------------------------------

#### 👥 Contacto y Soporte
Este proyecto es desarrollado y mantenido por **Boris Pinto**, en colaboración con **Asisnet Computación, CA**.

##### 🛠️ Autoría y Marca Personal
Si deseas colaborar en proyectos de código abierto o conectar profesionalmente:
*   **Desarrollador:** Boris Pinto
*   **Correo Personal:** [borispinto@gmail.com](mailto:borispinto@gmail.com)
*   **GitHub Profile:** [@borispinto](https://github.com/borispinto)

##### 🏢 Soluciones Empresariales y Conectividad
¿Necesitas adaptar esta herramienta a tu negocio, requieres soporte técnico corporativo o buscas una infraestructura tecnológica a la medida? En **Asisnet Computación, CA** integramos software y hardware para optimizar tu operación.
*   **Nuestros Servicios:**
    *   **Software Administrativo:** Sistemas a la medida para la gestión y control de tu negocio.
    *   **Redes y Comunicaciones:** Diseño, instalación y soporte técnico para redes, infraestructura y conectividad.
    *   **Equipos Tecnológicos:** Venta, soporte y mantenimiento de equipos.
*   **Contacto Comercial:** [proyectos@asisnet.net](mailto:proyectos@asisnet.net)

--------------------------------------------------------------------------------

#### 📄 Licencia
Este proyecto está bajo la Licencia [MIT](LICENSE). Es software libre y de código abierto, totalmente autorizado para su uso, modificación e integración en soluciones comerciales y empresariales.

Copyright (c) 2026 Boris Pinto. Todos los derechos reservados.
