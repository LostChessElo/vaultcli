from vault.vault import Vault

def main():
    vault = Vault()
    vault.ui()

def validate_password(pwd: str) -> bool:
    vault = Vault.__new__(Vault)
    return vault._validate_password(pwd)

def derive_key(master_pwd: str, salt: bytes) -> bytes:
    from vault.encryption import Encryption
    enc = Encryption.__new__(Encryption)
    return enc._derive_key.__func__(enc, master_pwd)

def classify_service(name: str) -> str:
    return name.strip().lower()

if __name__ == "__main__":
    main()