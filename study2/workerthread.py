import os 
import re
import textwrap
import traceback
from datetime import datetime, timezone
from pprint import pformat
from socket import socket
from threading import Thread
from typing import Tuple, Optional

class WorkerThread(Thread):

    # 実行可能ファイルを含むディレクトリ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 静的に配信するファイルを含むディレクトリ
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    # ファイル拡張子とMIMEタイプの対応
    MIME_TYPES = {
        "html": "text/html",
        "css": "text/css",
        "png": "image/png",
        "jpg": "image/jpg",
        "gif": "image/gif",
    }

    def __init__(self, client_socket, address: Tuple[str, int]):
        super().__init__()

        self.client_socket = client_socket
        self.client_address = address

    def run(self) -> None:
        """
        クライアントと接続済みのsocketを引数として受け取り、
        リクエストを処理してレスポンスを送信する
        """

        try:

            # クライアントから送られてきたデータを取得する
            request = self.client_socket.recv(4096)

            # クライアントから送られてきたファイルを書き出す
            with open("server_recv.txt", "wb") as f:
                f.write(request)

            # HTTPリクエストをパースする
            method, path, http_version, request_header, request_body = self.parse_http_request(request)

            response_body: bytes
            content_type: Optional[str]
            response_line: str
            # pathがnowのときは、現在時刻を表示するHTMLを生成する
            if path == "/now":
                html = f"""
                    <html>
                        <body>
                            <h1>Now: {datetime.now()}</h1>
                        </body>
                    </html>
                """
                response_body = textwrap.dedent(html).encode()

                # Content-Typeを指定
                content_type = "text/html"

                # レスポンスラインを生成
                response_line = "HTTP/1.1 200 OK\r\n"

            # pathが/show_requestのときは、HTTPリクエストの内容を表示するHTMLを生成する
            elif path == "/show_request":
                html = f"""\
                    <html>
                        <body>
                            <h1>Request Line:</h1>
                            <p>
                                {method} {path} {http_version}
                            </p>
                            <h1>Headers:</h1>
                            <pre>{pformat(request_header)}</pre>  # ←これで辞書として見やすく表示される
                            <h1>Body:</h1>
                            <pre>{request_body.decode("utf-8", "ignore")}</pre>
                        </body>
                    </html>
                    """
                
                response_body = textwrap.dedent(html).encode()

                # Content-Typeを指定
                content_type = "text/html"

                # レスポンスラインを生成
                response_line = "HTTP/1.1 200 OK"

            # pathがそれ以外の時は、性的ファイルからレスポンスを生成する
            else:
                try:
                    # ファイルからレスポンスボディを生成
                    response_body = self.get_static_file_content(path)

                    # Content-Typeを指定
                    content_type = None

                    # レスポンスラインを生成
                    response_line = "HTTP/1.1 200 OK\r\n"
                
                except OSError:
                    # ファイルが見つからなかった場合は404を返す
                    response_body = b"<html><body><h1>404 Not Found</h1></body></html>"
                    content_type = "text/html"
                    response_line = "HTTP/1.1 404 Not Found\r\n"

            # レスポンスヘッダーを生成（content_typeを引数として渡す）
            response_header = self.build_response_header(path, response_body, content_type)

            # レスポンス全体を生成するs
            response = (response_line + response_header + "\r\n").encode() + response_body

            # クライアントレスポンスを送信する
            self.client_socket.send(response)


        except Exception:
            # リクエストの処理中に例外が発生した場合はコンソールにエラーログを出力し、
            # 処理を続行する
            print("=== Worker: リクエストの処理中にエラーが発生しました ===")
            traceback.print_exc()

        finally:
            # 例外が発生した場合も、発生しなかった場合も、TCP通信のcloseは行う
            print(f"=== Worker: クライアントとの通信を終了します remote_address: {self.client_address} ===")
            self.client_socket.close()




    def parse_http_request(self, request: bytes) -> Tuple[str, str, str, dict, bytes]:
        """
        HTTPリクエストを
        1. method: str
        2. path: str
        3. http_version: str
        4. request_header: dict  # ←戻り値の型を変更
        5. request_body: bytes
        に分割/変換する
        """

        # リクエスト全体を以下に解析する:
        # 1. リクエスト行（最初の行）
        # 2. リクエストヘッダー（2行目から空行まで）
        # 3. リクエストボディ（空行から最後まで）
        # にパースする
        request_line, remain = request.split(b"\r\n", maxsplit=1)
        request_header, request_body = remain.split(b"\r\n\r\n", maxsplit=1)

        # リクエストラインを文字列に変換してパースする
        method, path, http_version = request_line.decode().split(" ")

        # リクエストヘッダーを辞書にパースする
        headers = {}
        for header_row in request_header.decode().split("\r\n"):
            key, value = re.split(r": *", header_row, maxsplit=1)
            headers[key] = value

        return method, path, http_version, headers, request_body  # ←辞書を返す
    
    def get_static_file_content(self, path: str) -> bytes:
        """
        リクエストpathからstaticファイルの内容を取得する
        """

        # パスの先頭の/を削除し、相対パスとして保持
        relative_path = path.lstrip("/")
        
        # ファイルパスを取得
        static_file_path = os.path.join(self.STATIC_ROOT, relative_path)

        with open(static_file_path, "rb") as f:
            return f.read()
        
    def build_response_header(self, path: str, response_body: bytes, content_type: Optional[str] = None) -> str:
        """
        レスポンスヘッダーを構築する
        """
        # Content-Typeが指定されていない場合はpathから特定する
        if content_type is None:
            # パスから拡張子を取得
            if "." in path:
                ext = path.rsplit(".", maxsplit=1)[-1]
            else:
                ext = ""
            
            # 拡張子からMIMEタイプを取得
            # 拡張子が不明な場合はoctet-streamを使用
            content_type = self.MIME_TYPES.get(ext, "application/octet-stream")

        # レスポンスヘッダーを生成
        response_header = ""
        response_header += f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
        response_header += "Host: HomebrewWebServer/0.1\r\n"
        response_header += f"Content-Length: {len(response_body)}\r\n"
        response_header += "Connection: Close\r\n"
        response_header += f"Content-Type: {content_type}\r\n"

        return response_header

