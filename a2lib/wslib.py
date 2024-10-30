"""An approved library for some Websocket frame/data management.

Leverages and exposes some approved components of the websocket library."""

from threading import Timer

from websockets import frames as _frames
from websockets.streams import StreamReader as _StreamReader

MAGIC_VAL = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# The following are the only allowed imports from the websockets library, aliased here so you _do not_
# need to import anything from the websocket library yourself. Use "wslib.Frame" or 
# "from wslib import Frame" instead. Documentation for these is found at 
# https://websockets.readthedocs.io/en/stable/reference/datastructures.html
#
# You'll need to install the websocket library using pip before you can use this.
Frame = _frames.Frame
Opcode = _frames.Opcode
Close = _frames.Close
CloseCode = _frames.CloseCode


def parse_frame(data: bytes, mask=False) -> Frame:
    """A simple method for parsing Websocket frames from binary data.
    
    This reaches into the internals of the websocket library so you don't have to.

    Returns None if the frame fails to parse for any reason.
    """
    sr = _StreamReader()
    sr.feed_data(data)
    parser = Frame.parse(sr.read_exact, mask=False)
    try:
        next(parser)
    except StopIteration as si:
        return si.value
    
def parse_close(frame: Frame) -> Close:
    """Parses Websocket Close data from an already parsed Frame object.
    
    Returns `None` if the frame is not a close frame."""
    if not frame.opcode == Opcode.CLOSE:
        return None
    return Close.parse(frame.data)
    
def serialize_frame(frame: Frame, mask: bool = True) -> bytes:  
    """Serializes a frame. Masks by default (required for client frames)."""      
    return frame.serialize(mask=mask)

def wrap_close(close: Close) -> bytes:
    """Wraps a Close object with the appropriate frame."""
    return Frame(Opcode.CLOSE, close.serialize())