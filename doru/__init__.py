__version__ = "0.1.0"

try:
    from .main import main
except ImportError:

    def main() -> None:
        import sys

        print("The doru command line client could not run because of the luck of the required dependencies.")
        sys.exit(1)
