import argparse
import os
import random
import select
import signal
import socket
import sys
import time
import traceback
from base64 import b64encode
from hashlib import sha1
from http import HTTPStatus
from threading import Thread
from collections import defaultdict

import a2lib.httplib as httplib
import a2lib.wslib as wslib
from a2lib.consolelib import print_above_prompt
from a2lib.main_thread_waker import MainThreadWaker, WakingMainThread


class WebSocketClient:

    def __init__(self, host, port, role, time_out = 20.0, verbose=False):
        self.host = host
        self.port = port
        self.role = role
        self.time_out = time_out
        self.verbose = verbose
        self.socket = None
        self.connected = False
        self.recv_thread = None
        self.send_thread = None
        MainThreadWaker.register()

        

    def log(self, message):
        if self.verbose:
            print_above_prompt(message)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.time_out)

        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.handshake(self.role)
            self.log(f"Connected to {self.host}:{self.port}")

            if self.role == "consumer":
                self.recv_thread = Thread(target=self.receive_message)
                self.recv_thread.start()
            elif self.role == "producer":
                self.send_thread = Thread(target=self.send_message)
                self.send_thread.start()
            elif self.role == "both":
                self.recv_thread = Thread(target=self.receive_message)
                self.recv_thread.start()
                self.send_thread = Thread(target=self.send_message)
                self.send_thread.start()
        except Exception as e:
            self.log(f'Fail to connect: {e}')
            self.close(self.socket)

    def generate_websocket_key(self):
        return b64encode(os.urandom(16)).decode('utf-8')
    
    def handshake(self, path):
        key = self.generate_websocket_key()
        header = defaultdict(str, {
            "Host": f"{self.host}:{self.port}",
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": key,
            "Sec-WebSocket-Version": "13"
        })
        request = httplib.HttpRequest("GET", f"/{path}", header)
        self.socket.sendall(bytes(request))

        response = httplib.get_http_response(self.socket)
        self.log(f"Handshake response: {response}\r\n")

        if response.status == 101 and response.headers.get("Upgrade") == "websocket" and response.headers.get("Connection") == "Upgrade":
            accept_key = self.calculate_accept_key(key)
            if response.headers.get("Sec-WebSocket-Accept").encode() == accept_key:
                self.connected = True
                self.log("Handshake successful, connection upgraded to WebSocket.\r\n")
            else:
                self.log("Invalid Sec-WebSocket-Accept key in handshake response.\r\n")
        else:
            self.log("Invalid handshake response.\r\n")
    

    def calculate_accept_key(self, key):
        magic_value = wslib.MAGIC_VAL.decode('utf-8')
        sha1_value = sha1((key + magic_value).encode('utf-8'))
        return b64encode(sha1_value.digest())
    

    def receive_message(self):
        while self.connected:
            try:
                data = self.socket.recv(httplib._RECV_BUFFER_SIZE)
                if not data:
                    self.send_close()
                    break
                frame = wslib.parse_frame(data)
                if frame is None:
                    self.log("Failed to parse frame")
                    continue
                self.handle_frame(frame)
                
            except (KeyboardInterrupt):
                self.log("User request to close the connection.")
                self.send_close()
            except Exception as e:
                self.log(f"Receive error: {e}")
                self.send_close()
                break
    
    def handle_frame(self, frame: wslib.Frame):
        if frame.opcode == wslib.Opcode.PING:
            self.log(f"Received PING frame: {frame} and the data is: {frame.data}\r\n")
            self.send_pong(frame)
        elif frame.opcode == wslib.Opcode.PONG:
            self.log(f"Recieved PONG frame: {frame.data}\r\n")
        elif frame.opcode == wslib.Opcode.BINARY:
            self.log(f"Received binary frame: {frame.data}\r\n")
        elif frame.opcode == wslib.Opcode.TEXT:
            self.log(f"Received text frame: {frame.data.decode('utf-8')}\r\n")
        elif frame.opcode == wslib.Opcode.CLOSE:
            close = wslib.parse_close(frame)
            if close:
                self.log(f"Received close frame: {close.reason}\r\n")
                self.send_close(close)
            self.connected = False 
            MainThreadWaker.wake_main_thread()
    
    def send_pong(self, frame: wslib.Frame):
        pong_frame = wslib.Frame(opcode=wslib.Opcode.PONG, data = frame.data)
        data = wslib.serialize_frame(pong_frame, mask=True)
        self.log(f"Send back to server: {pong_frame}\r\n\r\n")
        self.socket.sendall(data)

    def send_message(self):
        while self.connected:
            try:
                message = input("\r\nEnter message: ")
                if message.lower() == "ping":
                    self.send_ping()
                elif message.lower() == "close":
                    self.send_close()
                else:
                    message_encoded = message.encode('utf-8')
                    frame_data = wslib.Frame(opcode = wslib.Opcode.TEXT, data = message_encoded)
                    data = wslib.serialize_frame(frame_data, mask=True)
                    self.socket.sendall(data)
            except (KeyboardInterrupt, EOFError):
                self.log("User request to close the connection.")
                self.send_close()
            except Exception as e:
                self.log(f"Exception: {e}")
                self.send_close()
            
    def send_ping(self):
        ping_frame = wslib.Frame(opcode=wslib.Opcode.PING, data = b"keep-alive")
        data = wslib.serialize_frame(ping_frame, mask=True)
        self.socket.sendall(data)
    
    def send_close(self, close_obj=None):
        if not close_obj:
            close_obj = wslib.Close(code = wslib.CloseCode.NORMAL_CLOSURE, reason = "Normal closure")
        close_frame = wslib.Frame(opcode = wslib.Opcode.CLOSE, data = close_obj.serialize())
        data = wslib.serialize_frame(close_frame, mask=True)
        try:
            self.log(f"Client send back close frame to server: {close_frame}, the data is: {data}")
            self.socket.sendall(data)
        except Exception as e:
            self.log(f"Error sending close frame: {e}")
        self.close(self.socket)
    
    def close(self, socket):
        socket.close()
        self.connected = False
        self.log("Connection closed")

            

def main():
    parser = argparse.ArgumentParser(description="WebSocket chat client.")
    parser.add_argument('host', type=str,
                        help="the port to bind to. Setting to 0 will randomly assign.")
    parser.add_argument('port', type=int,
                        help="the port to bind to. Setting to 0 will randomly assign.")
    parser.add_argument('role', type=str, choices=['producer', 'consumer', 'both'],
                        help="the role that the client should take: 'producer', 'consumer', or 'both'.")
    parser.add_argument('-v', '--verbose', action="store_true",
                        help="whether to print_above_prompt verbose output. Defaults to false.")
    parser.add_argument('-t', '--timeout', type=float, default=20.0,
                        help="How long to wait for responses from the server.")
    args = parser.parse_args()

    # See assignment description and main_thread_waker_example.py for details
    # on how to use this if you need it. It can stay here harmlessly until you
    # decide if/how you do!
    MainThreadWaker.register()

    client = WebSocketClient(args.host, args.port, args.role, verbose = True)

    try:
        client.connect()
    except WakingMainThread:
        print("main thread was woken up.")

    #print("\r\nExiting successfully.")


if __name__ == "__main__":
    main()
