from project import validate_password, classify_service

def test_validate_password():
    assert validate_password("Secure$1") is True
    assert validate_password("weak") is False

def test_classify_service():
    assert classify_service("  GitHub  ") == "github"
    assert classify_service("GMAIL") == "gmail"

def test_validate_password_no_special():
    assert validate_password("Secure11") is False