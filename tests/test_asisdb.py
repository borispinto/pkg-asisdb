# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 ASISNET Computación, CA <proyectos@asisnet.net>
# SPDX-FileCopyrightText: 2026 Boris Pinto <borispinto@gmail.com>
# SPDX-License-Identifier: MIT
# Autor: Boris Pinto <borispinto@gmail.com>
# Contacto Institucional: ASISNET Computación, CA <proyectos@asisnet.net>
# File: tests/test_asisdb.py

"""
Pruebas unitarias para la librería asisdb.
Valida conexión multi-motor, interpolación de comodines, DBFReader y ConnectionConfig.
"""

import pytest
import asisdb as db


def test_supported_drivers():
    drivers = db.get_supported_drivers()
    assert "mssql" in drivers
    assert "sqlite" in drivers
    assert "postgresql" in drivers
    assert "mysql" in drivers
    assert "foxpro" in drivers


def test_interpolate_placeholders():
    template = "server={host};database=BD_{empresa}"
    params = {"host": "192.168.1.100", "empresa": "01"}
    result = db.interpolate_placeholders(template, params)
    assert result == "server=192.168.1.100;database=BD_01"


def test_interpolate_db_url_placeholders():
    url_tmpl = "sqlite:///data_{empresa}.db"
    params = {"empresa": "05"}
    result = db.interpolate_db_url_placeholders(url_tmpl, params)
    assert result == "sqlite:///data_05.db"

    # Con contraseña cifrada
    enc = db.encrypt_password("p@ss:word")
    tmpl_cred = "postgresql://{user}:{password}@{host}/{database}"
    res_cred = db.interpolate_db_url_placeholders(
        tmpl_cred,
        {"user": "admin", "password": enc, "host": "10.0.0.1", "database": "db"}
    )
    assert "admin:p%40ss%3Aword@10.0.0.1/db" in res_cred


def test_sqlite_engine_and_query(tmp_path):
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file}"
    engine = db.get_db_engine(url)
    assert engine is not None

    db.execute_statement("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)", engine=engine)
    db.execute_statement("INSERT INTO test (id, name) VALUES (:id, :name)", params={"id": 1, "name": "Empresa01"}, engine=engine)

    rows = db.execute_query("SELECT * FROM test WHERE id = :id", params={"id": 1}, engine=engine)
    assert len(rows) == 1
    assert rows[0]["name"] == "Empresa01"

    db.close_engine(engine)


def test_db_connection_function(tmp_path):
    db_file = tmp_path / "test_conn.db"
    params = {
        "driver": "sqlite",
        "database": str(db_file)
    }
    success, msg = db.test_db_connection(params)
    assert success is True


def test_dbf_reader_availability():
    assert hasattr(db.DBFReader, "is_available")
    assert isinstance(db.DBFReader.is_available(), bool)


def test_dbf_cache_manager():
    cache = db.DBFCacheManager()
    cache.set("dummy.dbf", "100", {"CODIGO": "100", "NOMBRE": "Test"})
    record = cache.get("dummy.dbf", "100")
    assert record is not None
    assert record["NOMBRE"] == "Test"

    cache.clear("dummy.dbf")
    assert cache.get("dummy.dbf", "100") is None


def test_connection_config_from_dict():
    raw_data = {
        "driver": "mssql",
        "host": "192.168.1.50",
        "port": "1433",
        "database": "BD_PROD",
        "user": "sa",
        "password": "secret_password",
        "sql_driver_autodetect": "true",
        "extra_unknown_key": "ignore_me"
    }
    cfg = db.ConnectionConfig.from_dict(raw_data)
    assert cfg.driver == "mssql"
    assert cfg.host == "192.168.1.50"
    assert cfg.port == "1433"
    assert cfg.database == "BD_PROD"
    assert cfg.user == "sa"
    assert isinstance(cfg.password, db.EncryptedPassword)
    assert db.decrypt_password(cfg.password) == "secret_password"
    assert cfg.sql_driver_autodetect == "true"
    assert not hasattr(cfg, "extra_unknown_key")


def test_connection_config_automatic_encryption():
    # Enviar texto plano se encripta automáticamente en __init__
    cfg1 = db.ConnectionConfig(password="plain_secret")
    assert isinstance(cfg1.password, db.EncryptedPassword)
    assert db.decrypt_password(cfg1.password) == "plain_secret"

    # Enviar texto plano se encripta automáticamente en from_dict
    cfg2 = db.ConnectionConfig.from_dict({"password": "plain_secret_dict"})
    assert isinstance(cfg2.password, db.EncryptedPassword)
    assert db.decrypt_password(cfg2.password) == "plain_secret_dict"

    # Nulos o vacíos se manejan como contraseñas vacías cifradas
    cfg_empty = db.ConnectionConfig(password="")
    assert isinstance(cfg_empty.password, db.EncryptedPassword)
    assert bool(cfg_empty.password) is False
    assert db.decrypt_password(cfg_empty.password) == ""

    cfg_none = db.ConnectionConfig(password=None)
    assert isinstance(cfg_none.password, db.EncryptedPassword)
    assert bool(cfg_none.password) is False
    assert db.decrypt_password(cfg_none.password) == ""

    # Idempotencia: pasar un EncryptedPassword lo mantiene intacto
    enc = db.encrypt_password("test_pass")
    cfg_enc = db.ConnectionConfig(password=enc)
    assert cfg_enc.password is enc


def test_encrypted_password_lifecycle():
    plain = "MiClaveSuperSecreta_2026!"
    enc = db.encrypt_password(plain)

    assert isinstance(enc, db.EncryptedPassword)
    assert repr(enc) == "<EncryptedPassword: PROTECTED>"
    assert str(enc) == "********"
    assert enc.ciphertext != plain.encode("utf-8")
    assert plain not in repr(enc)
    assert plain not in str(enc)

    # Desencriptado exitoso
    decrypted = db.decrypt_password(enc)
    assert decrypted == plain

    # Idempotencia
    assert db.encrypt_password(enc) is enc

    # Nulos y vacíos
    enc_empty = db.encrypt_password("")
    assert isinstance(enc_empty, db.EncryptedPassword)
    assert bool(enc_empty) is False
    assert db.decrypt_password(enc_empty) == ""

    enc_none = db.encrypt_password(None)
    assert isinstance(enc_none, db.EncryptedPassword)
    assert bool(enc_none) is False
    assert db.decrypt_password(enc_none) == ""


def test_encrypted_password_custom_session():
    sid = db.create_security_session("sesion_especifica")
    enc = db.encrypt_password("clave_sesion", session_id=sid)

    assert enc.session_id == "sesion_especifica"
    assert db.decrypt_password(enc) == "clave_sesion"


def test_encrypted_password_expired_session():
    sid = db.create_security_session()
    enc = db.encrypt_password("clave_efimera", session_id=sid)

    # Invalida/limpia la clave de sesión en asisdb
    db.clear_security_session(sid)

    # Sin la clave en asisdb, el objeto no se puede abrir
    with pytest.raises(ValueError, match="inválida o expirada"):
        db.decrypt_password(enc)


def test_connection_config_with_encrypted_password():
    plain = "P@ssw0rd!#_Segura"
    enc = db.encrypt_password(plain)

    cfg = db.ConnectionConfig(
        driver="postgresql",
        host="10.0.0.1",
        database="mydb",
        user="appuser",
        password=enc
    )
    assert cfg.password is enc
    assert plain not in repr(cfg)
    assert plain not in str(cfg)

    # Comprobar que build_db_url desencripta efímeramente y arma la URL
    url = db.build_db_url(cfg)
    assert "appuser:P%40ssw0rd%21%23_Segura@10.0.0.1/mydb" in url


def test_build_db_url_from_connection_config(tmp_path):
    db_file = tmp_path / "app.db"
    cfg = db.ConnectionConfig(
        driver="sqlite",
        database=str(db_file)
    )
    url = db.build_db_url(cfg)
    assert url == f"sqlite:///{db_file}"

    # Instanciación de motor usando ConnectionConfig
    engine = db.get_db_engine(config=cfg)
    assert engine is not None
    db.close_engine(engine)


def test_multiple_keyed_engines(tmp_path):
    db1 = tmp_path / "primary.db"
    db2 = tmp_path / "secondary.db"

    eng1 = db.get_db_engine(key="primary", config={"driver": "sqlite", "database": str(db1)})
    eng2 = db.get_db_engine(key="secondary", config={"driver": "sqlite", "database": str(db2)})

    assert eng1 is not eng2

    # Verificar reutilización en caché
    eng1_cached = db.get_db_engine(key="primary")
    assert eng1_cached is eng1

    db.close_engine(key="primary")
    db.close_engine(key="secondary")
    db.reset_engine()


def test_test_connection_with_encrypted_password(tmp_path):
    db_file = tmp_path / "enc_test.db"
    enc = db.encrypt_password("dummy_password")
    ok, msg, diag = db.test_connection(driver="sqlite", database=str(db_file), password=enc)
    assert ok is True
    assert "dummy_password" not in diag["target_url"]


def test_test_connection_masking_with_encrypted_fields(tmp_path):
    db_file = tmp_path / "mask_test.db"
    extra_enc = db.encrypt_password("extra_secret_value")

    ok, msg, diag = db.test_connection(
        driver="sqlite",
        database=str(db_file),
        password="plain_password",
        custom_token="token_abc_123",
        custom_header="header_normal",
        extra_secret=extra_enc,
        encrypted_fields=["custom_token"]
    )
    assert ok is True
    used = diag["used_params"]
    # 1. Contraseña canónica siempre enmascarada
    assert used["password"] == "<password>"
    # 2. Campo explícito en encrypted_fields enmascarado
    assert used["custom_token"] == "<custom_token>"
    # 3. Campo tipado con EncryptedPassword enmascarado automáticamente por su tipo
    assert used["extra_secret"] == "<extra_secret>"
    # 4. Campo normal no se enmascara (sin falsos positivos por heurística)
    assert used["custom_header"] == "header_normal"


def test_interpolate_db_url_placeholders_typed_and_canonical():
    enc_secret = db.encrypt_password("s3cr3t/val")
    tmpl = "custom://{user}:{password}@{host}/api?token={api_token}&dept={department}"
    params = {
        "user": "usr@domain",
        "password": "p@ssword:123",
        "host": "127.0.0.1",
        "api_token": enc_secret,
        "department": "ventas"
    }
    result = db.interpolate_db_url_placeholders(tmpl, params)
    # user y password codificados canónicamente
    assert "usr%40domain" in result
    assert "p%40ssword%3A123" in result
    # api_token descifrado y codificado por ser EncryptedPassword
    assert "token=s3cr3t%2Fval" in result
    # department sin alteración
    assert "dept=ventas" in result
