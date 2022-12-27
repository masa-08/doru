import os

DORU_SOCK_NAME = os.environ.get("DORU_SOCK_NAME", "/tmp/doru.sock")
DORU_CREDENTIAL_FILE = os.environ.get("DORU_CREDENTIAL_FILE", "~/.doru/credential.json")
