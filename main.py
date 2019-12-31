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
        (conn, addr) = socket.accept()
        print("Connected at %s on %s" % addr)
        data = conn.recv(1024)
        response = self.handle_request(data)
        conn.sendall(response)
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

    def handle_501_HTTP(self):
        """Handles 501 Not Implemented response."""
        body = """
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="X-UA-Compatible" content="ie=edge">
                <title>Not implemented</title>
            </head>
            <body>
                <h1>Not implemented
            </body>
        </html>
        """
        response_line = self.make_response_line(status_code=501)
        headers = self.make_response_headers()
        response = "\r\n".join([response_line, headers, "", body])

        return bytes(response, "utf-8")

    def handle_GET(self):
        """Handles GET request."""
        body = "Handle GET body."
        response_line = self.make_response_line()
        headers = self.make_response_headers(
            more_headers={"Content-Length": len(bytes(body, "utf-8"))}
        )
        response = "\r\n".join([response_line, headers, "", body])

        return bytes(response, "utf-8")

    def handle_OPTIONS(self):
        """Handles OPTIONS request."""
        response_line = self.make_response_line()
        headers = self.make_response_headers(more_headers={"Allow": "GET, OPTIONS"})
        response = "\r\n".join([response_line, headers, ""])

        return bytes(response, "utf-8")

    def handle_request(self, data):
        """Handles incoming data and returns a response."""
        request_method = self.parse_request(data)
        request_handler = getattr(self, f"handle_{request_method}", None)

        return request_handler() if request_handler else self.handle_501_HTTP()

    def make_response_headers(self, mime_type="text/html; charset=UTF-8", more_headers=None):
        """Constructs response headers.
        The `more_headers` is a dict to send additional headers.
        """
        headers = {
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
        request_line_words = head(lines).split(" ")
        return head(request_line_words)


if __name__ == "__main__":
    server = HTTPServer()
    server.start()
