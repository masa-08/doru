import os

DORU_SOCK_NAME = os.environ.get("DORU_SOCK_NAME", "/tmp/doru.sock")
DORU_CREDENTIAL_FILE = os.environ.get("DORU_CREDENTIAL_FILE", "~/.doru/credential.json")
DORU_TASK_FILE = os.environ.get("DORU_TASK_FILE", "~/.doru/task.json")
try:
    DORU_TASK_LIMIT = int(os.environ["DORU_TASK_LIMIT"])
except (KeyError, ValueError):
    DORU_TASK_LIMIT = 50
