from enum import Enum
import tkinter as tk
from style import *
import random
import math
from colorsys import hsv_to_rgb

class GameState(Enum):
    WAITING = 0
    RUNNING = 1
    ENDED = 2

class Cell(Enum):
    EMPTY = 0
    LOCAL = 1
    REMOTE = 2

class Player():
    def __init__(self, name, hue) -> None:
        self._name = name
        r, g, b = [hex(int(c*255))[2:] for c in hsv_to_rgb(hue, 1.0, 0.9)]
        if len(r) == 1: r = '0' + r
        if len(g) == 1: g = '0' + g
        if len(b) == 1: b = '0' + b

        self._color = "#" + r + g + b
        r, g, b = [hex(int(c*255))[2:] for c in hsv_to_rgb(hue, 0.3, 0.9)]
        if len(r) == 1: r = '0' + r
        if len(g) == 1: g = '0' + g
        if len(b) == 1: b = '0' + b
        self._piece_color = "#" + r + g + b

    @property
    def name(self):
        return self._name
    
    @property
    def color(self):
        return self._color

    @property
    def piece_color(self):
        return self._piece_color

class Game():
    def __init__(self, size=11) -> None:
        self._size = size
        self._board = [[Cell.EMPTY for _ in range(size)] for _ in range(size)]
        self._local_player = None
        self._remote_player = None
        self._current_player_turn = None
        self.game_state = GameState.WAITING

    def insert_cell(self, i, j, cell: Cell):
        if self._board[i][j] != Cell.EMPTY: return None
        self._board[i][j] = cell
        return cell

    def check_winner(self, cell: Cell):
        queue = [(0, b) if cell == Cell.REMOTE else (b, 0) for b in range(self.size)]
        queue = [possible_start for possible_start in queue if self._board[possible_start[0]][possible_start[1]] == cell]
        possible_end_cells = [(self.size-1, b) if cell == Cell.REMOTE else (b, self.size-1) for b in range(self.size)]
        possible_end_cells = [possible_cell for possible_cell in possible_end_cells if self._board[possible_cell[0]][possible_cell[1]] == cell]

        current_cell = None

        bfs_visited = set(queue)
        bfs_tree = {}

        while queue:
            current_cell = queue.pop(0)
            if current_cell in possible_end_cells: break
            
            for neighbor in self.cell_neighbors(*current_cell):
                if (neighbor not in bfs_visited) and self._board[neighbor[0]][neighbor[1]] == cell:
                    bfs_tree[neighbor] = current_cell
                    queue.append(neighbor)
                    bfs_visited.add(neighbor)
        else:
            return None
        # Use the bfs tree to find the path from start to end
        path = [current_cell]
        while path[-1] in bfs_tree: path.append(bfs_tree[path[-1]])

        return path

    def cell_neighbors(self, i, j) -> set[Cell]:
        neighbors = set()
        for x in range(-1, 2):
            for y in range(-1, 2):
                if (x == y == 0) or (x == -1 and y == -1) or (x == 1 and y == 1): continue
                if x+i < 0 or x+i >= self.size or y+j < 0 or y+j >= self.size: continue
                neighbors.add((x+i, y+j))

        return neighbors

    @property
    def size(self) -> int:
        return self._size
    
    @property
    def board(self) -> list[list[Cell]]:
        return self._board
    
    @property
    def local_player(self) -> Player:
        return self._local_player

    @property
    def remote_player(self) -> Player:
        return self._remote_player

    @property
    def current_player_turn(self) -> Player | None:
        return self._current_player_turn

    @property
    def game_state(self) -> GameState:
        return self._game_state

    @size.setter
    def size(self, size: int) -> None:
        self._size = size

    @current_player_turn.setter
    def current_player_turn(self, player: Player) -> None:
        self._current_player_turn = player

    @board.setter
    def board(self, board: list[list[Cell]]) -> None:
        self._board = board
    
    @local_player.setter
    def local_player(self, player: Player) -> None:
        self._local_player = player

    @remote_player.setter
    def remote_player(self, player: Player) -> None:
        self._remote_player = player

    @current_player_turn.setter
    def current_player_turn(self, player: Player) -> None:
        self._current_player_turn = player

    @game_state.setter
    def game_state(self, game_state: GameState) -> None:
        self._game_state = game_state


class HexInterface:
    def __init__(self) -> None:
        # Screen and game info
        self._root = tk.Tk()
        self._root.title("Hex")
        self._game = Game()
        
        # Set app icon from png
        self._root.iconphoto(False, tk.PhotoImage(file='assets/logo.png'))

        # Math for drawing cells
        self.__canvas_padding = 15
        self._canvas_size_x = 800
        self._hex_side_size = self._canvas_size_x / (1.5*((self._game.size)*3**(1/2)))
        self._canvas_size_x += 2*self.__canvas_padding
        self._canvas_size_y = 1.5*self._hex_side_size * self._game.size + self._hex_side_size/2 + 2*self.__canvas_padding

        # Control gamestate
        self._ready_players = 0
        self._restart_votes = 0

        ### Screen components
        # Game title
        self.__title_frame = tk.Frame(self._root, bg=BACKGROUND_COLOR)
        self.__game_title = tk.Label(self.__title_frame, text="Hex", font=("Helvetica", 24), bg=BACKGROUND_COLOR, fg="black", pady=10)

        # Player labels
        self.__local_player_label = tk.Label(self._root, text="Local Player")
        self.__remote_player_label = tk.Label(self._root, text="Remote Player")

        # Player action buttons
        self.local_player_action_button = tk.Button(command=lambda: self.player_press_action_button(self._game.local_player))
        self.remote_player_action_button = tk.Button(command=lambda: self.player_press_action_button(self._game.remote_player))
        
        # Current player turn label
        self.__current_player_label = tk.Label(self._root, bg=BACKGROUND_COLOR)

        # Canva
        self.__canvas = tk.Canvas(self._root, width=self._canvas_size_x, height=self._canvas_size_y)
        self.__canvas.tag_bind("hexagon", "<Button-1>", lambda e: self.player_click(e))

    def load_styles(self):
        self._root.configure(bg=BACKGROUND_COLOR)
        local_player_color = self._game.local_player.color if self._game.local_player != None else WAITING_COLOR
        remote_player_color = self._game.remote_player.color if self._game.remote_player != None else WAITING_COLOR

        self.__local_player_label.configure(bg= BACKGROUND_COLOR, fg=local_player_color)
        self.__remote_player_label.configure(bg= BACKGROUND_COLOR, fg=remote_player_color)

        # Set action buttons to "waiting for game to start" (WAITING) state
        self.local_player_action_button.configure(text="ready", bg='white', fg='black')
        self.remote_player_action_button.configure(text="ready", bg='white', fg='black')
        self.__current_player_label.configure(text="")

        [self.draw_hexagon(i, j, 'white') for i in range(self._game.size) for j in range(self._game.size)]

    def game_screen(self):
        '''Draws the game screen with the game title, player labels and action buttons, and the canvas for the game board.'''
        self.__game_title.pack()
        self.__title_frame.grid(row=0, column=1)

        self.__local_player_label.grid(row=1, column=2, padx=10)
        self.__remote_player_label.grid(row=3, column=0, padx=10)
        self.__current_player_label.grid(row=1, column=0, padx=10)

        self.local_player_action_button.grid(row=1, column=1, sticky="e", padx=10)
        self.remote_player_action_button.grid(row=3, column=1, sticky="w", padx=10)

        # Board
        self.__canvas.grid(row=2, column=1, padx=10, pady=10)

        [self.draw_triangle(i, True, self._game.local_player) for i in range(self._game.size+1)]
        [self.draw_triangle(i, False, self._game.local_player) for i in range(self._game.size+1)]

        [self.draw_triangle(i, True, self._game.remote_player) for i in range(1, self._game.size)]
        [self.draw_triangle(i, False, self._game.remote_player) for i in range(1, self._game.size)]

    def draw_hexagon(self, i, j, color, edgecolor='black'):
        side_root3 = 3**(1/2)*self._hex_side_size
        x = i*side_root3 + j*side_root3/2
        y = 1.5*j*self._hex_side_size

        x += self.__canvas_padding
        y += self.__canvas_padding

        self.__canvas.create_polygon(
            x + side_root3/2, self.fix_y(y),
            x + side_root3, self.fix_y(y + self._hex_side_size/2),
            x + side_root3, self.fix_y(y + 3*self._hex_side_size/2),
            x + side_root3/2, self.fix_y(y + 2*self._hex_side_size),
            x, self.fix_y(y + 3*self._hex_side_size/2),
            x, self.fix_y(y + self._hex_side_size/2),

            fill=color,
            outline=edgecolor,
            tags="hexagon"
        )

    def draw_triangle(self, i: int, start: bool, player: Player):
        side_root3 = 3**(1/2)*self._hex_side_size
        coords = []
        if player == self._game.local_player:
            if start: # Bottom side
                y = self.__canvas_padding
                x = self.__canvas_padding + i*side_root3

                coords.append(max(self.__canvas_padding, x - side_root3/2))
                coords.append(self.fix_y(y))                 

                coords.append(x)
                coords.append(self.fix_y(y + self._hex_side_size/2))

                coords.append(min(x + side_root3/2, self.__canvas_padding+self._game.size*side_root3))
                coords.append(self.fix_y(y))               
            else: # Top side
                start_x = self.__canvas_padding + (self._game.size-1)*side_root3/2
                x = start_x + i*side_root3
                y = self._canvas_size_y - self.__canvas_padding

                coords.append(max(start_x, x - side_root3/2))
                coords.append(self.fix_y(y))

                coords.append(x)
                coords.append(self.fix_y(y - self._hex_side_size/2))

                coords.append(min(x + side_root3/2, start_x + self._game.size*side_root3))
                coords.append(self.fix_y(y))
        else:
            if start: # Left side
                x = self.__canvas_padding + i*side_root3/2
                y = self.__canvas_padding + i*1.5*self._hex_side_size + self._hex_side_size/2

                coords.append(x - side_root3/2)
                coords.append(self.fix_y(y - self._hex_side_size/2))

                coords.append(x)
                coords.append(self.fix_y(y))

                coords.append(x)
                coords.append(self.fix_y(y + self._hex_side_size))
            else: # Right side
                start_x = self.__canvas_padding + (self._game.size)*side_root3
                x = start_x + (i-1)*side_root3/2
                y = self.__canvas_padding + i*1.5*self._hex_side_size
                print(y)

                coords.append(x)
                coords.append(self.fix_y(y))

                coords.append(x)
                coords.append(self.fix_y(y - self._hex_side_size))

                coords.append(x + side_root3/2)
                coords.append(self.fix_y(y + self._hex_side_size/2))

        self.__canvas.create_polygon(
            *coords,
            fill=player.color,
        )

    def player_press_action_button(self, player: Player):
        print(f"{player.name} pressed the action button")

        if player == self._game.local_player:
            self.local_player_action_button.configure(bg=player.color, fg="white")
        else:
            self.remote_player_action_button.configure(bg=player.color, fg="white")

        if self._game.game_state == GameState.WAITING:
            self._ready_players = min(self._ready_players + 1, 2)
            if self._ready_players == 2: self.start_game()
        elif self._game.game_state == GameState.RUNNING or self._game.game_state == GameState.ENDED:
            self._restart_votes = min(self._restart_votes + 1, 2)
            if self._restart_votes == 2: self.restart_game()

        print(f"Game state: {self._game.game_state}")

    def start_game(self):
        self._game.game_state = GameState.RUNNING
        self._game.current_player_turn = (self._game.local_player, self._game.remote_player)[random.randint(0, 1)]
        
        self.__current_player_label.configure(text=f"Vez de {self._game.current_player_turn.name}", fg=self._game.current_player_turn.color)
        self.local_player_action_button.configure(bg="white", text="Restart", fg='black')
        self.remote_player_action_button.configure(bg="white", text="Restart", fg='black')

    def restart_game(self):
        self._ready_players = 0
        self._restart_votes = 0
        self._game.game_state = GameState.WAITING
        self._game.board = [[Cell.EMPTY for _ in range(self._game.size)] for _ in range(self._game.size)]
        self.load_styles()

    def add_player(self, player: Player):
        if self._game.local_player == None: self._game.local_player = player
        else: self._game.remote_player = player
        self.load_styles()

    def player_click(self, event):
        if self._game.game_state != GameState.RUNNING: return
        i, j = self.get_hex_index_by_coords(event.x, event.y)
        if i < 0 or i >= self._game.size or j < 0 or j >= self._game.size: return

        cell_value = Cell.LOCAL if self._game.current_player_turn == self._game.local_player else Cell.REMOTE
        if self._game.insert_cell(i, j, cell_value) == None: return

        self.draw_hexagon(i, j, self._game.current_player_turn.piece_color)
        winning_path = self._game.check_winner(cell_value)

        if winning_path != None:
            print(f"{self._game.current_player_turn.name} wins!")
            self._game.game_state = GameState.ENDED
            self.draw_winning_path(self._game.current_player_turn, winning_path)
            return

        self._game.current_player_turn = self._game.local_player if self._game.current_player_turn == self._game.remote_player else self._game.remote_player        
        self.__current_player_label.configure(text=f"Vez de {self._game.current_player_turn.name}", fg=self._game.current_player_turn.color)

    def draw_winning_path(self, winner: Player, winning_path):
        for i, j in winning_path:
            self.draw_hexagon(i, j, winner.color, edgecolor='black')

    def get_hex_index_by_coords(self, x, y):
        # y = 1.5*j*side_size
        # x = 2*i*side_root3_half + j*side_root3_half
        # j = y/(1.5*side_size)
        # i = (x-j*side_root3_half)/(side_root3_half*2)
        y = self.fix_y(y)
        x -= self.__canvas_padding
        y -= self.__canvas_padding

        j = int(math.floor(y/(1.5*self._hex_side_size)))
        i = int(math.floor((x-j*self._hex_side_size*3**(1/2)/2)/(self._hex_side_size*3**(1/2))))
        return i, j

    def fix_y(self, y):
        return self._canvas_size_y - y

if __name__ == "__main__":
    p1_name = "Player 1"
    p2_name = "Player 2"
    p1_color_hue = sum([ord(c) for c in p1_name]) % 256 / 256
    p2_color_hue = (p1_color_hue + 0.5) % 1

    hex_interface = HexInterface()
    hex_interface.add_player(Player(p1_name, p1_color_hue))
    hex_interface.add_player(Player(p2_name, p2_color_hue))
    hex_interface.game_screen()
    hex_interface._root.mainloop()
