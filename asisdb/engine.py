# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 ASISNET Computación, CA <proyectos@asisnet.net>
# SPDX-FileCopyrightText: 2026 Boris Pinto <borispinto@gmail.com>
# SPDX-License-Identifier: MIT
# Autor: Boris Pinto <borispinto@gmail.com>
# Contacto Institucional: ASISNET Computación, CA <proyectos@asisnet.net>
# File: asisdb/engine.py

"""
Módulo Principal de Motores y Ejecución SQL (asisdb).
Gestiona la construcción de URLs de conexión, pooling SQLAlchemy, ejecución resiliente y pruebas de conectividad.
"""

import re
import logging
import os
import urllib.parse
from typing import Optional, Any, Tuple, Dict, List, Union, Sequence
from sqlalchemy import create_engine, Engine, MetaData, text
from i18n import t18n
from .connection_config import ConnectionConfig
from .security import EncryptedPassword, encrypt_password, decrypt_password, clear_all_security_sessions
# try:
#     from i18n import t18n
# except ImportError:
#     def t18n(key: str, default: str = "", **kwargs: Any) -> str:
#         msg = default or key
#         if kwargs:
#             try:
#                 return msg.format(**kwargs)
#             except Exception:
#                 return msg
#         return msg

_ENGINE: Optional[Engine] = None
_ENGINES: Dict[str, Engine] = {}
SUPPORTED_DRIVERS = [
    "mssql",
    "postgresql",
    "mysql",
    "sqlite",
    "foxpro"
]

def interpolate_placeholders(text_template: str, params: Dict[str, Any]) -> str:
    """
    Interpola comodines con sintaxis dual ([campo] y {campo}) en cadenas de texto
    a partir del diccionario de parámetros suministrado y comodines de fecha estándar.
    """
    if not text_template or not isinstance(text_template, str):
        return ""

    res = text_template.strip()
    replacements: Dict[str, str] = {}

    try:
        from datetime import datetime as dt_cls
        now_dt = dt_cls.now()
        replacements.update({
            "DATEYEAR": now_dt.strftime("%Y"),
            "DATEMONTH": now_dt.strftime("%m"),
            "DATEDAY": now_dt.strftime("%d"),
            "DATEHOUR": now_dt.strftime("%H"),
            "DATEMINUTE": now_dt.strftime("%M"),
            "DATESECOND": now_dt.strftime("%S"),
            "TIMESTAMP": now_dt.strftime("%Y%m%d_%H%M%S"),
        })
    except Exception:
        pass

    if params and isinstance(params, dict):
        for k, v in params.items():
            if v is not None and not isinstance(v, (dict, list, tuple)):
                replacements[k] = str(v)

    for key, val in replacements.items():
        pattern = rf'(\[{key}\]|\{{{key}\}})'
        res = re.sub(pattern, lambda m, v=val: v, res, flags=re.IGNORECASE)

    return res


def interpolate_db_url_placeholders(url_template: str, params: Dict[str, Any]) -> str:
    """
    Interpola comodines con sintaxis dual ([campo] y {campo}) dentro de una plantilla de db_url.
    Maneja limpiamente puertos vacíos y codificación segura de credenciales.
    """
    if not url_template or not isinstance(url_template, str):
        return ""

    url = url_template.strip()
    port = str(params.get("port") or "").strip()

    # 1. Manejo inteligente del puerto (limpiar ':' si el puerto está vacío)
    if not port:
        url = re.sub(r':\s*(\[port\]|\{port\})', '', url, flags=re.IGNORECASE)
        url = re.sub(r'(\[port\]|\{port\})', '', url, flags=re.IGNORECASE)
    else:
        url = re.sub(r':\s*(\[port\]|\{port\})', f':{port}', url, flags=re.IGNORECASE)
        url = re.sub(r'(\[port\]|\{port\})', port, url, flags=re.IGNORECASE)

    # 2. Diccionario de reemplazo genérico y determinista
    replacements: Dict[str, str] = {}
    for k, v in params.items():
        if k == "port":
            continue
        if v is not None and not isinstance(v, (dict, list, tuple)):
            if isinstance(v, EncryptedPassword):
                raw_pwd = decrypt_password(v)
                replacements[k] = urllib.parse.quote_plus(raw_pwd)
            elif k in ("password", "user"):
                replacements[k] = urllib.parse.quote_plus(str(v))
            else:
                replacements[k] = str(v)

    for key, val in replacements.items():
        pattern = rf'(\[{key}\]|\{{{key}\}})'
        url = re.sub(pattern, lambda m, v=val: v, url, flags=re.IGNORECASE)

    return url


MSSQL_ODBC_DRIVERS_PRIORITY: List[Dict[str, str]] = [
    {"name": "ODBC Driver 18 for SQL Server", "extra": "TrustServerCertificate=yes;Encrypt=optional;"},
    {"name": "ODBC Driver 17 for SQL Server", "extra": "TrustServerCertificate=yes;"},
    {"name": "ODBC Driver 13 for SQL Server", "extra": ""},
    {"name": "SQL Server Native Client 11.0", "extra": ""},
    {"name": "SQL Server Native Client 10.0", "extra": ""},
    {"name": "SQL Server",                    "extra": ""}
]


def get_machine_name() -> str:
    """Retorna el nombre del equipo local en mayúsculas."""
    import socket
    return_val = os.environ.get("COMPUTERNAME") or socket.gethostname() or "LOCALHOST"
    return return_val.strip().upper()


def get_machine_cached_odbc_driver(ini_path: str, machine_name: str) -> Optional[str]:
    """Lee asientos.ini y retorna el driver ODBC asignado al equipo si existe."""
    if not ini_path or not os.path.exists(ini_path):
        return None
    try:
        import configparser
        cp = configparser.ConfigParser()
        cp.read(ini_path, encoding="utf-8")
        for sec in ("equipos", "drivers", "DEFAULT"):
            if cp.has_section(sec) and cp.has_option(sec, machine_name):
                val = cp.get(sec, machine_name).strip()
                if val:
                    return val
    except Exception as e:
        logging.warning(f"[asisdb] Error leyendo driver de {ini_path}: {e}")
    return None


def save_machine_cached_odbc_driver(ini_path: str, machine_name: str, driver_name: str) -> bool:
    """Registra en asientos.ini el driver ODBC para el equipo en la sección [equipos]."""
    if not ini_path or not driver_name:
        return False
    try:
        import configparser
        cp = configparser.ConfigParser()
        if os.path.exists(ini_path):
            cp.read(ini_path, encoding="utf-8")
        if not cp.has_section("equipos"):
            cp.add_section("equipos")
        cp.set("equipos", machine_name, driver_name)
        with open(ini_path, "w", encoding="utf-8") as f:
            cp.write(f)
        return True
    except Exception as e:
        logging.warning(f"[asisdb] Error guardando driver en {ini_path}: {e}")
        return False


def get_best_mssql_odbc_driver(installed_drivers: Optional[List[str]] = None) -> Tuple[Optional[str], str]:
    """Recorre la lista ordenada MSSQL_ODBC_DRIVERS_PRIORITY y retorna el primer driver disponible."""
    if installed_drivers is None:
        try:
            import pyodbc
            installed_drivers = pyodbc.drivers()
        except Exception:
            installed_drivers = []

    installed_map = {d.strip().lower(): d.strip() for d in installed_drivers}

    for item in MSSQL_ODBC_DRIVERS_PRIORITY:
        driver_key = item["name"].strip().lower()
        if driver_key in installed_map:
            return installed_map[driver_key], item["extra"]

    return None, ""


def resolve_odbc_driver_for_machine(
    ini_path: Optional[str] = None,
    machine_name: Optional[str] = None,
    preferred_driver: Optional[str] = None,
    installed_drivers: Optional[List[str]] = None
) -> Tuple[Optional[str], str]:
    """
    Resuelve el driver ODBC para el equipo:
    1. Si preferred_driver está provisto, lo busca en MSSQL_ODBC_DRIVERS_PRIORITY.
    2. Si existe asientos.ini y la máquina está registrada, toma ese driver.
    3. Si no, autodetecta recorriendo la lista MSSQL_ODBC_DRIVERS_PRIORITY y guarda en asientos.ini.
    """
    m_name = (machine_name or get_machine_name()).upper().strip()

    if preferred_driver:
        for item in MSSQL_ODBC_DRIVERS_PRIORITY:
            if item["name"].lower() == preferred_driver.lower():
                return item["name"], item["extra"]
        return preferred_driver, ""

    if ini_path:
        cached = get_machine_cached_odbc_driver(ini_path, m_name)
        if cached:
            for item in MSSQL_ODBC_DRIVERS_PRIORITY:
                if item["name"].lower() == cached.lower():
                    return item["name"], item["extra"]
            return cached, ""

    best_driver, extra = get_best_mssql_odbc_driver(installed_drivers=installed_drivers)
    if best_driver and ini_path:
        save_machine_cached_odbc_driver(ini_path, m_name, best_driver)

    return best_driver, extra


def _format_mssql_target_url(user_pass: str, host: str, port: str, database_name: str) -> str:
    """Format/sanitize host string for MSSQL pymssql connections."""
    clean_host = host.strip().lstrip('\\').lstrip('/')
    clean_host = clean_host.replace('/', '\\')
    if '\\' in clean_host:
        if port:
            server_only = clean_host.split('\\')[0]
            return f"mssql+pymssql://{user_pass}{server_only}:{port}/{database_name}"
        else:
            encoded_host = urllib.parse.quote(clean_host)
            return f"mssql+pymssql://{user_pass}{encoded_host}/{database_name}"
    else:
        port_str = f":{port}" if port else ""
        return f"mssql+pymssql://{user_pass}{clean_host}{port_str}/{database_name}"


def _build_auth_segment(user: str, password_obj: Union[EncryptedPassword, str, None]) -> str:
    """
    Construye el segmento de autenticación 'user:password@' para URLs de conexión.
    El texto plano de la contraseña se descifra estrictamente dentro del marco local
    de esta función y es descartado inmediatamente tras la concatenación.
    """
    if not user and not password_obj:
        return ""
    quoted_user = urllib.parse.quote_plus(user) if user else ""
    raw_pwd = decrypt_password(password_obj) if password_obj else ""
    quoted_password = urllib.parse.quote_plus(raw_pwd) if raw_pwd else ""
    return f"{quoted_user}:{quoted_password}@" if (quoted_user or quoted_password) else ""


def _mask_url_password(url: str, password_obj: Union[EncryptedPassword, str, None]) -> str:
    """
    Enmascara la contraseña en una URL o cadena de conexión para diagnósticos y logs seguros.
    """
    if not url or not password_obj:
        return url
    plain = decrypt_password(password_obj) if password_obj else ""
    if not plain:
        return url
    masked = url.replace(plain, "<password>")
    quoted = urllib.parse.quote_plus(plain)
    if quoted != plain:
        masked = masked.replace(quoted, "<password>")
    return masked


def build_db_url(

    config: Union[ConnectionConfig, Dict[str, Any]],
    last_resource: bool = False
) -> str:
    """
    Construye la URL de conexión a la Base de Datos desde un ConnectionConfig
    o diccionario con claves canónicas exactas, interpolando comodines si aplica.
    """
    params = config if isinstance(config, ConnectionConfig) else ConnectionConfig.from_dict(config)

    explicit_url = params.explicit_url
    driver = params.driver.strip().lower()
    host = params.host
    port = params.port
    database_name = params.database
    user = params.user

    sql_driver_autodetect = params.sql_driver_autodetect.strip().lower() == "true"
    tds_version = params.tds_version
    odbc_driver = params.odbc_driver
    ini_path = params.ini_path

    # Limpiar campos inhabilitados con '*' o '#'
    if odbc_driver.startswith(("*", "#")):
        odbc_driver = ""
    if tds_version.startswith(("*", "#")):
        tds_version = ""

    # Contexto para interpolación genérica (mantiene EncryptedPassword sin exponer texto plano)
    context_params = {
        "driver": driver,
        "host": host,
        "port": port,
        "database": database_name,
        "user": user,
        "password": params.password,
    }
    database_name = interpolate_placeholders(database_name, context_params)

    clean_url = explicit_url.strip() if explicit_url else ""
    if clean_url and not clean_url.startswith(("*", "#")):
        final_url = interpolate_db_url_placeholders(clean_url, context_params)
    else:
        effective_db = database_name

        if driver == "sqlite":
            db_path = effective_db if effective_db.endswith(".db") else f"{effective_db}.db"
            final_url = f"sqlite:///{db_path}"
        elif driver == "mssql" or driver in ("odbc", "pyodbc"):
            if sql_driver_autodetect or driver in ("odbc", "pyodbc"):
                detected_driver, extra_params = resolve_odbc_driver_for_machine(
                    ini_path=ini_path,
                    preferred_driver=odbc_driver if odbc_driver else None
                )
                if detected_driver:
                    clean_h = host.strip().lstrip('\\').lstrip('/')
                    clean_h = clean_h.replace('/', '\\')
                    server_name = clean_h.split('\\')[0]
                    if port:
                        server_part = f"{server_name},{port}"
                    else:
                        server_part = clean_h

                    odbc_conn_str = f"DRIVER={{{detected_driver}}};SERVER={server_part};DATABASE={effective_db};UID={user};PWD={decrypt_password(params.password)};"
                    if extra_params:
                        odbc_conn_str = f"{odbc_conn_str}{extra_params}"
                    quoted_odbc = urllib.parse.quote_plus(odbc_conn_str)
                    final_url = f"mssql+pyodbc:///?odbc_connect={quoted_odbc}"
                else:
                    # Fallback a pymssql si no se detectó ningún driver ODBC
                    user_pass = _build_auth_segment(user, params.password)
                    final_url = _format_mssql_target_url(user_pass, host, port, effective_db)
                    if tds_version:
                        sep = "&" if "?" in final_url else "?"
                        final_url = f"{final_url}{sep}tds_version={tds_version}"
            else:
                # Comportamiento estándar con pymssql
                user_pass = _build_auth_segment(user, params.password)
                final_url = _format_mssql_target_url(user_pass, host, port, effective_db)
                if tds_version:
                    sep = "&" if "?" in final_url else "?"
                    final_url = f"{final_url}{sep}tds_version={tds_version}"
        else:
            user_pass = _build_auth_segment(user, params.password)
            port_str = f":{port}" if port else ""

            if driver == "postgresql":
                final_url = f"postgresql+psycopg2://{user_pass}{host}{port_str}/{effective_db}"
            elif driver == "mysql":
                final_url = f"mysql+pymysql://{user_pass}{host}{port_str}/{effective_db}"
            else:
                final_url = f"{driver}://{user_pass}{host}{port_str}/{effective_db}"

    if last_resource:
        import socket
        logging.info("[LAST_RESOURCE] [asisdb] Diagnóstico de red y resolución:")
        clean_h = host.split('\\')[0].split('/')[0].strip()
        if clean_h:
            try:
                resolved_ip = socket.gethostbyname(clean_h)
                logging.info(f"[LAST_RESOURCE] [asisdb.DNS] Host '{clean_h}' resuelto exitosamente a IP: {resolved_ip}")
            except Exception as dns_err:
                logging.warning(f"[LAST_RESOURCE] [asisdb.DNS] No se pudo resolver host '{clean_h}': {dns_err}")

            if port:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3.0)
                    s.connect((clean_h, int(port)))
                    s.close()
                    logging.info(f"[LAST_RESOURCE] [asisdb.SOCKET_TCP] Socket hacia '{clean_h}:{port}' CONECTADO OK.")
                except Exception as sock_err:
                    logging.warning(f"[LAST_RESOURCE] [asisdb.SOCKET_TCP] Socket hacia '{clean_h}:{port}' FALLÓ: {sock_err}")

        logging.info(f"[LAST_RESOURCE] [asisdb] Autodetect: {sql_driver_autodetect} | TDS: '{tds_version}' | INI: '{ini_path}'")
        logging.info(f"[LAST_RESOURCE] [asisdb] URL final construida para Engine: {_mask_url_password(final_url, params.password)}")

    return final_url


def get_db_engine(
    db_url: Optional[str] = None,
    config: Optional[Union[ConnectionConfig, Dict[str, Any]]] = None,
    key: Optional[str] = None
) -> Engine:
    """
    Retorna una instancia de motor SQLAlchemy Core.
    Soporta un motor Singleton por defecto o múltiples motores indexados mediante 'key'.
    """
    global _ENGINE, _ENGINES
    if key is not None:
        cache_key = key.strip()
        if cache_key in _ENGINES:
            return _ENGINES[cache_key]

        target_url = db_url
        if target_url is None:
            if config is not None:
                target_url = build_db_url(config)
            else:
                raise ValueError(
                    t18n(
                        "db.no_config_error",
                        "[asisdb] Se debe proporcionar 'db_url' o 'config' para inicializar el motor de base de datos."
                    )
                )

        connect_args = {}
        if "sqlite" in target_url:
            connect_args = {"check_same_thread": False}

        eng = create_engine(target_url, connect_args=connect_args, pool_pre_ping=True)
        _ENGINES[cache_key] = eng
        return eng

    if _ENGINE is None:
        target_url = db_url
        if target_url is None:
            if config is not None:
                target_url = build_db_url(config)
            else:
                raise ValueError(
                    t18n(
                        "db.no_config_error",
                        "[asisdb] Se debe proporcionar 'db_url' o 'config' para inicializar el motor de base de datos."
                    )
                )

        connect_args = {}
        if "sqlite" in target_url:
            connect_args = {"check_same_thread": False}

        _ENGINE = create_engine(target_url, connect_args=connect_args, pool_pre_ping=True)
        logging.info(
            t18n(
                "db.engine_created",
                "[TRANSFER] Motor de Base de Datos inicializado exitosamente para {url}",
                url=target_url.split("@")[-1] if "@" in target_url else target_url
            )
        )
    return _ENGINE


def verify_db_structure(
    eng: Optional[Engine] = None,
    metadata: Optional[MetaData] = None,
    parametro: int = 0
) -> Dict[str, Any]:
    """
    Verifica e inspecciona la estructura relacional de la base de datos comparándola con MetaData,
    retornando un diccionario con el informe detallado del diagnóstico.
    
    :param eng: Instancia de Engine. Si es None, utiliza get_db_engine().
    :param metadata: MetaData de las tablas relacionales.
    :param parametro: Nivel de verificación diagnóstica (0 por defecto).
        - 0: Agrega columnas faltantes automáticamente mediante ALTER TABLE.
        - >= 1: Agrega columnas faltantes y notifica anomalías simples (ej. tablas faltantes).
        - >= 2: Notifica discrepancias de características (tipo/longitud/anulabilidad) en columnas existentes.
        - >= 3: Comparación inversa: notifica columnas sobrantes/huérfanas en la BD física.
    :return: Diccionario con el informe relacional de la verificación.
    """
    report: Dict[str, Any] = {
        "ok": True,
        "migrated_columns": [],
        "missing_tables": [],
        "mismatched_columns": [],
        "surplus_columns": []
    }

    engine_obj = eng or get_db_engine()
    if metadata is None:
        return report

    try:
        from sqlalchemy import inspect, text
        insp = inspect(engine_obj)
        existing_tables = set(insp.get_table_names())
        
        with engine_obj.begin() as conn:
            for table_name, table in metadata.tables.items():
                if table_name in existing_tables:
                    db_cols = {c["name"].lower(): c for c in insp.get_columns(table_name)}
                    existing_col_names = set(db_cols.keys())

                    for col in table.columns:
                        col_name_lower = col.name.lower()
                        if col_name_lower not in existing_col_names:
                            col_type = col.type.compile(engine_obj.dialect)
                            nullable_str = "NULL" if col.nullable else "NOT NULL DEFAULT '01'"
                            sql_str = f"ALTER TABLE {table_name} ADD {col.name} {col_type} {nullable_str}"
                            logging.info(
                                t18n("db.column_migrated", "[asisdb] Migrando columna faltante '{col}' en '{table}'", col=col.name, table=table_name)
                            )
                            conn.execute(text(sql_str))
                            report["migrated_columns"].append({"table": table_name, "column": col.name})
                        else:
                            if parametro >= 2:
                                db_col = db_cols[col_name_lower]
                                db_type_raw = str(db_col.get("type", "")).upper()
                                db_type_clean = db_type_raw.split("COLLATE")[0].strip()
                                model_type_raw = col.type.compile(engine_obj.dialect).upper()
                                model_type_clean = model_type_raw.split("COLLATE")[0].strip()
                                db_null = db_col.get("nullable", True)
                                model_null = col.nullable

                                # Normalizar equivalencias como VARCHAR -> VARCHAR(MAX) o TEXT en SQL Server
                                if db_type_clean != model_type_clean or db_null != model_null:
                                    # Evitar notificar como error diferencias cosméticas entre Text/VARCHAR(MAX)
                                    if not ({"VARCHAR", "VARCHAR(MAX)", "TEXT"}.issuperset({db_type_clean, model_type_clean})):
                                        report["ok"] = False
                                        mismatch_info = {
                                            "table": table_name,
                                            "column": col.name,
                                            "db_type": db_type_raw,
                                            "model_type": model_type_raw,
                                            "db_nullable": db_null,
                                            "model_nullable": model_null
                                        }
                                        report["mismatched_columns"].append(mismatch_info)
                                        logging.info(
                                            t18n(
                                                "db.column_mismatch",
                                                "[asisdb] Discrepancia en columna '{col}' ('{table}'): DB=[{db_type}, Null:{db_null}], Modelo=[{model_type}, Null:{model_null}]",
                                                col=col.name, table=table_name,
                                                db_type=db_type_raw, db_null=db_null,
                                                model_type=model_type_raw, model_null=model_null
                                            )
                                        )

                    if parametro >= 3:
                        model_col_names = {col.name.lower() for col in table.columns}
                        surplus_cols = existing_col_names - model_col_names
                        for extra_col in surplus_cols:
                            report["surplus_columns"].append({"table": table_name, "column": extra_col})
                            logging.info(
                                t18n(
                                    "db.surplus_column_found",
                                    "[asisdb] Columna sobrante/huérfana '{col}' detectada en la tabla '{table}' de la base de datos.",
                                    col=extra_col, table=table_name
                                )
                            )
                else:
                    report["ok"] = False
                    report["missing_tables"].append(table_name)
                    if parametro >= 1:
                        logging.info(
                            t18n(
                                "db.table_not_found",
                                "[asisdb] Tabla esperada '{table}' no existe en la base de datos.",
                                table=table_name
                            )
                        )
    except Exception as e:
        logging.warning(
            t18n("db.column_migration_warning", "[asisdb] Advertencia al verificar/migrar estructura de base de datos: {err}", err=str(e))
        )

    return report


def init_db(
    engine: Optional[Engine] = None,
    metadata: Optional[MetaData] = None,
    parametro: int = 0
) -> Dict[str, Any]:
    """Crea todas las tablas definidas en los metadatos si no existen y verifica/migra su estructura."""
    global _ENGINE
    eng = engine or get_db_engine()

    if metadata is None:
        logging.warning(
            t18n(
                "db.no_metadata_error",
                "[asisdb] No se proporcionaron los metadatos de las tablas (MetaData) para la inicialización."
            )
        )
        return {"ok": False, "error": "No MetaData provided"}

    try:
        metadata.create_all(eng)
        report = verify_db_structure(eng, metadata, parametro=parametro)
        logging.info(
            t18n(
                "db.tables_created",
                "[APPLICATION] Tablas locales verificadas/creadas exitosamente."
            )
        )
        return report
    except Exception as e:
        logging.warning(
            t18n(
                "db.connect_fallback",
                "[TRANSFER] No se pudo conectar al motor DB configurado ({err}). Aplicando fallback a SQLite local ('sqlite:///middleware_local.db').",
                err=str(e)
            )
        )
        _ENGINE = create_engine("sqlite:///middleware_local.db", connect_args={"check_same_thread": False})
        metadata.create_all(_ENGINE)
        report = verify_db_structure(_ENGINE, metadata, parametro=parametro)
        logging.info(
            t18n(
                "db.sqlite_initialized",
                "[APPLICATION] Tablas locales verificadas/creadas en SQLite de respaldo."
            )
        )
        return report


def reset_engine() -> None:
    """Resetea todos los motores en caché (Singleton y pool indexado)."""
    global _ENGINE, _ENGINES
    if _ENGINE:
        _ENGINE.dispose()
        _ENGINE = None
    for eng in _ENGINES.values():
        try:
            eng.dispose()
        except Exception:
            pass
    _ENGINES.clear()
    clear_all_security_sessions()


def close_engine(engine: Optional[Engine] = None, key: Optional[str] = None) -> None:
    """Cierra y libera los recursos del motor especificado, clave o motor Singleton activo."""
    global _ENGINE, _ENGINES
    if key is not None and key in _ENGINES:
        eng = _ENGINES.pop(key)
        eng.dispose()
        logging.info(t18n("db.engine_closed", "[asisdb] Motor de base de datos cerrado y recursos liberados."))
        return

    eng = engine or _ENGINE
    if eng:
        eng.dispose()
        if eng == _ENGINE:
            _ENGINE = None
        for k, v in list(_ENGINES.items()):
            if v == eng:
                _ENGINES.pop(k, None)
        logging.info(t18n("db.engine_closed", "[asisdb] Motor de base de datos cerrado y recursos liberados."))


def execute_query(statement: Any, params: Optional[Dict[str, Any]] = None, engine: Optional[Engine] = None) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta SQL genérica (SELECT) o sentencia ejecutable y retorna los resultados como diccionarios.
    Acepta tanto sentencias SQLAlchemy como strings SQL puros con parámetros.
    """
    eng = engine or get_db_engine()
    stmt = text(statement) if isinstance(statement, str) else statement
    with eng.connect() as conn:
        result = conn.execute(stmt, params or {})
        return [dict(row) for row in result.mappings().all()]


def execute_statement(statement: Any, params: Optional[Dict[str, Any]] = None, engine: Optional[Engine] = None) -> Any:
    """
    Ejecuta un comando o sentencia SQL de modificación (INSERT, UPDATE, DELETE, DDL) en una transacción auto-commit.
    Acepta tanto sentencias SQLAlchemy como strings SQL puros con parámetros.
    Retorna la clave primaria insertada o el número de filas afectadas.
    """
    eng = engine or get_db_engine()
    stmt = text(statement) if isinstance(statement, str) else statement
    with eng.begin() as conn:
        result = conn.execute(stmt, params or {})
        try:
            if getattr(result, "is_insert", False) and result.inserted_primary_key:
                return result.inserted_primary_key[0]
        except Exception:
            pass
        return result.rowcount


def LITERAL(val: Any) -> Dict[str, Any]:
    """Helper para definir un valor constante/literal en el mapping de un test de conexión."""
    return {"literal": val}


def test_connection(
    driver: str = "",
    host: str = "",
    port: str = "",
    database: str = "",
    user: str = "",
    password: Union[str, EncryptedPassword] = "",
    explicit_url: str = "",
    path: str = "",
    sql_driver_autodetect: str = "",
    tds_version: str = "",
    odbc_driver: str = "",
    ini_path: str = "",
    encrypted_fields: Optional[Sequence[str]] = None,
    **kwargs
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Punto de entrada único universal para probar cualquier tipo de conexión (FoxPro o Motores BD).
    El parámetro 'driver' es OBLIGATORIO y explícito (cero heurísticas/asunciones).
    
    Retorna:
        Tuple[bool, str, Dict[str, Any]]:
        - éxito (bool)
        - mensaje (str)
        - diagnóstico (dict con 'used_params', 'unused_params', 'target_url')
    """
    password = encrypt_password(password)
    raw_params = {
        "driver": driver,
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
        "explicit_url": explicit_url,
        "path": path,
        "sql_driver_autodetect": sql_driver_autodetect,
        "tds_version": tds_version,
        "odbc_driver": odbc_driver,
        "ini_path": ini_path,
        **kwargs
    }
    #print("asisdb/engine.py raw_params:")
    #print(raw_params)
    clean_driver = driver.strip().lower()
    if not clean_driver:
        return False, "Error: Debe especificar un 'driver' o motor de base de datos válido.", {
            "used_params": {},
            "unused_params": list(raw_params.keys()),
            "target_url": ""
        }

    clean_path = interpolate_placeholders(path.strip(), raw_params)
    clean_host = interpolate_placeholders(host.strip(), raw_params)
    clean_db = interpolate_placeholders(database.strip(), raw_params)
    clean_user = interpolate_placeholders(user.strip(), raw_params)
    clean_explicit_url = interpolate_placeholders(explicit_url.strip(), raw_params)

    if clean_path: raw_params["path"] = clean_path
    if clean_host: raw_params["host"] = clean_host
    if clean_db: raw_params["database"] = clean_db
    if clean_user: raw_params["user"] = clean_user
    if clean_explicit_url: raw_params["explicit_url"] = clean_explicit_url

    # Conjunto canónico de campos a enmascarar (password siempre protegido por contrato)
    to_mask = {"password"}
    if encrypted_fields:
        to_mask.update(f.strip() for f in encrypted_fields if isinstance(f, str))

    used_params: Dict[str, Any] = {}
    unused_params: list = []

    # Clasificar parámetros con valor vs vacíos sin heurísticas mágicas
    for k, v in raw_params.items():
        if v is not None and str(v).strip() != "" and v is not False:
            if k in to_mask or isinstance(v, EncryptedPassword):
                used_params[k] = f"<{k}>"
            else:
                used_params[k] = v
        else:
            unused_params.append(k)

    # 1. Validación de FoxPro / DBF
    if clean_driver in ("foxpro", "vfp", "dbf"):
        target_dir = (clean_path or clean_host or "").strip()
        if not target_dir:
            return False, "Error: La ruta del directorio de tablas FoxPro ('path' o 'host') está vacía.", {
                "used_params": used_params,
                "unused_params": unused_params,
                "target_url": ""
            }
        
        abs_host = os.path.abspath(target_dir)
        masked_target = abs_host

        if not os.path.exists(abs_host):
            return False, f"La ruta de tablas FoxPro '{abs_host}' no existe o no es accesible.", {
                "used_params": used_params,
                "unused_params": unused_params,
                "target_url": masked_target
            }
        if not os.path.isdir(abs_host):
            return False, f"La ruta '{abs_host}' no es un directorio válido.", {
                "used_params": used_params,
                "unused_params": unused_params,
                "target_url": masked_target
            }
        try:
            verified_samples = []
            for root, dirs, files in os.walk(abs_host):
                rel_p = os.path.relpath(root, abs_host)
                depth = 0 if rel_p == "." else len(rel_p.split(os.sep))
                if depth > 2:
                    dirs.clear()
                    continue

                for f in files:
                    if f.lower().endswith('.dbf'):
                        full_p = os.path.join(root, f)
                        try:
                            with open(full_p, 'rb') as f_dbf:
                                hdr = f_dbf.read(32)
                                if len(hdr) >= 32:
                                    verified_samples.append(os.path.relpath(full_p, abs_host))
                        except Exception:
                            pass
                        if len(verified_samples) >= 2:
                            break
                if len(verified_samples) >= 2:
                    break

            if not verified_samples:
                msg = f"Directorio FoxPro '{abs_host}' accesible (Nota: no se detectaron tablas .DBF en la muestra de lectura)."
            else:
                samples_str = ", ".join(verified_samples)
                msg = f"Conexión exitosa a FoxPro '{abs_host}': Lectura verificada correctamente en muestra ({samples_str})."

            return True, msg, {
                "used_params": used_params,
                "unused_params": unused_params,
                "target_url": masked_target
            }
        except Exception as e:
            return False, f"Error al acceder a la ruta FoxPro '{abs_host}': {str(e)}", {
                "used_params": used_params,
                "unused_params": unused_params,
                "target_url": masked_target
            }

    # 2. Validación de Motores SQL Relacionales (MSSQL, SQLite, PostgreSQL, MySQL, etc.)
    try:
        conn_config = ConnectionConfig(
            driver=clean_driver,
            host=clean_host,
            port=port,
            database=clean_db,
            user=clean_user,
            password=password,
            explicit_url=clean_explicit_url,
            sql_driver_autodetect=sql_driver_autodetect,
            tds_version=tds_version,
            odbc_driver=odbc_driver,
            ini_path=ini_path
        )
        target_url = build_db_url(conn_config)

        # Enmascarar contraseñas en target_url para diagnóstico
        masked_url = _mask_url_password(target_url, password)

        connect_args = {}
        if "sqlite" in target_url:
            connect_args = {"check_same_thread": False}

        test_engine = create_engine(target_url, connect_args=connect_args, pool_pre_ping=True)
        with test_engine.connect() as conn:
            pass
        test_engine.dispose()

        effective_db = clean_db

        return True, f"Conexión exitosa al motor [{clean_driver}] en {clean_host or 'local'}/{effective_db}.", {
            "used_params": used_params,
            "unused_params": unused_params,
            "target_url": masked_url
        }
    except Exception as e:
        # En caso de error, generar URL enmascarada si es posible
        try:
            target_url = build_db_url(conn_config)
            masked_url = _mask_url_password(target_url, password)
        except Exception:
            masked_url = f"{clean_driver}://{clean_host}/{clean_db}"

        return False, f"Error al conectar a la base de datos [{clean_driver}]: {str(e)}", {
            "used_params": used_params,
            "unused_params": unused_params,
            "target_url": masked_url
        }


def test_db_connection(params: Union[ConnectionConfig, Dict[str, Any]]) -> Tuple[bool, str]:
    """Prueba la conexión a partir de un ConnectionConfig o diccionario de parámetros canónicos."""
    if isinstance(params, ConnectionConfig):
        cfg_dict = {
            "driver": params.driver,
            "host": params.host,
            "port": params.port,
            "database": params.database,
            "user": params.user,
            "password": params.password,
            "explicit_url": params.explicit_url,
            "sql_driver_autodetect": params.sql_driver_autodetect,
            "tds_version": params.tds_version,
            "odbc_driver": params.odbc_driver,
            "ini_path": params.ini_path,
        }
    else:
        cfg_dict = params
    success, msg, _ = test_connection(**cfg_dict)
    return success, msg

def get_supported_drivers() -> list:
    """Retorna la lista de tipos de conexiones / drivers de Base de Datos soportados por asisdb."""
    return list(SUPPORTED_DRIVERS)

