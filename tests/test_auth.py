import pytest
import bcrypt
from unittest.mock import patch, MagicMock


@pytest.fixture
def auth():
    with patch("pathlib.Path.mkdir"):
        from vault.auth import Auth
        a = Auth()
    a._config = MagicMock()
    return a



def test_is_configured_true_when_exists_and_not_empty(auth):
    auth._config.exists.return_value = True
    auth._config.is_empty.return_value = False
    assert auth.is_configured() is True

def test_is_configured_false_when_not_exists(auth):
    auth._config.exists.return_value = False
    auth._config.is_empty.return_value = True
    assert auth.is_configured() is False

def test_is_configured_false_when_empty(auth):
    auth._config.exists.return_value = True
    auth._config.is_empty.return_value = True
    assert auth.is_configured() is False



def test_check_pwd_raises_if_not_configured(auth):
    auth._config.exists.return_value = False
    auth._config.is_empty.return_value = True
    with pytest.raises(RuntimeError):
        auth.check_pwd("anypassword")

def test_check_pwd_returns_true_for_correct_password(auth):
    pwd = "Correct$1"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd.encode(), salt).decode()
    auth._config.exists.return_value = True
    auth._config.is_empty.return_value = False
    auth._config.read_master.return_value = {"master_pwd": hashed, "salt": salt.decode()}
    assert auth.check_pwd(pwd) is True

def test_check_pwd_returns_false_for_wrong_password(auth):
    pwd = "Correct$1"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd.encode(), salt).decode()
    auth._config.exists.return_value = True
    auth._config.is_empty.return_value = False
    auth._config.read_master.return_value = {"master_pwd": hashed, "salt": salt.decode()}
    assert auth.check_pwd("Wrong$1") is False

def test_check_pwd_returns_false_for_empty_string(auth):
    pwd = "Correct$1"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd.encode(), salt).decode()
    auth._config.exists.return_value = True
    auth._config.is_empty.return_value = False
    auth._config.read_master.return_value = {"master_pwd": hashed, "salt": salt.decode()}
    assert auth.check_pwd("") is False

def test_check_pwd_returns_false_for_similar_password(auth):
    pwd = "Correct$1"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd.encode(), salt).decode()
    auth._config.exists.return_value = True
    auth._config.is_empty.return_value = False
    auth._config.read_master.return_value = {"master_pwd": hashed, "salt": salt.decode()}
    assert auth.check_pwd("correct$1") is False



def test_set_up_calls_write_to_master(auth):
    auth.set_up("Secure$1")
    auth._config.write_to_master.assert_called_once()

def test_set_up_stores_hashed_not_plaintext(auth):
    captured = {}
    auth._config.write_to_master.side_effect = lambda d: captured.update(d)
    auth.set_up("Secure$1")
    assert captured.get("master_pwd") != "Secure$1"

def test_set_up_stored_hash_verifies_correctly(auth):
    captured = {}
    auth._config.write_to_master.side_effect = lambda d: captured.update(d)
    auth.set_up("Secure$1")
    assert bcrypt.checkpw("Secure$1".encode(), captured["master_pwd"].encode())

def test_set_up_stores_salt(auth):
    captured = {}
    auth._config.write_to_master.side_effect = lambda d: captured.update(d)
    auth.set_up("Secure$1")
    assert "salt" in captured
    assert len(captured["salt"]) > 0

def test_set_up_different_calls_produce_different_hashes(auth):
    results = []
    auth._config.write_to_master.side_effect = lambda d: results.append(d.copy())
    auth.set_up("Secure$1")
    auth.set_up("Secure$1")
    assert results[0]["master_pwd"] != results[1]["master_pwd"]
