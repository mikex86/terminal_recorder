import os
import sys
import struct
import pyte
import time
import pyglet
from pyglet.window import key

DATA_TYPE_SIZE_CHANGE = 0
DATA_TYPE_STDIN = 1
DATA_TYPE_STDOUT = 2

def read_from_log(log_file):
    data_type_bytes = log_file.read(1)
    if not data_type_bytes:
        return None, None, None

    data_type = struct.unpack("B", data_type_bytes)[0]
    timestamp = struct.unpack("q", log_file.read(8))[0]
    length = struct.unpack("q", log_file.read(8))[0]
    data = log_file.read(length)

    return data_type, timestamp, data

class TerminalProvider:
    def __init__(self, log_filename):
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.Stream(self.screen)

        self.log_file = open(log_filename, "rb")
        self.prev_timestamp = None
        self.window_resize_callback = None

    def get_terminal_size(self):
        return self.screen.columns, self.screen.lines

    def get_terminal_context(self):
        return self.screen.display

    def process_next_event(self):
        data_type, timestamp, data = read_from_log(self.log_file)
        if data_type is None:
            return None

        if self.prev_timestamp is not None:
            delay = (timestamp - self.prev_timestamp) / 1000.0
        else:
            delay = 0
        self.prev_timestamp = timestamp

        if data_type == DATA_TYPE_SIZE_CHANGE:
            rows, cols = struct.unpack("HH", data)
            print(f"Resizing to {rows}x{cols}")
            self.screen.resize(rows, cols)
            if self.window_resize_callback:
                self.window_resize_callback()
        elif data_type == DATA_TYPE_STDIN:
            pass  # User input is not needed for playback
        elif data_type == DATA_TYPE_STDOUT:
            self.stream.feed(data.decode('utf-8', 'ignore'))

        return delay

def main(log_filename):
    term_prov = TerminalProvider(log_filename)

    terminal_width, terminal_height = term_prov.get_terminal_size()
    font_size = 16
    window = pyglet.window.Window(
        width=int(terminal_width * font_size * 0.75),
        height=(terminal_height + 2) * font_size,
        caption="Terminal Playback"
    )

    labels = []
    for i in range(terminal_height):
        label = pyglet.text.Label(
            text='',
            font_name='Consolas',
            font_size=font_size,
            x=0,
            y=window.height - i * font_size,
            anchor_x='left',
            anchor_y='top'
        )
        labels.append(label)

    def on_window_resize():
        terminal_width, terminal_height = term_prov.get_terminal_size()
        window_width = int(terminal_width * font_size * 0.65)
        window_height = int((terminal_height + 1) * font_size)
        window.set_size(window_width, window_height)

        del labels[:]
        for i in range(terminal_height):
            label = pyglet.text.Label(
                text='',
                font_name='Consolas',
                font_size=font_size,
                x=0,
                y=window.height - (i - 2) * font_size,
                anchor_x='left',
                anchor_y='top'
            )
            labels.append(label)

    term_prov.window_resize_callback = on_window_resize

    @window.event
    def on_draw():
        window.clear()
        lines = term_prov.get_terminal_context()
        for i, line in enumerate(lines):
            try:
                labels[i].text = line
            except ValueError:
                pass
            labels[i].draw()

    def update(dt):
        delay = term_prov.process_next_event()
        if delay is None:
            pyglet.app.exit()
            return
        pyglet.clock.schedule_once(update, delay)
        

    pyglet.clock.schedule_once(update, 0)
    pyglet.app.run()

    term_prov.log_file.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} log_filename")
        sys.exit(1)

    main(sys.argv[1])