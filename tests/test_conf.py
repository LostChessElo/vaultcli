import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path


@pytest.fixture
def config():
    with patch("pathlib.Path.mkdir"):
        from vault.conf import VaultConfig
        return VaultConfig()



def test_conf_dir_returns_path(config):
    assert isinstance(config.conf_dir, Path)

def test_conf_file_returns_path(config):
    assert isinstance(config.conf_file, Path)

def test_conf_file_is_inside_conf_dir(config):
    assert str(config.conf_file).startswith(str(config.conf_dir))



def test_exists_true_when_file_present(config):
    with patch.object(Path, "exists", return_value=True):
        assert config.exists() is True

def test_exists_false_when_file_missing(config):
    with patch.object(Path, "exists", return_value=False):
        assert config.exists() is False



def test_is_empty_true_when_file_missing(config):
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert config.is_empty() is True

def test_is_empty_true_when_empty_dict(config):
    with patch("builtins.open", mock_open(read_data="{}")):
        assert config.is_empty() is True

def test_is_empty_false_when_data_present(config):
    data = json.dumps({"master_pwd": "hashed", "salt": "somesalt"})
    with patch("builtins.open", mock_open(read_data=data)):
        assert config.is_empty() is False


def test_read_master_raises_without_sudo(config):
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(PermissionError):
            config.read_master()

def test_read_master_returns_dict(config):
    data = json.dumps({"master_pwd": "hashed", "salt": "somesalt"})
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open(read_data=data)):
        assert isinstance(config.read_master(), dict)

def test_read_master_returns_correct_keys(config):
    data = json.dumps({"master_pwd": "hashed", "salt": "somesalt"})
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open(read_data=data)):
        result = config.read_master()
        assert "master_pwd" in result
        assert "salt" in result

def test_read_master_raises_file_not_found(config):
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            config.read_master()


def test_write_to_master_raises_without_sudo(config):
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(PermissionError):
            config.write_to_master({"master_pwd": "x", "salt": "y"})

def test_write_to_master_writes_file(config):
    m = mock_open()
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", m), \
         patch.object(Path, "chmod"), \
         patch("os.chown"):
        config.write_to_master({"master_pwd": "x", "salt": "y"})
        m.assert_called_once_with(config.conf_file, "w")

def test_write_to_master_sets_permissions(config):
    chmod_mock = MagicMock()
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open()), \
         patch.object(Path, "chmod", chmod_mock), \
         patch("os.chown"):
        config.write_to_master({"master_pwd": "x", "salt": "y"})
        chmod_mock.assert_called_once_with(0o600)

def test_write_to_master_sets_root_ownership(config):
    chown_mock = MagicMock()
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", mock_open()), \
         patch.object(Path, "chmod"), \
         patch("os.chown", chown_mock):
        config.write_to_master({"master_pwd": "x", "salt": "y"})
        chown_mock.assert_called_once_with(config.conf_file, 0, 0)

def test_write_to_master_raises_file_not_found(config):
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            config.write_to_master({"master_pwd": "x", "salt": "y"})


def test_clear_raises_without_sudo(config):
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(PermissionError):
            config.clear()

def test_clear_writes_empty_dict(config):
    m = mock_open()
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", m):
        config.clear()
        handle = m()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        assert json.loads(written) == {}

def test_clear_raises_file_not_found(config):
    with patch("os.geteuid", return_value=0), \
         patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            config.clear()
