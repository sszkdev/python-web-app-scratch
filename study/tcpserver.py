import socket

class TCPServer():
    def serve(self):
        print("=== start a server ===")

        try:
            # create socket
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # assign the socket to localhost:8080
            server_socket.bind(("localhost", 8080))
            server_socket.listen(10)

            # wait an external connection and establish when one is received
            print("=== wait a connection from client ===")
            (client_socket, address) = server_socket.accept()
            print(f"=== client connection complete, remote_address: {address} ===")

            # retrieve the data sent from client
            request = client_socket.recv(4096)

            # write data sent from client to a file
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            # retrieve the response data to be sent to the client from the file
            with open("server_send.txt", "rb") as f:
                response = f.read()
            
            # send response data to the client
            client_socket.send(response)

            # end the connection without response 
            client_socket.close()

        finally:
            print("=== shut down the server ===")



if __name__ == "__main__":
    server = TCPServer()
    server.serve()