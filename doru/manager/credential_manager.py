import json
import os
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional

from doru.api.schema import Credential, CredentialBase
from doru.envs import DORU_CREDENTIAL_FILE
from doru.types import Exchange

logger = getLogger("doru")


class CredentialManager:
    credentials: Dict[Exchange, CredentialBase]

    def __init__(self, file: str) -> None:
        self.file = Path(file).expanduser()
        try:
            self._read()
        except FileNotFoundError:
            logger.warning("Credential file for this application could not be found.")
            self.credentials = {}

            if not os.path.exists(self.file.parent):
                self.file.parent.mkdir(parents=True)
            self._write()
        except Exception as e:
            logger.error(f"Failed to read the credential file: {e}")
            raise e

    def _write(self) -> None:
        with open(self.file, "w") as f:
            credentials_dict = {k: v.dict() for (k, v) in self.credentials.items()}
            json.dump(credentials_dict, f)

    def _read(self) -> None:
        with open(self.file, "r") as f:
            credentials = json.load(f)
            self.credentials = {k: CredentialBase.parse_obj(v) for (k, v) in credentials.items()}

    def add_credential(self, cred: Credential) -> None:
        credentials_backup = self.credentials.copy()
        self.credentials[cred.exchange] = CredentialBase(key=cred.key, secret=cred.secret)
        try:
            self._write()
        except Exception as e:
            logger.error(str(e))
            self.credentials = credentials_backup  # If the dump fails for any reason, rewind the process.
            raise e

    def get_credential(self, exchange: Exchange) -> Optional[Credential]:
        c = self.credentials.get(exchange)
        if c is None:
            return None
        return Credential(key=c.key, secret=c.secret, exchange=exchange)

    def remove_credential(self, exchange: Exchange) -> None:
        credentials_backup = self.credentials.copy()
        try:
            self.credentials.pop(exchange)
            self._write()
        except Exception as e:
            logger.error(str(e))
            self.credentials = credentials_backup  # If the dump fails for any reason, rewind the process.
            raise e


def create_credential_manager(file: str = DORU_CREDENTIAL_FILE) -> CredentialManager:
    return CredentialManager(file)
