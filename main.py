import socket
from email.utils import formatdate


def serve_forever(f, *args, **kwargs):
    """
    Runs a function forever in a loop.
    """
    while True:
        f(*args, **kwargs)


class TCPServer:
    def __init__(self, host="127.0.0.1", port=7777):
        self.host = host
        self.port = port

    def accept_and_send(self, socket):
        """
        Accepts incoming connection to the socket and sends back data.
        """
        (conn, addr) = socket.accept()
        print("Connected at %s on %s" % addr)
        data = conn.recv(1024)
        response = self.handle_request(data)
        conn.sendall(response)
        conn.close()

    def handle_request(self, data):
        return data

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # SO_REUSEADDR allow reuse of local addresses
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            s.bind((self.host, self.port))
            s.listen(5)
            print("Listening at %s on %s" % s.getsockname())

            serve_forever(self.accept_and_send, s)


class HTTPServer(TCPServer):
    def handle_request(self, data):
        """
        Handles incoming data and returns a response.
        """
        response = "\r\n".join(
            [
                "HTTP/1.1 200 OK",
                "Content-Type: text/html; charset=UTF-8",
                "Date: " + formatdate(timeval=None, localtime=False, usegmt=True),
                "",
                "Body",
            ]
        )
        return bytes(response, "utf-8")


if __name__ == "__main__":
    server = HTTPServer()
    server.start()