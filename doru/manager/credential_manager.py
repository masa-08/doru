import json
import os
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional

from doru.api.schema import Credential, CredentialBase
from doru.envs import DORU_CREDENTIAL_FILE
from doru.manager.utils import rollback

logger = getLogger(__name__)


class CredentialManager:
    credentials: Dict[str, CredentialBase]

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

    @rollback(properties=["credentials"], files=["file"])
    def add_credential(self, cred: Credential) -> None:
        self.credentials[cred.exchange] = CredentialBase(key=cred.key, secret=cred.secret)
        self._write()

    def get_credential(self, exchange: str) -> Optional[Credential]:
        c = self.credentials.get(exchange)
        if c is None:
            return None
        return Credential(key=c.key, secret=c.secret, exchange=exchange)

    @rollback(properties=["credentials"], files=["file"])
    def remove_credential(self, exchange: str) -> None:
        del self.credentials[exchange]
        self._write()


def create_credential_manager(file: str = DORU_CREDENTIAL_FILE) -> CredentialManager:
    return CredentialManager(file)
