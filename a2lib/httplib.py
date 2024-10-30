import socket
from collections import defaultdict
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, DefaultDict, Optional, Union

# Need to keep the buffer size small to allow for proper buffering of data over the wire.
# See https://docs.python.org/3/library/socket.html#socket.socket.recv.
_RECV_BUFFER_SIZE = 4096


class HttpMessage:
    version: str = "HTTP/1.1"
    headers: DefaultDict[str, str] = field(default_factory=lambda: defaultdict(str))
    body: Union[str, bytes, None] = None

    def __init__(self, headers: DefaultDict[str, str] = {}, body=None):
        self.headers = headers
        self.body = body
    
    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, data):
        self._body = data
        if self._body:
            self.headers["Content-Length"] = len(self._body)
        elif 'Content-Length' in self.headers:
            del self.headers['Content-Length']

    def _header_repr(self):
        return ""

    def __bytes__(self):
        repr = self._header_repr()
        for (name, value) in self.headers.items():
            repr += f'{name}: {value}\r\n'
        repr += '\r\n'

        if type(self.body) == bytes:
            repr = repr.encode()
            repr += self.body
            return repr
        else:
            if self.body:
                repr += self.body
            return repr.encode()
    
    def encode(self):
        return self.__bytes__()
    
    def serialize(self):
        return self.__bytes__()

class HttpRequest(HttpMessage):
    method: str
    url: str

    def __init__(self, method: str, url: str, headers: DefaultDict[str, str] = {},
                 body: Union[str, bytes] = None):
        self.method = method
        self.url = url
        super().__init__(headers, body)

    def __repr__(self):
        body_repr = f'<{len(self.body)} bytes>' if self.body else "None" 
        return f'HttpRequest(method={self.method}, url={self.url}, headers={self.headers}, body={body_repr})'
    

    def _header_repr(self):
        return f'{self.method} {self.url} {self.version}\r\n'
        
class HttpResponse(HttpMessage):
    status: HTTPStatus = HTTPStatus.OK
    msg: str = ""
    
    def __init__(self, status, msg="", headers: DefaultDict[str, str] = {},
                 body: Union[str, bytes] = None):
        self.status = status
        self.msg = msg
        super().__init__(headers, body)

    def __repr__(self):
        body_repr = f'<{len(self.body)} bytes>' if self.body else "None" 
        return f'HttpResponse(status={self.status}, headers={self.headers}, body={body_repr})'

    def _header_repr(self):
        return  f'{self.version} {self.status}{" " + self.msg if self.msg else ""}\r\n'
    

def get_http_request(socket: socket.socket) -> HttpRequest:
    data = socket.recv(_RECV_BUFFER_SIZE)
    header_end = data.find(b'\r\n\r\n')
    while header_end == -1:
        data = socket.recv(_RECV_BUFFER_SIZE)
        header_end = data.find(b'\r\n\r\n')

    (header_data, body) = (data[:header_end].decode(), data[header_end+4:])

    lines = header_data.strip().split('\r\n')
    (method, url, version) = lines[0].split()

    headers = defaultdict(str)
    for line in lines[1:]:
            (name, value) = line.split(":", 1)
            headers[name] = value.strip()

    if 'Content-Length' in headers: 
        while len(body) < int(headers['Content-Length']):
            body += socket.recv(_RECV_BUFFER_SIZE)

    return HttpRequest(method, url, version, headers, body)

def get_http_response(socket: socket.socket) -> HttpResponse:
    data = socket.recv(_RECV_BUFFER_SIZE)
    header_end = data.find(b'\r\n\r\n')
    while header_end == -1:
        data = socket.recv(_RECV_BUFFER_SIZE)
        header_end = data.find(b'\r\n\r\n')

    (header_data, body) = (data[:header_end].decode(), data[header_end+4:])

    lines = header_data.strip().split('\r\n')
    status_comps = lines[0].split(maxsplit=2)
    if len(status_comps) == 3:
        (_, status, msg) = status_comps
    else:
        (_, status) = status_comps
        msg = ""
    status = HTTPStatus(int(status))

    headers = defaultdict(str)
    for line in lines[1:]:
            (name, value) = line.split(":", 1)
            headers[name] = value.strip()

    if 'Content-Length' in headers: 
        while len(body) < int(headers['Content-Length']):
            body += socket.recv(_RECV_BUFFER_SIZE)

    return HttpResponse(status, msg, headers, body)
