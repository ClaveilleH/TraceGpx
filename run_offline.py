#!/usr/bin/env python3
from __future__ import annotations

import argparse
import functools
import http.server
import socket
import sys
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
START_PAGE = "tracegpx.html"


class TraceGpxHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".css": "text/css",
        ".js": "text/javascript",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".webmanifest": "application/manifest+json",
    }

    def translate_path(self, path: str) -> str:
        if path.split("?", 1)[0] in ("", "/"):
            path = f"/{START_PAGE}"
        return super().translate_path(path)

    def end_headers(self) -> None:
        path = self.path.split("?", 1)[0]
        if path.endswith("service-worker.js"):
            self.send_header("Service-Worker-Allowed", "/")
            self.send_header("Cache-Control", "no-cache")
        elif path in ("", "/") or path.endswith(".html"):
            self.send_header("Cache-Control", "no-cache")
        else:
            self.send_header("Cache-Control", "public, max-age=604800")
        super().end_headers()


class ThreadingServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True


def pick_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 50):
        if port_available(host, port):
            return port
    raise RuntimeError(f"No available port found from {preferred} to {preferred + 49}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run TraceGPX locally without requiring an internet connection."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address. Use 0.0.0.0 for LAN access.")
    parser.add_argument("--port", type=int, default=8000, help="Preferred port.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    port = pick_port(args.host, args.port)
    handler = functools.partial(TraceGpxHandler, directory=str(ROOT))
    url = f"http://localhost:{port}/{START_PAGE}"

    try:
        with ThreadingServer((args.host, port), handler) as server:
            print("TraceGPX offline server")
            print(f"Serving: {ROOT}")
            print(f"URL:     {url}")
            print("Stop:    Ctrl+C")
            print("")
            print("Note: map tiles must already be cached/prepared for offline use.")
            if args.host == "0.0.0.0":
                print("LAN mode: open the same port from this machine's local IP.")
            if not args.no_browser:
                webbrowser.open(url)
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
