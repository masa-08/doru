from pathlib import Path
from urllib.parse import quote

from requests_unixsocket import Session


class SessionWithSocket(Session):
    scheme: str = "http+unix://"
    sock: str

    def __init__(self, sock: str) -> None:
        super().__init__()
        sockpath = Path(sock).expanduser()
        self.sock = quote(str(sockpath), safe="")

    def _build_url(self, path: str) -> str:
        return self.scheme + str(Path(self.sock, path))

    def request(self, method: str, url: str, **kwargs):
        return super().request(method, self._build_url(url), **kwargs)


def create_session(sock: str) -> SessionWithSocket:
    return SessionWithSocket(sock)
