import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def vault():
    with patch("pathlib.Path.mkdir"), \
         patch("os.system"):
        from vault.vault import Vault
        v = Vault()
    v._authenticate = MagicMock()
    v._encryption = MagicMock()
    v._conf = MagicMock()
    v._master_pwd = "Master$1"
    return v

def test_master_pwd_returns_value(vault):
    assert vault.master_pwd == "Master$1"

def test_master_pwd_returns_none_when_not_set(vault):
    vault._master_pwd = None
    assert vault.master_pwd is None

def test_validate_password_valid(vault):
    assert vault._validate_password("Secure$1") is True

def test_validate_password_too_short(vault):
    assert vault._validate_password("Sh$1") is False

def test_validate_password_no_digit(vault):
    assert vault._validate_password("Securexx$") is False

def test_validate_password_no_special_char(vault):
    assert vault._validate_password("Secure11") is False

def test_validate_password_no_alpha(vault):
    assert vault._validate_password("12345678$") is False

def test_validate_password_exact_minimum_length(vault):
    assert vault._validate_password("Secur$1x") is True

def test_validate_password_empty_string(vault):
    assert vault._validate_password("") is False

def test_validate_password_all_special_chars(vault):
    assert vault._validate_password("!@#$%^&*") is False


def test_login_sets_master_pwd_on_success(vault):
    vault._authenticate.check_pwd.return_value = True
    with patch("curses.wrapper", return_value="Master$1"):
        vault._login()
    assert vault._master_pwd == "Master$1"

def test_login_returns_on_correct_password(vault):
    vault._authenticate.check_pwd.return_value = True
    with patch("curses.wrapper", return_value="Master$1"):
        vault._login()
    vault._authenticate.check_pwd.assert_called_once()

def test_login_retries_on_wrong_password(vault):
    vault._authenticate.check_pwd.side_effect = [False, False, True]
    with patch("curses.wrapper", side_effect=["wrong", None, "wrong", None, "Master$1"]):
        vault._login()
    assert vault._authenticate.check_pwd.call_count == 3

def test_login_stops_after_three_failed_attempts(vault):
    vault._authenticate.check_pwd.return_value = False
    with patch("curses.wrapper", return_value="wrong"), \
         patch("builtins.print") as mock_print:
        vault._login()
    assert vault._authenticate.check_pwd.call_count == 3
    mock_print.assert_called_with("Too many failed attempts.")

def test_login_does_not_set_master_pwd_on_failure(vault):
    vault._master_pwd = None
    vault._authenticate.check_pwd.return_value = False
    with patch("curses.wrapper", return_value="wrong"), \
         patch("builtins.print"):
        vault._login()
    assert vault._master_pwd is None

def test_add_service_calls_encryption(vault):
    with patch("curses.wrapper", side_effect=["github", "mypassword"]), \
         patch("builtins.print"):
        vault._add_service()
    vault._encryption.add_pwd.assert_called_once_with("github", "mypassword", "Master$1")

def test_add_service_lowercases_service_name(vault):
    with patch("curses.wrapper", side_effect=["GitHub", "mypassword"]), \
         patch("builtins.print"):
        vault._add_service()
    assert vault._encryption.add_pwd.call_args[0][0] == "github"

def test_add_service_prints_confirmation(vault):
    with patch("curses.wrapper", side_effect=["github", "mypassword"]), \
         patch("builtins.print") as mock_print:
        vault._add_service()
    mock_print.assert_called_once()
    assert "github" in mock_print.call_args[0][0]

def test_get_service_exits_early_when_empty(vault):
    vault._encryption.is_empty.return_value = True
    with patch("builtins.print") as mock_print:
        vault._get_service()
    vault._encryption.get_pwd.assert_not_called()
    mock_print.assert_called_with("No services saved.")

def test_get_service_copies_password_to_clipboard(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.get_pwd.return_value = "mypassword"
    with patch("curses.wrapper", side_effect=[None, "github"]), \
         patch("pyperclip.copy") as mock_copy, \
         patch("builtins.print"):
        vault._get_service()
    mock_copy.assert_called_once_with("mypassword")

def test_get_service_prints_confirmation(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.get_pwd.return_value = "mypassword"
    with patch("curses.wrapper", side_effect=[None, "github"]), \
         patch("pyperclip.copy"), \
         patch("builtins.print") as mock_print:
        vault._get_service()
    mock_print.assert_called_with("Password copied to clipboard.")

def test_get_service_strips_whitespace_from_input(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.get_pwd.return_value = "mypassword"
    with patch("curses.wrapper", side_effect=[None, "  github  "]), \
         patch("pyperclip.copy"), \
         patch("builtins.print"):
        vault._get_service()
    assert vault._encryption.get_pwd.call_args[0][0] == "github"

def test_remove_service_exits_early_when_empty(vault):
    vault._encryption.is_empty.return_value = True
    with patch("builtins.print") as mock_print:
        vault._remove_service()
    vault._encryption.remove_pwd.assert_not_called()
    mock_print.assert_called_with("No services saved.")

def test_remove_service_calls_encryption(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.remove_pwd.return_value = True
    with patch("curses.wrapper", side_effect=[None, "github"]), \
         patch("builtins.print"):
        vault._remove_service()
    vault._encryption.remove_pwd.assert_called_once_with("github")

def test_remove_service_lowercases_input(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.remove_pwd.return_value = True
    with patch("curses.wrapper", side_effect=[None, "GitHub"]), \
         patch("builtins.print"):
        vault._remove_service()
    assert vault._encryption.remove_pwd.call_args[0][0] == "github"

def test_remove_service_prints_success(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.remove_pwd.return_value = True
    with patch("curses.wrapper", side_effect=[None, "github"]), \
         patch("builtins.print") as mock_print:
        vault._remove_service()
    mock_print.assert_called_with("Successful.")

def test_remove_service_no_print_on_failure(vault):
    vault._encryption.is_empty.return_value = False
    vault._encryption.get_all.return_value = "github"
    vault._encryption.remove_pwd.return_value = False
    with patch("curses.wrapper", side_effect=[None, "github"]), \
         patch("builtins.print") as mock_print:
        vault._remove_service()
    mock_print.assert_not_called()

def test_remove_all_exits_early_when_empty(vault):
    vault._encryption.is_empty.return_value = True
    with patch("builtins.print") as mock_print:
        vault._remove_all()
    vault._encryption.clear.assert_not_called()
    mock_print.assert_called_with("No services saved.")

def test_remove_all_cancels_without_yes(vault):
    vault._encryption.is_empty.return_value = False
    with patch("curses.wrapper", return_value="NO"), \
         patch("builtins.print") as mock_print:
        vault._remove_all()
    vault._encryption.clear.assert_not_called()
    mock_print.assert_called_with("Cancelled.")

def test_remove_all_cancels_on_lowercase_yes(vault):
    vault._encryption.is_empty.return_value = False
    with patch("curses.wrapper", return_value="yes"), \
         patch("builtins.print"):
        vault._remove_all()
    vault._encryption.clear.assert_not_called()

def test_remove_all_clears_on_yes(vault):
    vault._encryption.is_empty.return_value = False
    with patch("curses.wrapper", return_value="YES"), \
         patch("builtins.print"):
        vault._remove_all()
    vault._encryption.clear.assert_called_once()

def test_remove_all_prints_success(vault):
    vault._encryption.is_empty.return_value = False
    with patch("curses.wrapper", return_value="YES"), \
         patch("builtins.print") as mock_print:
        vault._remove_all()
    mock_print.assert_called_with("Removed all services.")
