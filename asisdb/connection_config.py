# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 ASISNET Computación, CA <proyectos@asisnet.net>
# SPDX-FileCopyrightText: 2026 Boris Pinto <borispinto@gmail.com>
# SPDX-License-Identifier: MIT
# Autor: Boris Pinto <borispinto@gmail.com>
# Contacto Institucional: ASISNET Computación, CA <proyectos@asisnet.net>
# File: asisdb/connection_config.py

"""
Módulo de Configuración Canónica de Conexión para asisdb.
Define el contrato de datos estricto (ConnectionConfig) para instanciación
de motores y construcción de URLs sin dependencias externas ni sinónimos.
"""

from dataclasses import dataclass, fields
from typing import Any, Dict, Optional, Union
from .security import EncryptedPassword, encrypt_password


@dataclass
class ConnectionConfig:
    explicit_url: str = ""
    driver: str = ""
    host: str = ""
    port: str = ""
    database: str = ""
    user: str = ""
    password: Union[str, EncryptedPassword] = ""
    odbc_driver: str = ""
    tds_version: str = ""
    sql_driver_autodetect: str = ""
    ini_path: str = ""

    def __post_init__(self) -> None:
        self.password = encrypt_password(self.password)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> "ConnectionConfig":
        """
        Instancia ConnectionConfig poblando sus atributos exclusivamente
        con las claves canónicas exactas presentes en el diccionario.
        """
        instance = cls()
        if not data or not isinstance(data, dict):
            return instance

        valid_fields = {f.name for f in fields(cls)}

        for key, value in data.items():
            if key in valid_fields and value is not None:
                #TODO: no puede ser harcodeado
                if key == "password":
                    setattr(instance, key, encrypt_password(value))
                else:
                    setattr(instance, key, str(value).strip())

        return instance

