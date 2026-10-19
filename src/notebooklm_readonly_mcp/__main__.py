import argparse
import logging

from .config import OAuthSettings, Settings
from .server import create_server


def main():
    parser = argparse.ArgumentParser(description="NotebookLM retrieval MCP (local stdio or OAuth HTTP)")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8771)
    args = parser.parse_args()
    try:
        oauth = OAuthSettings.from_env() if args.transport == "streamable-http" else None
        if not 1 <= args.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if args.transport == "stdio" and args.host != "127.0.0.1":
            raise ValueError("--host is only used with --transport streamable-http")
        settings = Settings.from_env()
    except (ValueError, OSError):
        parser.error(
            "Invalid local configuration. See docs/configuration.md; HTTP requires complete OAuth settings."
        )
    # Upstream error logging can contain source text or auth response details.
    for logger_name in ("notebooklm", "httpx", "httpcore"):
        logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)
    server = create_server(settings, oauth=oauth, host=args.host, port=args.port)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
