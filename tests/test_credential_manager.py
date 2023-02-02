import json
from typing import Any, Dict

import pytest

from doru.api.schema import Credential
from doru.manager.credential_manager import CredentialManager, create_credential_manager

TEST_DATA = {
    "bitbank": {
        "key": "bitbank_key",
        "secret": "bitbank_secret",
    },
}


@pytest.fixture
def credential_file(tmpdir, credentials: Dict[str, Any]):
    file = tmpdir.mkdir("tmp").join("credential.json")
    with open(file, "w") as fp:
        json.dump(credentials, fp)
    return file


@pytest.fixture
def credential_manager(credential_file) -> CredentialManager:
    return create_credential_manager(credential_file)


@pytest.mark.parametrize("credentials", [TEST_DATA, {}])
def test_init_with_valid_credential_file_succeed(credential_file, credentials):
    m = create_credential_manager(credential_file)
    assert m.credentials == credentials


def test_init_without_credential_file_succeed(tmpdir, caplog):
    from logging import WARNING

    d = tmpdir.mkdir("tmp")
    file = f"{d}/credential.json"
    m = create_credential_manager(file)

    assert m.credentials == {}
    assert [
        ("doru.manager.credential_manager", WARNING, "Credential file for this application could not be found.")
    ] == caplog.record_tuples
    with open(m.file, "r") as f:
        assert json.load(f) == {}


def test_init_with_invalid_json_file_raise_exception(tmpdir):
    from pathlib import Path

    file = Path(tmpdir.mkdir("tmp").join("credential.json"))
    file.touch()
    with pytest.raises(json.decoder.JSONDecodeError):
        create_credential_manager(str(file))


@pytest.mark.parametrize(
    "credentials",
    [
        {"bitbank": {"key": "bitbank_key"}},  # without "secret"
        {"bitbank": {"secret": "bitbank_secret"}},  # without "key"
        {"bitbank": {"key": "", "secret": ""}},  # key and secret have empty fields
    ],
)
def test_init_with_invalid_credential_schema_raise_exception(tmpdir, credentials):
    file = tmpdir.mkdir("tmp").join("credential.json")
    with open(file, "w") as fp:
        json.dump(credentials, fp)
    with pytest.raises(Exception):
        create_credential_manager(str(file))


@pytest.mark.parametrize(
    "cred",
    [
        Credential(exchange="bitflyer", key="bitflyer_key", secret="bitflyer_secret"),
        Credential(exchange="bitbank", key="bitbank_key_changed", secret="bitbank_secret_changed"),
    ],
)
@pytest.mark.parametrize("credentials", [TEST_DATA])
def test_add_credential_with_valid_credential_succeed(
    credential_manager: CredentialManager, cred: Credential, credentials
):
    credential_manager.add_credential(cred)
    result = {**credentials, **{cred.exchange: {"key": cred.key, "secret": cred.secret}}}
    assert credential_manager.credentials == result
    with open(credential_manager.file, "r") as f:
        assert json.load(f) == result


@pytest.mark.parametrize(
    "credentials, cred", [(TEST_DATA, Credential(exchange="bitflyer", key="bitflyer_key", secret="bitflyer_secret"))]
)
def test_add_credential_with_exception_on_writing_throw_exception(
    credential_manager: CredentialManager, cred, credentials, mocker
):
    mocker.patch("doru.manager.credential_manager.CredentialManager._write", side_effect=Exception)
    with pytest.raises(Exception):
        credential_manager.add_credential(cred)
    # add_credential change nothing
    assert credential_manager.credentials == credentials
    with open(credential_manager.file, "r") as f:
        assert json.load(f) == credentials


@pytest.mark.parametrize("credentials, exchange", [(TEST_DATA, "bitbank")])
def test_get_credential_with_valid_key_succeed(credential_manager: CredentialManager, credentials, exchange):
    c = credential_manager.get_credential(exchange)
    assert c is not None
    assert c == Credential(exchange=exchange, key=credentials[exchange]["key"], secret=credentials[exchange]["secret"])


@pytest.mark.parametrize("credentials, exchange", [(TEST_DATA, "bitflyer")])
def test_get_credential_with_invalid_key_return_none(credential_manager: CredentialManager, exchange):
    assert credential_manager.get_credential(exchange) is None


@pytest.mark.parametrize("credentials, exchange", [(TEST_DATA, "bitbank")])
def test_remove_credential_with_valid_key_succeed(credential_manager: CredentialManager, exchange):
    credential_manager.remove_credential(exchange)
    assert credential_manager.credentials == {}
    with open(credential_manager.file, "r") as f:
        assert json.load(f) == {}


@pytest.mark.parametrize("credentials, exchange", [(TEST_DATA, "bitflyer")])
def test_remove_credential_with_invalid_key_raise_exception(
    credential_manager: CredentialManager, exchange, credentials
):
    with pytest.raises(KeyError):
        credential_manager.remove_credential(exchange)
    assert credential_manager.credentials == credentials
    with open(credential_manager.file, "r") as f:
        assert json.load(f) == credentials


@pytest.mark.parametrize("credentials, exchange", [(TEST_DATA, "bitbank")])
def test_remove_credential_with_exception_on_writing_throw_exception(
    credential_manager: CredentialManager, exchange, credentials, mocker
):
    mocker.patch("doru.manager.credential_manager.CredentialManager._write", side_effect=Exception)
    with pytest.raises(Exception):
        credential_manager.remove_credential(exchange)
    # remove_credential change nothing
    assert credential_manager.credentials == credentials
    with open(credential_manager.file, "r") as f:
        assert json.load(f) == credentials
