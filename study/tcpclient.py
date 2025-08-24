import socket

class TCPClient:
    def request(self):
        print("=== start a client ===")

        try:
            # create a socket
            client_socket = socket.socket()
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # connect the server
            print("=== connect the server ===")
            client_socket.connect(("localhost", 80))
            print("=== complete connecting the server ===")

            # retrieve requests to be sent to the server from the file
            with open("client_send.txt", "rb") as f:
                request = f.read()

            # send a request to eh server
            client_socket.send(request)

            # wait for a response from the server and retrieve it 
            response = client_socket.recv(4096)

            # withe the response content to the file
            with open("client_recv.txt", "wb") as f:
                f.write(response)

            # end the connection
            client_socket.close()

        finally:
            print("=== end the client ===")

if __name__ == "__main__":
    client = TCPClient()
    client.request()