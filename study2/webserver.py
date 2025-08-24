import os 
import socket
from datetime import datetime, timezone

class WebServer:
    # directory containing excutable file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # directory contairing files to be delivered statically
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    def serve(self):
        print("=== start server ===")

        try:
            # create a socket
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # assign the socket to localhost:8080
            server_socket.bind(("localhost", 8080))
            server_socket.listen(10)

            # wait an external connection and establish when one is receive
            print("=== wait a conection from client ===")
            (client_socket, address) = server_socket.accept()
            print(f"=== client connection complete, remote_address: {address} ===")

            # retrieve the data sent from the client
            request = client_socket.recv(4096)

            # write the data sent from the client to the file
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            # Parse the entire request into
            # 1. Request line (first line)
            # 2. Request header (second line to blank line)
            # 3. Request body (blank line to )
            request_line, remain = request.split(b"\r\n", maxsplit=1)
            request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

            # parse request line
            method, path, http_version = request_line.decode().split(" ")

            # remove the leading / from the path and keep it as a relative path
            relative_path = path.lstrip("/")
            
            # get the file path
            static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

            # generate response body from file
            try: 
                with open(static_file_path, "rb") as f:
                    response_body = f.read()

                # generate response line
                response_line = "HTTP/1.1 200 OK\r\n"
            except OSError:
                # if file not found, return 404
                response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
                response_line = "HTTP/1.1 404 Not Found\r\n"

            # generate response header
            response_header = ""
            response_header += f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            response_header += "Host: HomebrewWebServer/0.1\r\n"
            response_header += f"Content-length: {len(response_body)}\r\n"
            response_header += "Connection: Close\r\n"
            response_header += "Content-Type: text/html\r\n"

            # generate whole response
            response = (response_line + response_header + "\r\n").encode() + response_body

            # send response to the client
            client_socket.send(response)

            # end the connection
            client_socket.close()

        finally:
            print("=== stop server ===")


if __name__ == "__main__":
    server = WebServer()
    server.serve()