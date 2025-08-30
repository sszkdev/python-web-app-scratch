import os 
import traceback
from datetime import datetime
from socket import socket
from threading import Thread
from typing import Tuple

class WorkerThread(Thread):

    # 実行可能ファイルを含むディレクトリ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 静的に配信するファイルを含むディレクトリ
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

    # ファイル拡張子とMIMEタイプの対応
    MIME_TYPE = {
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
