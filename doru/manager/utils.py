import os
from copy import deepcopy
from logging import getLogger
from shutil import copyfile
from typing import Any, Callable, List

from nanoid import generate

logger = getLogger(__name__)


def rollback(properties=List[str], files=List[str]) -> Any:
    """
    This decorator rolls back the specified propertes and files when some exception occurs in the method.

    Parameters
    ----------
    properties : List[str]
        List of properties you want to roll back
    files: List[str]
        List of properties containing the path to the file you want to roll back

    Raises
    ------
    DoruError
        A case in which a non-existent property or file is specified.

    Examples
    --------
    >>> class Foo:
    ...     prop = {"foo": "bar"}
    ...     file_path = Path("path/to/file.json")
    ...
    ...     @rollback(properties=["prop"], files=["file_path"])
    ...     def bad_method(self):
    ...         self.prop["hoge"] = "hogehoge"
    ...         with open(self.file_path, "w") as f:
    ...             json.dump(self.prop, f)
    ...         raise Exception  # something wrong...
    ...
    ...     def read(self):
    ...         with open(self.file_path, "r") as f:
    ...             return json.load(f)
    ...
    >>> foo = Foo()
    >>> foo.prop
    {'foo': 'bar'}
    >>> foo.read()
    {'foo': 'bar'}
    >>> foo.bad_method()
    Traceback (most recent call last):
        ...
    >>> foo.prop
    {'foo': 'bar'}
    >>> foo.read()
    {'foo': 'bar'}
    """

    def wrapper(func: Callable[..., Any]) -> Any:
        def _wrapper(self, *args, **kwargs) -> Any:
            property_backups = {}
            file_backups = {}

            # backup properties
            for prop in properties:
                property_backups[prop] = deepcopy(getattr(self, prop))

            # create backup files
            for file in files:
                origin = getattr(self, file)
                backup = f"{origin}_bk_{generate()}"
                file_backups[origin] = backup
                copyfile(src=origin, dst=backup)

            try:
                result = func(self, *args, **kwargs)
            except Exception:
                for prop, backup in property_backups.items():
                    setattr(self, prop, backup)
                for origin, backup in file_backups.items():
                    copyfile(backup, origin)
                raise
            finally:
                for file_backup in file_backups.values():
                    os.remove(file_backup)
            return result

        return _wrapper

    return wrapper
