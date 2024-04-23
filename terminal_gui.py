import time
from typing import Callable, List

import pyglet
import pyglet.graphics

from terminal_provider import TerminalProvider

key_xterm_mapping = {
    pyglet.window.key.ESCAPE: '\x1b',
    pyglet.window.key.F1: '\x1bOP',
    pyglet.window.key.F2: '\x1bOQ',
    pyglet.window.key.F3: '\x1bOR',
    pyglet.window.key.F4: '\x1bOS',
    pyglet.window.key.F5: '\x1b[15~',
    pyglet.window.key.F6: '\x1b[17~',
    pyglet.window.key.F7: '\x1b[18~',
    pyglet.window.key.F8: '\x1b[19~',
    pyglet.window.key.F9: '\x1b[20~',
    pyglet.window.key.F10: '\x1b[21~',
    pyglet.window.key.F11: '\x1b[23~',
    pyglet.window.key.F12: '\x1b[24~',
    pyglet.window.key.TAB: '\t'
}

motion_xterm_mapping = {
    pyglet.window.key.MOTION_UP: '\x1b[A',
    pyglet.window.key.MOTION_DOWN: '\x1b[B',
    pyglet.window.key.MOTION_LEFT: '\x1b[D',
    pyglet.window.key.MOTION_RIGHT: '\x1b[C',
    pyglet.window.key.MOTION_BACKSPACE: '\x7f',
    pyglet.window.key.MOTION_DELETE: '\x1b[3~',
}

COLORS = {
    "black": (0x00, 0x00, 0x00),
    "lightred": (0xFF, 0x00, 0x00),
    "lightgreen": (0x00, 0xFF, 0x00),
    "yellow": (0xFF, 0xFF, 0x00),
    "lightblue": (0x00, 0x00, 0xFF),
    "lightmagenta": (0xFF, 0x00, 0xFF),
    "lightcyan": (0x00, 0xFF, 0xFF),
    "highwhite": (0xFF, 0xFF, 0xFF),
    "grey": (0x80, 0x80, 0x80),
    "red": (0x80, 0x00, 0x00),
    "green": (0x00, 0x80, 0x00),
    "rown": (0x80, 0x80, 0x00),
    "blue": (0x00, 0x00, 0x80),
    "magenta": (0x80, 0x00, 0x80),
    "cyan": (0x00, 0x80, 0x80),
    "white": (0xC0, 0xC0, 0xC0)
}


def decode_term_color(color_str: str, is_bg: bool) -> (int, int, int):
    if color_str == "default":
        if is_bg:
            return 0x00, 0x00, 0x00
        else:
            return 0xFF, 0xFF, 0xFF

    color_lookup_result = COLORS.get(color_str, None)

    if color_lookup_result is not None:
        return color_lookup_result

    def hex_to_rgb(hex_value: str) -> (int, int, int):
        return tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))

    return hex_to_rgb(color_str)


is_running = False
LINE_SPACING_FACTOR = 1.7


class FpsDisplay:

    def __init__(self):
        self.label = pyglet.text.Label(text='', font_name='Arial', font_size=12, x=0, y=0)
        self.label.color = (0, 255, 255)
        self.last_time = 0
        self.frame_count = 0
        self.current_fps = 0

    def draw(self, width: int, height: int):
        current_time = time.time()
        self.frame_count += 1
        if current_time - self.last_time > 1:
            self.last_time = current_time
            self.current_fps = self.frame_count
            self.frame_count = 0

        self.label.x = width - self.label.content_width
        self.label.y = height - 12
        self.label.text = f'FPS: {self.current_fps}'
        self.label.draw()


class TerminalGui:

    def __init__(self, title: str, terminal_provider: TerminalProvider, enable_input: bool):
        self.title = title
        self.term_prov = terminal_provider
        self.enable_input = enable_input
        self.input_listeners: List[Callable[[str], None]] = []
        terminal_width, terminal_height = self.term_prov.get_terminal_size()
        self.fps_display = FpsDisplay()

        font_size = 12
        max_height = terminal_height * font_size * LINE_SPACING_FACTOR
        self.window = pyglet.window.Window(width=int(terminal_width * font_size * 0.83),
                                           height=int(max_height), caption=self.title,
                                           vsync=False)

        def make_label(y_idx: int):
            return pyglet.text.Label(text='', font_name='JetBrainsMono Nerd Font', font_size=font_size, x=0,
                                     y=max_height - (
                                             y_idx + 1) * font_size * LINE_SPACING_FACTOR + LINE_SPACING_FACTOR * 2)

        self.cursor_calc_dummy_label = make_label(0)
        self.labels = []
        for i in range(terminal_height):
            labels = []
            self.labels.append(labels)

        @self.window.event
        def on_draw():
            self.window.clear()

            cursor_x, cursor_y = self.term_prov.get_terminal_cursor_position()
            lines = self.term_prov.get_terminal_context()

            for y, line in enumerate(lines):
                x_pos = 0
                line_str = ""

                bg_rect = pyglet.shapes.Rectangle(
                    x=0,
                    y=0,
                    width=0,
                    height=0,
                    color=(0, 0, 0)
                )

                last_char_style = None
                last_char = None

                current_label_text = ""
                has_unrendered_text = False

                group_idx = 0

                def flush_chars():
                    nonlocal has_unrendered_text, current_label_text, x_pos, last_char, group_idx
                    if last_char is None:
                        return
                    current_label_text = current_label_text.replace('\n', '')

                    if group_idx >= len(self.labels[y]):
                        label = make_label(y)
                        self.labels[y].append(label)
                    else:
                        label = self.labels[y][group_idx]

                    if label.text != current_label_text:
                        label.text = current_label_text

                    if label.bold != last_char.bold:
                        label.bold = last_char.bold

                    if label.italic != last_char.italics:
                        label.italic = last_char.italics

                    fg_color = decode_term_color(last_char.fg, False)
                    if fg_color != label.color:
                        label.color = fg_color
                    label.x = x_pos

                    hack_offset = 0
                    if '\uF111' in current_label_text:
                        hack_offset += 6
                    if '\uE61E' in current_label_text:
                        hack_offset += 2

                    if last_char.bg != "default":
                        bg_color = decode_term_color(last_char.bg, True)
                        bg_rect.x = x_pos
                        bg_rect.y = max_height - (y + 1) * font_size * LINE_SPACING_FACTOR
                        bg_rect.width = label.content_width + hack_offset
                        bg_rect.height = font_size * LINE_SPACING_FACTOR
                        bg_rect.color = bg_color
                        bg_rect.draw()

                    label.draw()

                    x_pos += label.content_width + hack_offset
                    current_label_text = ""
                    has_unrendered_text = False

                    group_idx += 1

                for cidx in range(len(line)):
                    char = line[cidx]
                    current_char_style = {
                        'bold': char.bold,
                        'fg': char.fg,
                        'bg': char.bg
                    }
                    if last_char_style != current_char_style:
                        if last_char_style is not None:
                            flush_chars()
                            pass
                        last_char_style = current_char_style
                    last_char = char

                    current_label_text += char.data
                    has_unrendered_text = True

                    line_str += char.data

                if has_unrendered_text:
                    flush_chars()
                    pass

                if y == cursor_y:
                    # calculate cursor position
                    self.cursor_calc_dummy_label.text = line_str[:cursor_x]
                    cursor_x_pos = self.cursor_calc_dummy_label.content_width

                    # draw cursor
                    cursor_y_pos = self.window.height - (cursor_y + 1) * font_size * LINE_SPACING_FACTOR
                    shape = pyglet.shapes.Rectangle(x=cursor_x_pos, y=cursor_y_pos, width=font_size * 0.75,
                                                    height=font_size * LINE_SPACING_FACTOR,
                                                    color=(255, 255, 255))
                    shape.draw()

            self.fps_display.draw(self.window.width, self.window.height)

        @self.window.event
        def on_key_press(symbol, modifiers):
            if symbol in key_xterm_mapping:
                stdin = key_xterm_mapping[symbol]
                for listener in self.input_listeners:
                    listener(stdin)
                if self.enable_input:
                    self.term_prov.send_input(stdin)
            if symbol == pyglet.window.key.ESCAPE:
                return pyglet.event.EVENT_HANDLED

        @self.window.event
        def on_text(text):
            for listener in self.input_listeners:
                listener(text)
            if self.enable_input:
                self.term_prov.send_input(text)

        @self.window.event
        def on_text_motion(motion):
            if motion in motion_xterm_mapping:
                stdin = motion_xterm_mapping[motion]
                if self.enable_input:
                    self.term_prov.send_input(stdin)

                for listener in self.input_listeners:
                    listener(stdin)

    def add_input_listener(self, listener: Callable[[str], None]):
        self.input_listeners.append(listener)
