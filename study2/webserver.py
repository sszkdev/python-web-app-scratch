import os 
import socket
import traceback
from datetime import datetime, timezone

class WebServer:

    # ファイル拡張子とMIMEタイプの対応
    MIME_TYPE = {
        "html": "text/html",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpg",
        "gif": "image/gif",
    }

    # 実行可能ファイルを含むディレクトリ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 静的に配信するファイルを含むディレクトリ
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    def serve(self):
        print("=== start server ===")
        print("=== If you want to stop the server, press Ctrl + c ===")

        try:
            # ソケットを作成
            server_socket = self.create_server_socket()
            
            while True:
                # 外部からの接続を待ち、受信したら確立する
                print("=== wait a conection from client ===")
                (client_socket, address) = server_socket.accept()
                print(f"=== client connection complete, remote_address: {address} ===")

                try:
                    # クライアントと通信し、リクエストを処理
                    self.handle_client(client_socket) 
                
                except Exception:
                    # リクエスト処理中に例外が発生した場合は、エラーログをコンソールに出力して処理を続行
                    print("=== an error occurred while processing your request. ===")
                    traceback.print_exc()

                finally:
                    # TCP通信は常に閉じる
                    client_socket.close()

        finally:
            print("=== stop server ===")

    def create_server_socket(self) -> socket:
        """
        外部からの接続を待つためのserver_socketを作成
        """
        # ソケットを作成
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # ソケットをlocalhost:8080に割り当て
        server_socket.bind(("localhost", 8080))
        server_socket.listen(10)

        return server_socket
    
    def handle_client(self, client_socket: socket) -> None:
        """
        クライアントと接続されたソケットを引数として受け取り、リクエストを処理してレスポンスを送信する
        """

        # クライアントから送信されたデータを取得
        request = client_socket.recv(4096)

        # クライアントから送信されたデータをファイルに書き込み
        with open("server_recv.txt", "wb") as f:
            f.write(request)

        # リクエスト全体を以下に解析する:
        # 1. リクエスト行（最初の行）
        # 2. リクエストヘッダー（2行目から空行まで）
        # 3. リクエストボディ（空行から最後まで）
        request_line, remain = request.split(b"\r\n", maxsplit=1)
        request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

        # リクエスト行を解析
        method, path, http_version = request_line.decode().split(" ")

        # パスの先頭の/を削除し、相対パスとして保持
        relative_path = path.lstrip("/")
        
        # ファイルパスを取得
        static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

        # ファイルからレスポンスボディを生成
        try: 
            with open(static_file_path, "rb") as f:
                response_body = f.read()

            # レスポンス行を生成
            response_line = "HTTP/1.1 200 OK\r\n"
        except OSError:
            # ファイルが見つからない場合は404を返す
            response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
            response_line = "HTTP/1.1 404 Not Found\r\n"

        # ヘッダー作成のためにContent-Typeを取得
        # パスから拡張子を取得
        if "." in path:
            ext = path.rsplit(".", maxsplit=1)[-1]
        else:
            ext = ""
        
        # 拡張子からMIMEタイプを取得
        # 拡張子が不明な場合はoctet-streamを使用
        content_type = self.MIME_TYPE.get(ext, "application/octet-stream")

        # レスポンスヘッダーを生成
        response_header = ""
        response_header += f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
        response_header += "Host: HomebrewWebServer/0.1\r\n"
        response_header += f"Content-length: {len(response_body)}\r\n"
        response_header += "Connection: Close\r\n"
        response_header += f"Content-Type: {content_type}\r\n"

        # 完全なレスポンスを生成
        response = (response_line + response_header + "\r\n").encode() + response_body

        # レスポンスをクライアントに送信
        client_socket.send(response)


if __name__ == "__main__":
    server = WebServer()
    server.serve()