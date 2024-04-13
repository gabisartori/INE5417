from enum import Enum
import tkinter as tk
from style import *
import random
import math

class GameState(Enum):
    WAITING = 0
    RUNNING = 1
    ENDED = 2

class Cell(Enum):
    EMPTY = 0
    LOCAL = 1
    REMOTE = 2

class Player():
    def __init__(self, name, color) -> None:
        self.name = name
        self.color = color

class Game():
    def __init__(self, size=11) -> None:
        self.__size = size
        self.board = [[Cell.EMPTY for _ in range(size)] for _ in range(size)]
        self.local_player = None
        self.remote_player = None
        self.current_player_turn = None
        self.game_state = GameState.WAITING
    
    def get_size(self):
        return self.__size

    def print_board(self):
        for row in self.board:
            print(row)

class HexInterface:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Hex")
        self.game = Game()

        self.ready_players = 0
        self.restart_votes = 0

        self.local_player_label = tk.Label(self.root, text="Local Player")
        self.remote_player_label = tk.Label(self.root, text="Remote Player")

        self.local_player_action_button = tk.Button(command=lambda: self.player_press_action_button(self.game.local_player))
        self.remote_player_action_button = tk.Button(command=lambda: self.player_press_action_button(self.game.remote_player))
        
        self.current_player_label = tk.Label(self.root, bg=BACKGROUND_COLOR)
        
        self.canvas_size = 800
        canvas_x = self.canvas_size
        side_size = self.canvas_size / (1.5*((self.game.get_size())*3**(1/2)))
        canvas_y = 1.5*side_size*self.game.get_size() + side_size/2
        self.canvas = tk.Canvas(self.root, width=canvas_x, height=canvas_y)
        # self.canvas.bind("<Button-1>", lambda e: self.player_click())
        self.canvas.tag_bind("hexagon", "<Button-1>", lambda e: self.player_click(e))
        self.load_styles()
        self.game_screen()

    def load_styles(self):
        self.root.configure(bg=BACKGROUND_COLOR)
        local_player_color = self.game.local_player.color if self.game.local_player != None else WAITING_COLOR
        remote_player_color = self.game.remote_player.color if self.game.remote_player != None else WAITING_COLOR

        self.local_player_label.configure(bg= BACKGROUND_COLOR, fg=local_player_color)
        self.remote_player_label.configure(bg= BACKGROUND_COLOR, fg=remote_player_color)

        self.local_player_action_button.configure(text="ready", bg='white', fg='black')
        self.remote_player_action_button.configure(text="ready", bg='white', fg='black')
        self.current_player_label.configure(text="")

        [self.draw_hexagon(i, j, 'white') for i in range(self.game.get_size()) for j in range(self.game.get_size())]

    def game_screen(self):
        game_title = tk.Label(self.root, text="Hex", font=("Helvetica", 24), bg=BACKGROUND_COLOR, fg="black", pady=10)
        game_title.grid(row=0, column=1)

        self.local_player_label.grid(row=1, column=2, padx=10)
        self.remote_player_label.grid(row=3, column=0, padx=10)

        self.local_player_action_button.grid(row=1, column=1, sticky="e", padx=10)
        self.remote_player_action_button.grid(row=3, column=1, sticky="w", padx=10)

        self.canvas.grid(row=2, column=1, padx=10, pady=10)

    def draw_hexagon(self, i, j, color):
        side_size = self.canvas_size / (1.5*((self.game.get_size())*3**(1/2)))
        side_root3_half = 3**(1/2)*side_size/2
        x = 2*i*side_root3_half + j*side_root3_half
        y = 1.5*j*side_size

        self.canvas.create_polygon(
            x + side_root3_half, y,
            x + 2*side_root3_half, y + side_size/2,
            x + 2*side_root3_half, y + 3*side_size/2,
            x + side_root3_half, y + 2*side_size,
            x, y + 3*side_size/2,
            x, y + side_size/2,
            
            # fill=f"#{f'{hex((i+j)*10)[2:]}'*3}",
            fill=color,
            outline="black",
            tags="hexagon"
        )

    def player_press_action_button(self, player: Player):
        print(f"{player.name} pressed the action button")

        if player == self.game.local_player:
            self.local_player_action_button.configure(bg=player.color, fg="white")
        else:
            self.remote_player_action_button.configure(bg=player.color, fg="white")

        if self.game.game_state == GameState.WAITING:
            self.ready_players = min(self.ready_players + 1, 2)
            if self.ready_players == 2: self.start_game()
        elif self.game.game_state == GameState.RUNNING:
            self.restart_votes = min(self.restart_votes + 1, 2)
            if self.restart_votes == 2: self.restart_game()

        print(f"Game state: {self.game.game_state}")

    def start_game(self):
        self.game.game_state = GameState.RUNNING
        self.game.current_player_turn = (self.game.local_player, self.game.remote_player)[random.randint(0, 1)]

        self.current_player_label.grid(row=1, column=0)
        
        self.current_player_label.configure(text=f"{self.game.current_player_turn.name}'s turn", fg=self.game.current_player_turn.color)
        self.local_player_action_button.configure(bg="white", text="Restart", fg='black')
        self.remote_player_action_button.configure(bg="white", text="Restart", fg='black')

    def restart_game(self):
        self.ready_players = 0
        self.restart_votes = 0
        self.game.game_state = GameState.WAITING
        self.load_styles()
        

    def add_player(self, player: Player):
        if self.game.local_player == None:
            self.game.local_player = player
            self.load_styles()
        else:
            self.game.remote_player = player
            self.load_styles()

    def player_click(self, event):
        if self.game.game_state != GameState.RUNNING: return
        i, j = self.get_coords(event.x, event.y)
        self.draw_hexagon(i, j, self.game.current_player_turn.color)
        if self.game.current_player_turn == self.game.local_player:
            self.game.current_player_turn = self.game.remote_player
            print("Local player clicked")
        else:
            self.game.current_player_turn = self.game.local_player
            print("Remote player clicked")
        
        self.current_player_label.configure(text=f"{self.game.current_player_turn.name}'s turn", fg=self.game.current_player_turn.color)

    def get_coords(self, x, y):
        side_size = self.canvas_size / (1.5*((self.game.get_size())*3**(1/2)))
        # y = 1.5*j*side_size
        # j = y/(1.5*side_size)
        # x = 2*i*side_root3_half + j*side_root3_half
        j = int(math.floor(y/(1.5*side_size)))
        i = int(math.floor((x-j*side_size*3**(1/2)/2)/(side_size*3**(1/2))))
        return i, j
if __name__ == "__main__":

    hex_interface = HexInterface()
    hex_interface.add_player(Player("Player 1", "red"))
    hex_interface.add_player(Player("Player 2", "blue"))

    hex_interface.root.mainloop()