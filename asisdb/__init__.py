# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 ASISNET Computación, CA <proyectos@asisnet.net>
# SPDX-FileCopyrightText: 2026 Boris Pinto <borispinto@gmail.com>
# SPDX-License-Identifier: MIT
# Autor: Boris Pinto <borispinto@gmail.com>
# Contacto Institucional: ASISNET Computación, CA <proyectos@asisnet.net>
# File: asisdb/__init__.py

"""
Librería asisdb: Gestión de Conexiones de Datos y Ejecución de Comandos 100% Independiente.
Ofrece:
- Ejecutar comandos (execute_query, execute_statement)
- Cerrar conexiones y gestión de ciclo de vida (close_engine, reset_engine)
- Manejo limpio de errores de conexión y resiliencia multi-motor.
"""

__title__ = "pkg-asisdb"
__version__ = "1.0.0"
__author__ = "Boris Pinto"
__email__ = "borispinto@gmail.com"
__maintainer__ = "ASISNET Computación, CA"
__copyright__ = "Copyright (c) 2026 Boris Pinto"
__license__ = "MIT"

from typing import Dict, Any
from .connection_config import ConnectionConfig
from .engine import (
    interpolate_placeholders,
    interpolate_db_url_placeholders,
    build_db_url,
    get_db_engine,
    init_db,
    verify_db_structure,
    reset_engine,
    close_engine,
    execute_query,
    execute_statement,
    LITERAL,
    test_connection,
    test_db_connection,
    get_supported_drivers,
    SUPPORTED_DRIVERS,
    MSSQL_ODBC_DRIVERS_PRIORITY,
    get_best_mssql_odbc_driver,
    resolve_odbc_driver_for_machine,
    get_machine_cached_odbc_driver,
    save_machine_cached_odbc_driver
)
from .dbf_engine import (
    DBFReader,
    DBFCacheManager,
    get_dbf_cache
)
from .security import (
    EncryptedPassword,
    encrypt_password,
    decrypt_password,
    create_security_session,
    clear_security_session,
    clear_all_security_sessions
)

DEFAULT_DB_MESSAGES: Dict[str, Any] = {
    "db": {
        "engine_created": "[asisdb] Motor de base de datos inicializado exitosamente para {url}",
        "tables_created": "[asisdb] Tablas verificadas/creadas exitosamente.",
        "engine_closed": "[asisdb] Motor de base de datos cerrado y recursos liberados.",
        "connect_fallback": "[asisdb] No se pudo conectar al motor DB configurado ({err}). Aplicando fallback a SQLite local ('sqlite:///middleware_local.db').",
        "sqlite_initialized": "[asisdb] Tablas verificadas/creadas en SQLite de respaldo.",
        "no_metadata_error": "[asisdb] No se proporcionaron MetaData para la inicialización."
    }
}

# Auto-registro del diccionario inicial en código (Capa 0) en i18n
try:
    from i18n import get_i18n_instance
    get_i18n_instance().register_defaults(DEFAULT_DB_MESSAGES)
except ImportError:
    pass

__all__ = [
    "ConnectionConfig",
    "interpolate_placeholders",
    "interpolate_db_url_placeholders",
    "build_db_url",
    "get_db_engine",
    "init_db",
    "verify_db_structure",
    "reset_engine",
    "close_engine",
    "execute_query",
    "execute_statement",
    "LITERAL",
    "test_connection",
    "test_db_connection",
    "get_supported_drivers",
    "SUPPORTED_DRIVERS",
    "MSSQL_ODBC_DRIVERS_PRIORITY",
    "get_best_mssql_odbc_driver",
    "resolve_odbc_driver_for_machine",
    "get_machine_cached_odbc_driver",
    "save_machine_cached_odbc_driver",
    "DBFReader",
    "DBFCacheManager",
    "get_dbf_cache",
    "DEFAULT_DB_MESSAGES",
    "EncryptedPassword",
    "encrypt_password",
    "decrypt_password",
    "create_security_session",
    "clear_security_session",
    "clear_all_security_sessions"
]
