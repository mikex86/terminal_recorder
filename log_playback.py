import time

import pyglet

from terminal_gui import TerminalGui
import struct
from typing import Optional

import pyte
from pyte import Screen, Stream

from terminal_provider import TerminalProvider


def read_from_log(log_file):
    data_type_bytes = log_file.read(1)
    if not data_type_bytes:
        return None, None, None

    data_type = struct.unpack("B", data_type_bytes)[0]
    timestamp = struct.unpack("q", log_file.read(8))[0]
    length = struct.unpack("q", log_file.read(8))[0]
    data = log_file.read(length)

    return data_type, timestamp, data


DATA_TYPE_SIZE_CHANGE = 0
DATA_TYPE_STDIN = 1
DATA_TYPE_STDOUT = 2


class LogTerminalProvider(TerminalProvider):

    def __init__(self, log_filename: str):
        self.pyte_screen: Optional[Screen] = None
        self.pyte_stream: Optional[Stream] = None
        self.log_file = open(log_filename, "rb")
        self.prev_timestamp = None
        self.virtual_stdin: bytes = b''
        self.update()

    def get_terminal_context(self) -> [str]:
        terminal_context = []
        for idx in range(self.pyte_screen.lines):
            line = self.pyte_screen.buffer[idx]
            terminal_context.append(line)
        return terminal_context

    def get_terminal_size(self) -> (int, int):
        return self.pyte_screen.columns, self.pyte_screen.lines

    def get_terminal_cursor_position(self) -> (int, int):
        cursor = self.pyte_screen.cursor
        return cursor.x, cursor.y

    def set_terminal_cursor_position(self, x: int, y: int):
        raise NotImplementedError("LogTerminalProvider is a read-only terminal provider. It wraps a recording.")

    def send_input(self, key: str):
        raise NotImplementedError("LogTerminalProvider is a read-only terminal provider. It wraps a recording.")

    def process_next_event(self):
        data_type, timestamp, data = read_from_log(self.log_file)
        if data_type is None:
            return -1

        if self.prev_timestamp is not None:
            delay = (timestamp - self.prev_timestamp) / 1000.0
        else:
            delay = 0
        self.prev_timestamp = timestamp

        if data_type == DATA_TYPE_SIZE_CHANGE:
            rows, cols = struct.unpack("HH", data)
            if self.pyte_screen is None:
                self.pyte_screen = pyte.Screen(cols, rows)
                self.pyte_stream = pyte.Stream(self.pyte_screen)
            self.pyte_screen.resize(rows, cols)
        elif data_type == DATA_TYPE_STDIN:
            self.virtual_stdin += data
        elif data_type == DATA_TYPE_STDOUT:
            # workaround because pyte doesn't support alternate screens
            xterm_str = data.decode('utf-8', 'ignore')
            if '\x1b[?1049l' in xterm_str:
                xterm_str = xterm_str.replace('\x1b[?1049l', '\x1b[2J\x1b[H')
            self.pyte_stream.feed(xterm_str)

        return delay

    def update(self):
        return self.process_next_event()

    def is_open(self) -> bool:
        return True

    def poll_virtual_stdin(self) -> Optional[bytes]:
        if len(self.virtual_stdin) == 0:
            return None
        stdin = self.virtual_stdin
        self.virtual_stdin = b''
        return stdin


if __name__ == '__main__':
    term_provider = LogTerminalProvider("terminal_log.bin")
    term_gui = TerminalGui('Terminal', term_provider, False)
    logical_time = 0
    start_time = time.time()

    def update():
        global logical_time
        delay = term_provider.update()

        if delay is None or delay == -1:
            pyglet.app.exit()

        logical_time += delay
        actual_time = time.time() - start_time

        delta = logical_time - actual_time
        if delta < 0:
            delta = 0

        pyglet.clock.schedule_once(lambda dt: update(), delta)


    pyglet.clock.schedule_once(lambda dt: update(), 0)

    pyglet.app.run()
