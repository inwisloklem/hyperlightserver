import os
import mimetypes
import socket
from http.client import responses
from email.utils import formatdate

head = lambda xs: xs[0]


def serve_forever(f, *args, **kwargs):
    """Runs a function forever in a loop."""
    while True:
        f(*args, **kwargs)


class TCPServer:
    def accept_and_send(self, socket):
        """Accepts incoming connection to the socket and sends back data."""
        (conn, addr) = socket.accept()  # accept will block until a new client connects
        print("Connected at %s on %s" % addr)
        data = conn.recv(2048)
        response = self.handle_request(data)
        conn.sendall(response)  # inside repeatedly calls send
        conn.close()

    def handle_request(self, data):
        return data

    def start(self, host="127.0.0.1", port=4444):
        """Starts a hyperlightserver."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen(5)

            print("Listening at %s on %s" % s.getsockname())
            serve_forever(self.accept_and_send, s)


class HTTPServer(TCPServer):
    http_version = "HTTP/1.1"

    def handle_404_HTTP(self, request_uri=None):
        """Handles 404 Not found."""
        with open(".pages/404.html") as f:
            body = f.read()

        line = self.make_response_line(status_code=404)
        headers = self.make_response_headers(
            more_headers={"Content-Length": len(bytes(body, "utf-8"))}
        )
        response = "\r\n".join([line, headers, "", body])

        return bytes(response, "utf-8")

    def handle_501_HTTP(self, request_uri=None):
        """Handles 501 Not Implemented."""
        with open(".pages/501.html") as f:
            body = f.read()

        line = self.make_response_line(status_code=501)
        headers = self.make_response_headers(
            more_headers={"Content-Length": len(bytes(body, "utf-8"))}
        )
        response = "\r\n".join([line, headers, "", body])

        return bytes(response, "utf-8")

    def handle_GET(self, request_uri=None):
        """Handles GET request."""
        request_uri = request_uri.strip("/")

        if request_uri.startswith(".pages"):
            return self.handle_404_HTTP()

        filename = request_uri or "index.html"
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                body = f.read()

            line = self.make_response_line()
            headers = self.make_response_headers(
                mime_type=mimetypes.guess_type(filename)[0],
                more_headers={"Content-Length": len(body)},
            )
            response_except_body = "\r\n".join([line, headers, ""])

            return b"\r\n".join([bytes(response_except_body, "utf-8"), body])

        return self.handle_404_HTTP()

    def handle_OPTIONS(self, request_uri=None):
        """Handles OPTIONS request."""
        line = self.make_response_line()
        headers = self.make_response_headers(more_headers={"Allow": "GET, OPTIONS"})
        response = "\r\n".join([line, headers, ""])

        return bytes(response, "utf-8")

    def handle_request(self, data):
        """Handles incoming data and returns a response."""
        request = self.parse_request(data)
        handler = getattr(self, f"handle_{request['method']}", self.handle_501_HTTP)

        return handler(request_uri=request["uri"])

    def make_response_headers(self, mime_type="text/html; charset=UTF-8", more_headers=None):
        """Constructs response headers.
        The `more_headers` is a dict to send additional headers.
        """
        headers = {
            "Connection": "keep-alive",
            "Content-Type": mime_type,
            "Date": formatdate(timeval=None, localtime=False, usegmt=True),
        }

        if more_headers:
            headers.update(more_headers)

        return "\r\n".join([f"{k}: {v}" for k, v in headers.items()])

    def make_response_line(self, status_code=200):
        """Constructs response line from HTTP version, status code and message.

        HTTP version Status code Message
        HTTP/1.1     200         OK
        """
        return " ".join([self.http_version, str(status_code), responses[status_code]])

    def parse_request(self, data):
        """Parses request and returns a request method.

        Method URI HTTP version
        GET    /   HTTP/1.1
        """
        lines = str(data, "utf-8").split("\r\n")
        method, uri, _ = head(lines).split(" ")

        return {"method": method, "uri": uri}


if __name__ == "__main__":
    server = HTTPServer()
    server.start()
