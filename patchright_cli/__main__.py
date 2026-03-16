"""Entry point: python -m patchright_cli starts the server."""
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        from patchright_cli.server import start_server
        start_server()
    else:
        from patchright_cli.cli import cli
        cli()
