import socket
from datetime import datetime, timezone

class WebServer:
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

            # generate response body
            response_body = "<html><body><h1>It Works! from homebrew web server...</h1></body></html>"

            # generate response line
            response_line = "HTTP/1.1 200 OK\r\n"

            # generate response header
            response_header = ""
            response_header += f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
            response_header += "Host: HomebrewWebServer/0.1\r\n"
            response_header += f"Content-length: {len(response_body.encode())}\r\n"
            response_header += "Connection: Close\r\n"
            response_header += "Content-Type: text/html\r\n"

            # generate whole response
            response = (response_line + response_header + "\r\n" + response_body).encode()

            # send response to the client
            client_socket.send(response)

            # end the connection
            client_socket.close()

        finally:
            print("=== stop server ===")


if __name__ == "__main__":
    server = WebServer()
    server.serve()