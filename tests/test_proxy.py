# pylint: disable=missing-function-docstring
"""Test proxy."""
import http.server
import socketserver
import threading
import pytest


class Proxy(http.server.SimpleHTTPRequestHandler):
    """Proxy server for mock."""
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Proxy server received request')


@pytest.fixture(scope="session")
def proxy_server():
    port = 9999  # 确保这个端口在你的系统上是可用的
    with socketserver.TCPServer(("", port), Proxy) as httpd:
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
    yield f'http://localhost:{port}'
    httpd.shutdown()


def test_example(proxy_server):  # pylint: disable=redefined-outer-name
    print(f"Testing with proxy server at: {proxy_server}")
    assert proxy_server == 'http://localhost:9999'
    # 你的测试逻辑...
