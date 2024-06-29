from dataclasses import dataclass, field
from typing import TypedDict

color = str
class button_theme(TypedDict):
    bg: color
    fg: color

@dataclass
class Theme:
    # Gamerules
    GAME_SIZE: int = 11

    # Colors
    BACKGROUND_COLOR: color = "lightgray"
    TEXT_COLOR: color = "black"
    DEFAULT_BUTTON: button_theme = field(init=False)
    HEXAGON_BORDER_COLOR: color = "black"
    HEXAGON_BORDER_WIDTH: int = 4
    COLOR_BRIGHTNESS: tuple[float, float] = (1.0, 0.9)

    TITLE_FONT: str = ""
    TEXT_FONT: str = ""

    # Board drawing size (The Y size is calculated from the X size and the number of hexagons in the board)
    CANVAS_PADDING: int = 15
    CANVAS_SIZE_X: int = 800
    ## Math for the canvas
    CANVAS_SIZE_Y: int = 0
    HEX_SIDE_SIZE: int = CANVAS_SIZE_X // (3*GAME_SIZE-1)
    HEX_SIDE_SIZE_ROOT_3: int = int(HEX_SIDE_SIZE*3**(1/2))

    def __post_init__(self):
        self.DEFAULT_BUTTON = {"bg": self.BACKGROUND_COLOR, "fg": self.TEXT_COLOR, "font": (self.TEXT_FONT, 12)}
        self.CANVAS_SIZE_X += 2*self.CANVAS_PADDING
        self.CANVAS_SIZE_Y = 2*self.CANVAS_PADDING + self.GAME_SIZE*self.HEX_SIDE_SIZE_ROOT_3
