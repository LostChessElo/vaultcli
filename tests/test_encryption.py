import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from cryptography.fernet import InvalidToken


@pytest.fixture
def enc():
    with patch("pathlib.Path.mkdir"):
        from vault.encryption import Encryption
        e = Encryption()
    e._conf = MagicMock()
    e._conf.exists.return_value = True
    e._conf.is_empty.return_value = False
    e._conf.read_master.return_value = {
        "master_pwd": "hashed",
        "salt": "thisisavalidsaltvalue!!"
    }
    return e


MASTER_PWD = "Master$1"


def test_derive_key_returns_bytes(enc):
    assert isinstance(enc._derive_key(MASTER_PWD), bytes)

def test_derive_key_is_deterministic(enc):
    assert enc._derive_key(MASTER_PWD) == enc._derive_key(MASTER_PWD)

def test_derive_key_differs_for_different_passwords(enc):
    assert enc._derive_key(MASTER_PWD) != enc._derive_key("Other$1")

def test_derive_key_raises_when_config_missing(enc):
    enc._conf.exists.return_value = False
    with pytest.raises(RuntimeError):
        enc._derive_key(MASTER_PWD)

def test_derive_key_raises_when_config_empty(enc):
    enc._conf.is_empty.return_value = True
    with pytest.raises(RuntimeError):
        enc._derive_key(MASTER_PWD)

def test_encrypt_returns_string(enc):
    key = enc._derive_key(MASTER_PWD)
    assert isinstance(enc._encrypt("mypassword", key), str)

def test_encrypt_does_not_return_plaintext(enc):
    key = enc._derive_key(MASTER_PWD)
    assert enc._encrypt("mypassword", key) != "mypassword"

def test_decrypt_returns_original(enc):
    key = enc._derive_key(MASTER_PWD)
    encrypted = enc._encrypt("mypassword", key)
    assert enc._decrypt(encrypted, key) == "mypassword"

def test_decrypt_fails_with_wrong_key(enc):
    key1 = enc._derive_key(MASTER_PWD)
    key2 = enc._derive_key("Wrong$1")
    encrypted = enc._encrypt("mypassword", key1)
    with pytest.raises(InvalidToken):
        enc._decrypt(encrypted, key2)

def test_encrypt_same_value_produces_different_ciphertext(enc):
    key = enc._derive_key(MASTER_PWD)
    assert enc._encrypt("mypassword", key) != enc._encrypt("mypassword", key)

def test_read_from_returns_empty_dict_when_file_missing(enc):
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert enc.read_from() == {}

def test_read_from_returns_dict(enc):
    data = json.dumps({"github": "encryptedvalue"})
    with patch("builtins.open", mock_open(read_data=data)):
        assert isinstance(enc.read_from(), dict)

def test_read_from_returns_correct_data(enc):
    data = json.dumps({"github": "encryptedvalue"})
    with patch("builtins.open", mock_open(read_data=data)):
        assert enc.read_from()["github"] == "encryptedvalue"

def test_write_to_raises_without_sudo(enc):
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(PermissionError):
            enc.write_to({"github": "enc"})

def test_write_to_raises_on_non_dict(enc):
    with patch("os.geteuid", return_value=0):
        with pytest.raises(ValueError):
            enc.write_to("not a dict")

def test_write_to_raises_on_none(enc):
    with patch("os.geteuid", return_value=0):
        with pytest.raises(ValueError):
            enc.write_to(None)

def test_write_to_sets_permissions(enc):
    chmod_mock = MagicMock()
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open()), \
         patch.object(Path, "exists", return_value=True), \
         patch.object(Path, "chmod", chmod_mock), \
         patch("os.chown"):
        enc.write_to({"github": "enc"})
        chmod_mock.assert_called_once_with(0o600)

def test_is_empty_raises_without_sudo(enc):
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(PermissionError):
            enc.is_empty()

def test_is_empty_true_when_file_missing(enc):
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", side_effect=FileNotFoundError):
        assert enc.is_empty() is True

def test_is_empty_true_for_empty_dict(enc):
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open(read_data="{}")):
        assert enc.is_empty() is True

def test_is_empty_false_when_data_present(enc):
    data = json.dumps({"github": "encryptedvalue"})
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open(read_data=data)):
        assert enc.is_empty() is False

def test_add_pwd_stores_encrypted_value(enc):
    enc.read_from = MagicMock(return_value={})
    enc.write_to = MagicMock()
    enc.add_pwd("github", "mypassword", MASTER_PWD)
    stored = enc.write_to.call_args[0][0]
    assert "github" in stored
    assert stored["github"] != "mypassword"

def test_add_pwd_preserves_existing_services(enc):
    key = enc._derive_key(MASTER_PWD)
    enc.read_from = MagicMock(return_value={"gitlab": enc._encrypt("existingpass", key)})
    enc.write_to = MagicMock()
    enc.add_pwd("github", "newpass", MASTER_PWD)
    stored = enc.write_to.call_args[0][0]
    assert "gitlab" in stored
    assert "github" in stored

def test_add_pwd_overwrites_existing_service(enc):
    key = enc._derive_key(MASTER_PWD)
    enc.read_from = MagicMock(return_value={"github": enc._encrypt("oldpass", key)})
    enc.write_to = MagicMock()
    enc.add_pwd("github", "newpass", MASTER_PWD)
    stored = enc.write_to.call_args[0][0]
    assert enc._decrypt(stored["github"], key) == "newpass"

def test_get_pwd_returns_correct_password(enc):
    key = enc._derive_key(MASTER_PWD)
    encrypted = enc._encrypt("mypassword", key)
    enc.read_from = MagicMock(return_value={"github": encrypted})
    assert enc.get_pwd("github", MASTER_PWD) == "mypassword"

def test_get_pwd_raises_on_missing_service(enc):
    enc.read_from = MagicMock(return_value={})
    with pytest.raises(KeyError):
        enc.get_pwd("github", MASTER_PWD)

def test_get_pwd_raises_on_empty_vault(enc):
    enc.read_from = MagicMock(return_value={})
    with pytest.raises(KeyError):
        enc.get_pwd("github", MASTER_PWD)

def test_get_pwd_raises_on_wrong_master_password(enc):
    key = enc._derive_key(MASTER_PWD)
    encrypted = enc._encrypt("mypassword", key)
    enc.read_from = MagicMock(return_value={"github": encrypted})
    with pytest.raises(InvalidToken):
        enc.get_pwd("github", "Wrong$1")

def test_remove_pwd_removes_service(enc):
    key = enc._derive_key(MASTER_PWD)
    enc.read_from = MagicMock(return_value={"github": enc._encrypt("pass", key)})
    enc.write_to = MagicMock()
    enc.remove_pwd("github")
    stored = enc.write_to.call_args[0][0]
    assert "github" not in stored

def test_remove_pwd_returns_true_on_success(enc):
    key = enc._derive_key(MASTER_PWD)
    enc.read_from = MagicMock(return_value={"github": enc._encrypt("pass", key)})
    enc.write_to = MagicMock()
    assert enc.remove_pwd("github") is True

def test_remove_pwd_raises_on_missing_service(enc):
    enc.read_from = MagicMock(return_value={})
    with pytest.raises(KeyError):
        enc.remove_pwd("github")

def test_remove_pwd_preserves_other_services(enc):
    key = enc._derive_key(MASTER_PWD)
    enc.read_from = MagicMock(return_value={
        "github": enc._encrypt("pass1", key),
        "gitlab": enc._encrypt("pass2", key),
    })
    enc.write_to = MagicMock()
    enc.remove_pwd("github")
    stored = enc.write_to.call_args[0][0]
    assert "gitlab" in stored

def test_get_all_returns_string(enc):
    enc.read_from = MagicMock(return_value={"github": "enc"})
    assert isinstance(enc.get_all(), str)

def test_get_all_contains_service_names(enc):
    enc.read_from = MagicMock(return_value={"github": "enc", "gitlab": "enc"})
    result = enc.get_all()
    assert "github" in result
    assert "gitlab" in result

def test_get_all_returns_empty_string_for_empty_vault(enc):
    enc.read_from = MagicMock(return_value={})
    assert enc.get_all() == ""

def test_get_all_does_not_return_encrypted_values(enc):
    key = enc._derive_key(MASTER_PWD)
    encrypted = enc._encrypt("mypassword", key)
    enc.read_from = MagicMock(return_value={"github": encrypted})
    assert encrypted not in enc.get_all()

def test_clear_raises_without_sudo(enc):
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(PermissionError):
            enc.clear()

def test_clear_writes_empty_dict(enc):
    m = mock_open()
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", m):
        enc.clear()
        handle = m()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        assert json.loads(written) == {}

def test_clear_raises_file_not_found(enc):
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            enc.clear()
