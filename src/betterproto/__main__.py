from .plugin.exception_hook import install_exception_hook

install_exception_hook()
from .plugin.cli import app as main

if __name__ == "__main__":
    main()
