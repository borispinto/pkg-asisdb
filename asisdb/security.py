# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 ASISNET Computación, CA <proyectos@asisnet.net>
# SPDX-FileCopyrightText: 2026 Boris Pinto <borispinto@gmail.com>
# SPDX-License-Identifier: MIT
# Autor: Boris Pinto <borispinto@gmail.com>
# Contacto Institucional: ASISNET Computación, CA <proyectos@asisnet.net>
# File: asisdb/security.py

"""
Módulo de Seguridad y Cifrado Dinámico de Credenciales para asisdb.
Proporciona el objeto EncryptedPassword y funciones para proteger contraseñas
en memoria mediante claves de sesión efímeras y cifrado de flujo con la biblioteca estándar.
"""

from dataclasses import dataclass
import hashlib
import secrets
from typing import Dict, Optional, Union


# Almacén de claves dinámicas por sesión en memoria
_SESSION_KEYS: Dict[str, bytes] = {}


def _generate_keystream(key: bytes, salt: bytes, length: int) -> bytes:
    """
    Genera un flujo de bytes pseudoaleatorio (keystream) derivado de una clave y un salt
    utilizando bloques encadenados con SHA-256 en modo contador.
    """
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        block = hashlib.sha256(key + salt + counter.to_bytes(4, byteorder="big")).digest()
        stream.extend(block)
        counter += 1
    return bytes(stream[:length])


@dataclass(frozen=True)
class EncryptedPassword:
    """
    Contenedor inmutable para contraseñas cifradas con clave efímera de sesión.
    Protege contra fugas en volcados de memoria, logs, serializaciones y tracebacks.
    """
    ciphertext: bytes
    session_id: str
    salt: bytes

    def __repr__(self) -> str:
        return "<EncryptedPassword: PROTECTED>"

    def __str__(self) -> str:
        return "********"

    def __bool__(self) -> bool:
        return bool(self.ciphertext)


def create_security_session(session_id: Optional[str] = None) -> str:
    """
    Crea o registra una sesión de seguridad con una clave dinámica de 256 bits.
    Si no se indica session_id, se genera un identificador aleatorio único.
    """
    sid = session_id if session_id else secrets.token_hex(16)
    _SESSION_KEYS[sid] = secrets.token_bytes(32)
    return sid


def get_security_session_key(session_id: str) -> Optional[bytes]:
    """
    Retorna la clave binaria asociada a la sesión de seguridad, o None si no existe.
    """
    return _SESSION_KEYS.get(session_id)


def clear_security_session(session_id: str) -> None:
    """
    Elimina e invalida la clave dinámica asociada a una sesión de seguridad.
    """
    _SESSION_KEYS.pop(session_id, None)


def clear_all_security_sessions() -> None:
    """
    Limpia todas las claves de sesión activas en el proceso.
    """
    _SESSION_KEYS.clear()


def encrypt_password(
    plain_password: Union[EncryptedPassword, str, None] = "",
    session_id: Optional[str] = None
) -> EncryptedPassword:
    """
    Cifra una contraseña en texto plano o normaliza valores y retorna un EncryptedPassword.
    Si ya es un EncryptedPassword, lo retorna tal cual (idempotente).
    """
    if isinstance(plain_password, EncryptedPassword):
        return plain_password

    if plain_password is None:
        plain_text = ""
    elif isinstance(plain_password, str):
        plain_text = plain_password
    else:
        plain_text = str(plain_password)

    sid = session_id
    if sid is None:
        sid = create_security_session()
    elif sid not in _SESSION_KEYS:
        sid = create_security_session(sid)

    key = _SESSION_KEYS[sid]
    salt = secrets.token_bytes(16)
    data = plain_text.encode("utf-8")
    keystream = _generate_keystream(key, salt, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, keystream))

    return EncryptedPassword(ciphertext=ciphertext, session_id=sid, salt=salt)


def decrypt_password(encrypted_password: Union[EncryptedPassword, str, None]) -> str:
    """
    Desencripta un EncryptedPassword utilizando la clave de sesión activa en asisdb.
    Si recibe None o vacío, retorna cadena vacía de forma transparente.
    Lanza ValueError si la sesión de seguridad no existe o ha expirado.
    """
    if encrypted_password is None or encrypted_password == "":
        return ""

    if not isinstance(encrypted_password, EncryptedPassword):
        raise TypeError(
            f"[asisdb] 'encrypted_password' debe ser EncryptedPassword, no {type(encrypted_password).__name__}."
        )

    key = _SESSION_KEYS.get(encrypted_password.session_id)
    if key is None:
        raise ValueError(
            f"[asisdb] Sesión de seguridad inválida o expirada para la contraseña: '{encrypted_password.session_id}'."
        )

    keystream = _generate_keystream(key, encrypted_password.salt, len(encrypted_password.ciphertext))
    data = bytes(a ^ b for a, b in zip(encrypted_password.ciphertext, keystream))
    return data.decode("utf-8")

