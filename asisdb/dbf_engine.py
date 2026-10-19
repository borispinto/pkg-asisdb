# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 ASISNET Computación, CA <proyectos@asisnet.net>
# SPDX-FileCopyrightText: 2026 Boris Pinto <borispinto@gmail.com>
# SPDX-License-Identifier: MIT
# Autor: Boris Pinto <borispinto@gmail.com>
# Contacto Institucional: ASISNET Computación, CA <proyectos@asisnet.net>
# File: asisdb/dbf_engine.py

"""
Módulo dbf_engine (asisdb): Motor de Acceso y Consulta Optimizado para Tablas DBF (FoxPro / dBase).

Proporciona:
- DBFReader: Consultas directas unitarias (find_one) y masivas (find_all) con soporte de
  lectura inversa (reverse streaming por byte-offset de registros fijos).
- DBFCacheManager: Gestor de caché en memoria para tablas maestras y catálogos (Clientes, Productos, etc.)
  con acceso O(1) en microsegundos.
- Compatibilidad universal con cualquier tabla .DBF (Ventas, Compras, Contabilidad, Nómina, etc.).
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable

try:
    from dbfread import DBF
    DBF_AVAILABLE = True
except ImportError:
    DBF = None  # type: ignore
    DBF_AVAILABLE = False


class DBFReader:
    """
    Motor universal de lectura para archivos .DBF (FoxPro 2.x, Visual FoxPro, dBase).
    """

    @staticmethod
    def is_available() -> bool:
        """Indica si la librería subyacente 'dbfread' está instalada y disponible."""
        return DBF_AVAILABLE

    @staticmethod
    def find_one(
        file_path: str,
        match_fn: Callable[[Dict[str, Any]], bool],
        reverse: bool = False,
        encoding: str = "latin-1"
    ) -> Optional[Dict[str, Any]]:
        """
        Busca y retorna el primer registro del archivo DBF que cumpla match_fn.
        
        Si reverse=True, recorre el archivo desde el último registro hacia el primero mediante
        acceso directo por byte offset (óptimo para transacciones y movimientos recientes).
        Detiene la lectura inmediatamente al encontrar la primera coincidencia (detención temprana).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo DBF requerido no existe en disco: {file_path}")
        if not DBF_AVAILABLE or DBF is None:
            raise ImportError("La librería 'dbfread' no está disponible para leer archivos DBF.")

        try:
            table: Any = DBF(file_path, encoding=encoding, ignore_missing_memofile=True, lowernames=True, load=False)

            if not reverse:
                for record in table:
                    rec_dict = dict(record)
                    if match_fn(rec_dict):
                        return rec_dict
                return None

            # Lectura Inversa Directa por Byte Offset
            header: Any = getattr(table, "header", None)
            if header is None or getattr(header, "numrecords", 0) == 0:
                return None

            num_records: int = int(header.numrecords)
            header_len: int = int(header.headerlen)
            record_len: int = int(header.recordlen)

            with open(file_path, "rb") as infile, table._open_memofile() as memofile:
                field_parser = table.parserclass(table, memofile)
                parse = field_parser.parse
                fields = table.fields

                for i in range(num_records - 1, -1, -1):
                    infile.seek(header_len + (i * record_len))
                    sep = infile.read(1)
                    if sep == b" ":  # Registro válido (no eliminado)
                        items = [(f.name.lower(), parse(f, infile.read(f.length))) for f in fields]
                        rec_dict = dict(items)
                        if match_fn(rec_dict):
                            return rec_dict
            return None
        except Exception as e:
            raise RuntimeError(f"Error al leer el archivo DBF '{file_path}': {str(e)}")

    @staticmethod
    def find_all(
        file_path: str,
        match_fn: Callable[[Dict[str, Any]], bool],
        reverse: bool = False,
        encoding: str = "latin-1"
    ) -> List[Dict[str, Any]]:
        """
        Filtra y retorna todos los registros del archivo DBF que cumplan match_fn.
        Si reverse=True, lee en streaming inverso y preserva el orden cronológico original de las filas.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo DBF requerido no existe en disco: {file_path}")
        if not DBF_AVAILABLE or DBF is None:
            raise ImportError("La librería 'dbfread' no está disponible para leer archivos DBF.")

        try:
            table: Any = DBF(file_path, encoding=encoding, ignore_missing_memofile=True, lowernames=True, load=False)

            if not reverse:
                matches = []
                for record in table:
                    rec_dict = dict(record)
                    if match_fn(rec_dict):
                        matches.append(rec_dict)
                return matches

            header: Any = getattr(table, "header", None)
            if header is None or getattr(header, "numrecords", 0) == 0:
                return []

            num_records: int = int(header.numrecords)
            header_len: int = int(header.headerlen)
            record_len: int = int(header.recordlen)
            matches = []

            with open(file_path, "rb") as infile, table._open_memofile() as memofile:
                field_parser = table.parserclass(table, memofile)
                parse = field_parser.parse
                fields = table.fields

                for i in range(num_records - 1, -1, -1):
                    infile.seek(header_len + (i * record_len))
                    sep = infile.read(1)
                    if sep == b" ":
                        items = [(f.name.lower(), parse(f, infile.read(f.length))) for f in fields]
                        rec_dict = dict(items)
                        if match_fn(rec_dict):
                            matches.append(rec_dict)

            # Invertir para preservar el orden secuencial original (1, 2, 3...)
            matches.reverse()
            return matches
        except Exception as e:
            raise RuntimeError(f"Error al leer el archivo DBF '{file_path}': {str(e)}")

    @staticmethod
    def count_records(file_path: str) -> int:
        """Retorna la cantidad total de registros almacenados en el encabezado del DBF."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo DBF no existe: {file_path}")
        with open(file_path, "rb") as f:
            header = f.read(32)
            if len(header) < 32:
                return 0
            return int.from_bytes(header[4:8], byteorder="little")


class DBFCacheManager:
    """
    Gestor de caché en memoria para tablas maestras y catálogos de FoxPro.
    Permite acceso O(1) instantáneo en microsegundos evitando lecturas repetitivas a disco.
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _build_key(self, file_path: str, key: str) -> str:
        norm_path = os.path.abspath(file_path).lower()
        return f"{norm_path}::{str(key).strip().upper()}"

    def get(self, file_path: str, key: str) -> Optional[Dict[str, Any]]:
        """Obtiene un registro de la caché si existe."""
        cache_key = self._build_key(file_path, key)
        return self._cache.get(cache_key)

    def set(self, file_path: str, key: str, record: Dict[str, Any]) -> None:
        """Almacena un registro en la caché."""
        cache_key = self._build_key(file_path, key)
        self._cache[cache_key] = record

    def get_or_fetch(
        self,
        file_path: str,
        key: str,
        match_fn: Callable[[Dict[str, Any]], bool],
        reverse: bool = False,
        encoding: str = "latin-1"
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna el registro desde la caché si existe; si no, lo busca en el DBF,
        lo indexa en memoria y lo retorna.
        """
        cached = self.get(file_path, key)
        if cached is not None:
            return cached

        record = DBFReader.find_one(file_path, match_fn=match_fn, reverse=reverse, encoding=encoding)
        if record is not None:
            self.set(file_path, key, record)
        return record

    def clear(self, file_path: Optional[str] = None) -> None:
        """Limpia la caché completa o solo las entradas correspondientes a un archivo DBF específico."""
        if file_path is None:
            self._cache.clear()
        else:
            norm_prefix = f"{os.path.abspath(file_path).lower()}::"
            keys_to_del = [k for k in self._cache.keys() if k.startswith(norm_prefix)]
            for k in keys_to_del:
                del self._cache[k]


# Instancia Singleton de Caché para reutilización global en el proceso
_GLOBAL_DBF_CACHE = DBFCacheManager()


def get_dbf_cache() -> DBFCacheManager:
    """Retorna la instancia global del gestor de caché DBF."""
    return _GLOBAL_DBF_CACHE
