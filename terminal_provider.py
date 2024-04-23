from abc import abstractmethod
from dataclasses import dataclass

@dataclass
class Char:
    data: str
    fg: str = "default"
    bg: str = "default"
    bold: bool = False
    italics: bool = False
    underscore: bool = False
    strikethrough: bool = False
    reverse: bool = False
    blink: bool = False
    

class TerminalProvider:

    @abstractmethod
    def get_terminal_context(self) -> [[Char]]:  # returns a list of equal terminal rows
        pass
    
    @abstractmethod
    def get_terminal_size(self) -> (int, int):  # returns (width, height)
        pass

    @abstractmethod
    def get_terminal_cursor_position(self) -> (int, int):  # returns (x, y)
        pass

    @abstractmethod
    def set_terminal_cursor_position(self, x: int, y: int):
        pass

    @abstractmethod
    def send_input(self, key: str):  # sends a key-code to the terminal. x-term control keys are supported
        pass

    @abstractmethod
    def is_open(self) -> bool:
        pass

    def update(self):
        pass
