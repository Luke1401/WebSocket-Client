#!/usr/bin/env python

import argparse
import asyncio
import sys
from asyncio.exceptions import CancelledError, TimeoutError
from http import HTTPStatus
from typing import List

import aioconsole
import websockets
from websockets.exceptions import ConnectionClosed

_consumers: List[websockets.WebSocketClientProtocol] = []

async def _post_message(msg: str, source: websockets.WebSocketClientProtocol):
    global _consumers
    for consumer in _consumers:
        if not source or consumer != source:
            await consumer.send(msg)


async def _handle_session(websocket: websockets.WebSocketServerProtocol):
    print(f'{websocket.remote_address}: Client connected as {websocket.path}')

    try:
        if websocket.path in ["/consumer", "/both"]:
            _consumers.append(websocket)
        
        if websocket.path in ["/producer", "/both"]:
            await _handle_producer_session(websocket)
        else:
            await websocket.wait_closed()
            print(f"{websocket.remote_address}: Consumer closed.")

    except TimeoutError:
        print(f"{websocket.remote_address}: Client timed out!")
    except ConnectionClosed as cc:
        closer = "Client" if cc.rcvd and cc.rcvd_then_sent else "Server"
        print(f"{websocket.remote_address}: {closer} closed the connection.")
    except CancelledError:
        print(f"{websocket.remote_address}: Connection was cancelled.")
    except Exception as e:
        print(e)
    finally:
        if websocket in _consumers:
            _consumers.remove(websocket)
        if not websocket.closed:
            await websocket.close(reason="")

async def _handle_producer_session(websocket: websockets.WebSocketServerProtocol):
    closing = False
    while not closing:
        msg = await websocket.recv()
        if isinstance(msg, str):
            print(f'Received message from {websocket.remote_address}.')
            msg = f'{websocket.remote_address[:2]}: {msg}'
            await _post_message(msg, websocket)
        else:
            await websocket.send("Server only accepts text data! Closing connection.")
            closing = True

async def _process_request(path, request_headers):
    print(path, request_headers)
    if path not in ["/producer", "/consumer", "/both"]:
        msg = "Improper route. Must be one of \"/producer\", \"/consumer\", or \"/both\""
        return (HTTPStatus.BAD_REQUEST, {'Content-Length': len(msg)}, msg.encode())
    return None


async def main(argv):
    parser = argparse.ArgumentParser(description="Chat server.")
    parser.add_argument('port', type=int,
                        help="the port to bind to. Setting to 0 will randomly assign.")
    parser.add_argument('-p', '--ping-interval', type=float, default=5.0,
                    help="the ping interval in seconds. Defaults to 5.0. A zero or negative value disables pinging.")
    parser.add_argument('-t', '--timeout', type=float, default=20.0,
                        help="the connecion timeout in seconds. Defaults to 20.0.")

    args = parser.parse_args(argv)
    if args.ping_interval <= 0.0:
        args.ping_interval = None

    async with websockets.serve(_handle_session, '', args.port, 
                                process_request = _process_request,
                                ping_interval = args.ping_interval,
                                ping_timeout= args.timeout,
                                server_header = "test_chat_server/1.0"):
        print(
            f'Started chat server on port {args.port}. Accepting connections...')

        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("Finished shutting down server. Adios!")
