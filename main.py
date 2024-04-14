import tkinter as tk
from style import *
import math

class Player():
    def __init__(self, name, color) -> None:
        self._name = name
        self._color = color

    @property
    def name(self):
        return self._name
    
    @property
    def color(self):
        return self._color


class HexInterface:
    def __init__(self, game_size=11) -> None:
        # Screen and game info
        self._root = tk.Tk()
        self._root.title("Hex")
        
        # Set app icon from png
        self._root.iconphoto(False, tk.PhotoImage(file='assets/logo.png'))

        # Math for drawing cells
        self.__game_size: int = game_size
        self.__side_bar_width = 5
        self._canvas_size_x: int = 800
        self._hex_side_size = self._canvas_size_x / (1.5*((self.__game_size)*3**(1/2)))
        self._canvas_size_x += 2*self.__side_bar_width
        self._canvas_size_y = 1.5*self._hex_side_size * self.__game_size + self._hex_side_size/2 + 2*self.__side_bar_width

        self.__local_player: Player = Player("Player 1", "blue")
        self.__remote_player: Player = Player("Player 2", "red")
        self.__current_player: Player = self.__local_player

        ### Screen components
        # Game title
        self.__title_frame = tk.Frame(self._root, bg=BACKGROUND_COLOR)
        self.__game_title_label = tk.Label(self.__title_frame, text="Hex", font=("Helvetica", 24), bg=BACKGROUND_COLOR, fg="black", pady=10)

        # Player labels
        self.__local_player_label = tk.Label(self._root, text="Local Player")
        self.__remote_player_label = tk.Label(self._root, text="Remote Player")
        
        # Current player turn label
        self.__current_player_label = tk.Label(self._root, bg=BACKGROUND_COLOR)

        # Canva
        self.__canvas = tk.Canvas(self._root, width=self._canvas_size_x, height=self._canvas_size_y)
        self.__canvas.tag_bind("hexagon", "<Button-1>", lambda e: self.player_click(e))

        # Action buttons
        self.__local_player_action_button = tk.Button(self._root, text=self.__local_player.name, command=lambda: self.player_action(self.__local_player))
        self.__remote_player_action_button = tk.Button(self._root, text=self.__remote_player.name, command=lambda: self.player_action(self.__remote_player))

        self.load_styles()
        self.game_screen()

    def load_styles(self):
        self._root.configure(bg=BACKGROUND_COLOR)
        local_player_color = self.__local_player.color if self.__local_player != None else WAITING_COLOR
        remote_player_color = self.__remote_player.color if self.__remote_player != None else WAITING_COLOR

        self.__local_player_label.configure(bg= BACKGROUND_COLOR, fg=local_player_color)
        self.__remote_player_label.configure(bg= BACKGROUND_COLOR, fg=remote_player_color)

        self.__current_player_label.configure(text=f"Vez de {self.__current_player.name}", fg=self.__current_player.color, bg=BACKGROUND_COLOR)

        # Draw empty board
        [self.draw_hexagon(i, j, 'white') for i in range(self.__game_size) for j in range(self.__game_size)]

    def game_screen(self):
        '''Draws the game screen with the game title, player labels and action buttons, and the canvas for the game board.'''
        self.__game_title_label.pack()
        self.__title_frame.grid(row=0, column=1)

        self.__local_player_label.grid(row=1, column=2, padx=10)
        self.__remote_player_label.grid(row=3, column=0, padx=10)

        self.__local_player_action_button.grid(row=1, column=1, padx=10, sticky="e")
        self.__remote_player_action_button.grid(row=3, column=1, padx=10, sticky="w")

        # Board
        self.__canvas.grid(row=2, column=1, padx=10, pady=10)

        self.__current_player_label.grid(row=1, column=0, pady=10)

        # Draw top and bottom bars for local player
        bar_size = self._hex_side_size*3**(1/2)*self.__game_size
        bottom_bar_offset = bar_size/2 - self._hex_side_size/2
        top_bar_coords = (
            0, 0,
            bar_size, self.__side_bar_width,
        )
        bottom_bar_coords = (
            bottom_bar_offset, self._canvas_size_y - self.__side_bar_width,
            bottom_bar_offset + bar_size, self._canvas_size_y,
        )

        left_bar_coords = (
            -self._hex_side_size*3**(1/2)/2, 0,
            bottom_bar_offset, self._canvas_size_y
        )

        right_bar_coords = (
            bar_size, 0,
            self.__side_bar_width + bar_size + self.__game_size*self._hex_side_size*3**(1/2)/2, self._canvas_size_y
        )

        # Draw side bars for each player goals
        if self.__local_player != None:
            self.__canvas.create_rectangle(*top_bar_coords, fill=self.__local_player.color)
            self.__canvas.create_rectangle(*bottom_bar_coords, fill=self.__local_player.color)

        if self.__remote_player != None:
            self.__canvas.create_line(*left_bar_coords, fill=self.__remote_player.color, width=self.__side_bar_width)
            self.__canvas.create_line(*right_bar_coords, fill=self.__remote_player.color, width=self.__side_bar_width)

    def draw_hexagon(self, i, j, color, edgecolor='black'):
        side_root3_half = 3**(1/2)*self._hex_side_size/2
        x = 2*i*side_root3_half + j*side_root3_half
        y = 1.5*j*self._hex_side_size

        x += self.__side_bar_width
        y += self.__side_bar_width

        self.__canvas.create_polygon(
            x + side_root3_half, y,
            x + 2*side_root3_half, y + self._hex_side_size/2,
            x + 2*side_root3_half, y + 3*self._hex_side_size/2,
            x + side_root3_half, y + 2*self._hex_side_size,
            x, y + 3*self._hex_side_size/2,
            x, y + self._hex_side_size/2,

            fill=color,
            outline=edgecolor,
            tags="hexagon"
        )

    def start_game(self):
        self.__current_player = self.__local_player
        
        self.__current_player_label.configure(text=f"Vez de {self.__current_player.name}", fg=self.__current_player.color)

    def player_click(self, event):
        i, j = self.get_coords(event.x, event.y)
        if i < 0 or i >= self.__game_size or j < 0 or j >= self.__game_size: return

        self.draw_hexagon(i, j, self.__current_player.color)

        print(f"{self.__current_player.name} clicou em um hexágono na posição ({i}, {j})")
        if self.__current_player == self.__local_player:
            self.__current_player = self.__remote_player
        else:
            self.__current_player = self.__local_player
 
        self.__current_player_label.configure(text=f"Vez do {self.__current_player.name}", fg=self.__current_player.color)

    def get_coords(self, x, y):
        # y = 1.5*j*side_size
        # x = 2*i*side_root3_half + j*side_root3_half
        # j = y/(1.5*side_size)
        # i = (x-j*side_root3_half)/(side_root3_half*2)
        j = int(math.floor(y/(1.5*self._hex_side_size)))
        i = int(math.floor((x-j*self._hex_side_size*3**(1/2)/2)/(self._hex_side_size*3**(1/2))))
        return i, j

    def player_action(self, player: Player):
        print(f"{player.name} apertou seu botão de ação")
        if player == self.__local_player:
            self.__local_player_action_button.configure(bg=player.color, fg=BACKGROUND_COLOR)
        else:
            self.__remote_player_action_button.configure(bg=player.color, fg=BACKGROUND_COLOR)

if __name__ == "__main__":
    hex_interface = HexInterface()
    hex_interface._root.mainloop()
