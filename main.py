from enum import Enum
import tkinter as tk
from tkinter import simpledialog
from style import *
import random
import math
from colorsys import hsv_to_rgb
from dog.dog_interface import DogPlayerInterface
from dog.dog_actor import DogActor
from dog.start_status import StartStatus

class GameState(Enum):
    WAITING = 0
    RUNNING = 1
    ENDED = 2

class Cell(Enum):
    EMPTY = 0
    LOCAL = 1
    REMOTE = 2

class Player:
    def __init__(self, name, hue=-1) -> None:
        self._name: str = name
        self._hue: float = hue
        self._color, self._piece_color = self.calculate_colors()

    def calculate_colors(self) -> tuple[str, str]:
        if self._hue == -1: return "#000000", "#000000"
        r1, g1, b1 = [hex(int(c*255))[2:] for c in hsv_to_rgb(self._hue, 1.0, 0.9)]
        if len(r1) == 1: r1 = '0' + r1
        if len(g1) == 1: g1 = '0' + g1
        if len(b1) == 1: b1 = '0' + b1

        r, g, b = [hex(int(c*255))[2:] for c in hsv_to_rgb(self._hue, 0.3, 0.9)]
        if len(r) == 1: r = '0' + r
        if len(g) == 1: g = '0' + g
        if len(b) == 1: b = '0' + b

        return "#" + r1 + g1 + b1, "#" + r + g + b

    @property
    def name(self):
        return self._name
    
    @property
    def color(self):
        return self._color

    @property
    def piece_color(self):
        return self._piece_color
    
    @property
    def hue(self):
        return self._hue
    
    @name.setter
    def name(self, name):
        self._name = name

    @hue.setter
    def hue(self, hue):
        self._hue = hue
        self._color, self._piece_color = self.calculate_colors()

class Game:
    def __init__(self, screen: 'HexInterface', size=11) -> None:
        self._size = size
        self._board = [[Cell.EMPTY for _ in range(size)] for _ in range(size)]
        self._local_player = None
        self._remote_player = None
        self._current_player_turn = None
        self._game_state = GameState.WAITING
        self._screen = screen

    def insert_cell(self, i, j, cell: Cell):
        if self._board[i][j] != Cell.EMPTY: return None
        self._board[i][j] = cell
        self._screen.draw_hexagon(i, j, self.current_player_turn.piece_color)
        return cell

    def check_winner(self, cell: Cell):
        queue = [(0, b) if cell == Cell.REMOTE else (b, 0) for b in range(self.size)]
        queue = [possible_start for possible_start in queue if self._board[possible_start[0]][possible_start[1]] == cell]
        possible_end_cells = [(self.size-1, b) if cell == Cell.REMOTE else (b, self.size-1) for b in range(self.size)]
        possible_end_cells = [possible_cell for possible_cell in possible_end_cells if self._board[possible_cell[0]][possible_cell[1]] == cell]

        if not queue or not possible_end_cells: return None

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

    def restart(self):
        self.game_state = GameState.WAITING
        self.board = [[Cell.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.current_player_turn = None
        self.remote_player = None

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

    @board.setter
    def board(self, board: list[list[Cell]]) -> None:
        self._board = board
    
    @local_player.setter
    def local_player(self, player: Player) -> None:
        self._local_player = player
        self._screen.update_style_player_change()

    @remote_player.setter
    def remote_player(self, player: Player) -> None:
        self._remote_player = player
        self._screen.update_style_player_change()

    @current_player_turn.setter
    def current_player_turn(self, player: Player) -> None:
        self._current_player_turn = player
        self._screen.update_style_player_change()

    @game_state.setter
    def game_state(self, game_state: GameState) -> None:
        self._game_state = game_state
        self._screen.update_style_game_state_change()

class HexInterface(DogPlayerInterface):
    def __init__(self) -> None:
        # Screen and game info
        self._root = tk.Tk()
        self._root.title("Hex")
        self._game = Game(self)

        # Set app icon from png
        self._root.iconphoto(False, tk.PhotoImage(file='assets/logo.png'))

        # Math for drawing cells
        self.__canvas_padding = 15
        self._canvas_size_x = 800
        self._hex_side_size = self._canvas_size_x / (3*self._game.size-1)
        self._canvas_size_x += 2*self.__canvas_padding
        self._canvas_size_y = 2*self.__canvas_padding + self._game.size*self._hex_side_size*3**(1/2)

        ### Screen components
        # Game title
        self.__title_frame = tk.Frame(self._root, bg=BACKGROUND_COLOR)
        self.__game_title = tk.Label(self.__title_frame, text="Hex", font=("Helvetica", 24), bg=BACKGROUND_COLOR, fg="black", pady=10)

        # Notification label
        self.__notification = tk.Label(self._root, bg=BACKGROUND_COLOR)

        # Player labels
        self.__local_player_label = tk.Label(self._root, text="Waiting")
        self.__remote_player_label = tk.Label(self._root, text="Waiting")

        # Player action button
        self.__action_button = tk.Button(command=self.player_press_action_button)
        
        # Current player turn label
        self.__current_player_label = tk.Label(self._root, bg=BACKGROUND_COLOR)

        # Canva
        self.__canvas = tk.Canvas(self._root, width=self._canvas_size_x, height=self._canvas_size_y)

        # Initialize screen
        self.build_screen()
        self.update_style_game_state_change()

        # Register local player and conect to DOG
        self._game.local_player = Player(simpledialog.askstring(title="Apelido de jogador", prompt="Qual o seu nome?"))
        self.dog_server_interface = DogActor()
        dog_connection_message = self.dog_server_interface.initialize(self._game.local_player.name, self)
        self.__notification.configure(text=dog_connection_message)

    def update_style_player_change(self):
        if self._game.local_player != None:
            self.__local_player_label.configure(text=self._game.local_player.name, bg=BACKGROUND_COLOR, fg=self._game.local_player.color)
        else:
            self.__local_player_label.configure(text="Esperando", bg=BACKGROUND_COLOR)
        if self._game.remote_player != None:
            self.__remote_player_label.configure(text=self._game.remote_player.name, bg=BACKGROUND_COLOR, fg=self._game.remote_player.color)
        else:
            self.__remote_player_label.configure(text="Esperando", bg=BACKGROUND_COLOR)
        if self._game.current_player_turn != None:
            self.__current_player_label.configure(text=f"Vez de {self._game.current_player_turn.name}", bg=BACKGROUND_COLOR, fg=self._game.current_player_turn.color)
        else:
            self.__current_player_label.configure(text="Esperando", bg=BACKGROUND_COLOR)

    def update_style_game_state_change(self):
        if self._game.game_state == GameState.WAITING:
            self.__action_button.configure(text="Começar")
            # Set canvas background color and bind mouse events to empty hexagons
            def handle_mouse_move(hexagon, out):
                if self._game.game_state != GameState.RUNNING: return
                if self._game.current_player_turn != self._game.local_player: return
                self.__canvas.itemconfig(hexagon, fill=BACKGROUND_COLOR if out else self._game.current_player_turn.piece_color)

            self.__canvas.delete("all")
            for i in range(self._game.size):
                for j in range(self._game.size):
                    hexagon = self.draw_hexagon(i, j, BACKGROUND_COLOR)
                    self.__canvas.tag_bind(hexagon, "<Button-1>", lambda e, i=i, j=j: self.choose_cell(i, j))
                    self.__canvas.tag_bind(hexagon, "<Enter>", lambda e, hexagon=hexagon: handle_mouse_move(hexagon, False))
                    self.__canvas.tag_bind(hexagon, "<Leave>", lambda e, hexagon=hexagon: handle_mouse_move(hexagon, True))

        elif self._game.game_state == GameState.RUNNING:
            self.draw_borders(self._game.local_player)
            self.draw_borders(self._game.remote_player)
            self.__action_button.configure(text="Desistir")

        else:
            self.__action_button.configure(text="Recomeçar")

    def build_screen(self):
        '''Configures the default styling and layout of the screen components.'''
        # Styling
        self._root.configure(bg=BACKGROUND_COLOR)

        # Layout
        self.__game_title.pack()
        self.__title_frame.grid(row=0, column=1)
        self.__notification.grid(row=1, column=1)

        self.__local_player_label.grid(row=1, column=2, padx=10)
        self.__remote_player_label.grid(row=3, column=0, padx=10)
        self.__current_player_label.grid(row=1, column=0, padx=10)

        self.__action_button.grid(row=1, column=1, sticky="e", padx=10)

        # Board
        self.__canvas.grid(row=2, column=1, padx=10, pady=10)

    def draw_hexagon(self, i, j, color, edgecolor='black'):
        side_root3 = 3**(1/2)*self._hex_side_size
        x, y = self.hex_starting_point(i, j)

        hexagon = self.__canvas.create_polygon(
            x, self.fix_y(y + side_root3/2),
            x + 0.5*self._hex_side_size, self.fix_y(y + side_root3),
            x + 1.5*self._hex_side_size, self.fix_y(y + side_root3),
            x + 2.0*self._hex_side_size, self.fix_y(y + side_root3/2),
            x + 1.5*self._hex_side_size, self.fix_y(y),
            x + 0.5*self._hex_side_size, self.fix_y(y),

            fill=color,
            outline=edgecolor,
            tags="hexagon"
        )
        return hexagon

    def hex_starting_point(self, i, j):
        side_root3 = 3**(1/2)*self._hex_side_size
        i, j = self.convert_ij(i, j)

        n = self._game.size - abs(i+1-self._game.size)

        x = i*1.5*self._hex_side_size
        y = (self._canvas_size_y - n*side_root3)/2

        y += j*side_root3
        x += self.__canvas_padding

        return x, y

    def convert_ij(self, i, j):
        m = [[(x, y) for y in range(self._game.size)] for x in range(self._game.size)]
        tilt = []

        for x in range(self._game.size):
            tilt.append([m[i-x][self._game.size-i-1] for i in range(self._game.size) if i>=x])
            tilt.append([m[i][self._game.size-i+x-1] for i in range(self._game.size) if i>=x])        
        tilt = sorted(tilt[1:])
        for x, diagonal in enumerate(tilt):
            for y, cell in enumerate(diagonal):
                if cell == (i, j):
                    return x, y
        return -1, -1

    def draw_borders(self, player: Player):
        side_root3 = 3**(1/2)*self._hex_side_size
        start_coords = (
            self.hex_starting_point(0, 0),
            self.hex_starting_point(0, self._game.size-1),
            self.hex_starting_point(self._game.size-1, 0),
            self.hex_starting_point(self._game.size-1, self._game.size-1)
        )
                
        offsets = (
            (-self._hex_side_size, side_root3/2),
            (self._hex_side_size, -side_root3*1/6),
            (1*self._hex_side_size, side_root3*7/6),
            (3*self._hex_side_size, side_root3/2)
        )
        coords = [
            [x+y for x, y in zip(start_coords[0], offsets[0])],
            [x+y for x, y in zip(start_coords[1], offsets[1])],
            [x+y for x, y in zip(start_coords[2], offsets[2])],
            [x+y for x, y in zip(start_coords[3], offsets[3])]
        ]

        if player == self._game.local_player:
            self.__canvas.create_polygon(
                *(coords[0]),
                *(coords[1]),
                *(coords[2]),
                *(coords[3]),
                fill=player.color,
                tags="border"
            )
        else:
            self.__canvas.create_polygon(
                *(coords[1]),
                *(coords[3]),
                *(coords[0]),
                *(coords[2]),
                fill=player.color,
                tags="border"
            )
        self.__canvas.tag_raise("hexagon")

    def player_press_action_button(self):
        if self._game.game_state == GameState.WAITING: self.start_match()
        elif self._game.game_state == GameState.RUNNING: self._root.quit()
        elif self._game.game_state == GameState.ENDED: self.restart_game()

    def start_match(self):
        start_status = self.dog_server_interface.start_match(2)
        if start_status.get_code() in '01': self.__notification.configure(text=start_status.get_message())
        else: self.start_game(start_status)

    def receive_start(self, start_status: StartStatus) -> None:
        if start_status.get_code() == 0 or start_status.get_code() == 1: print(start_status.get_message())
        else: self.start_game(start_status, True)

    def start_game(self, start_status: StartStatus, received=False):
        '''Sets things up for when a match starts, depending on who started it.'''
        players = start_status.get_players()
        # I'm not sure if this check is necessary
        if len(players) != 2:
            print("How'd you get here")
            print(players)
            return

        p1, p2 = players
        p1_name, p2_name = p1[0], p2[0]
        p1_hue, p2_hue = self.calculate_player_colors(p1_name, p2_name)
        if received: p1_hue, p2_hue = p2_hue, p1_hue  # Makes the colors consistent for both players

        self._game.local_player.hue = p1_hue
        self._game.remote_player = Player(p2_name, p2_hue)

        self._game.game_state = GameState.RUNNING
        my_turn = (str(p1[2]) == "1") ^ (p1[1] == start_status.get_local_id())
        self._game.current_player_turn = self._game.local_player if my_turn else self._game.remote_player

    def restart_game(self):
        self.__game_title.configure(text="Hex")
        self._game.restart()

    def choose_cell(self, i, j):
        if self._game.game_state != GameState.RUNNING: return
        if self._game.current_player_turn != self._game.local_player: return

        if self._game.insert_cell(i, j, Cell.LOCAL) == None: return

        winning_path = self._game.check_winner(Cell.LOCAL)

        move = {'match_status': 'next'}
        move['marked_cell'] = (i, j)
        if winning_path:
            self.__notification.configure(text=f"{self._game.current_player_turn.name} venceu!")
            self._game.game_state = GameState.ENDED
            [self.draw_hexagon(i, j, self._game.current_player_turn.color, edgecolor='black') for i, j in winning_path]
            move['match_status'] = 'finished'
            move['winning_path'] = winning_path
        else:
            self._game.current_player_turn = self._game.local_player if self._game.current_player_turn == self._game.remote_player else self._game.remote_player        

        self.dog_server_interface.send_move(move)

    def receive_move(self, a_move):
        if a_move['match_status'] == 'finished':
            self.__notification.configure(text=f"{self._game.remote_player.name} venceu!")
            winning_path = a_move['winning_path']
            [self.draw_hexagon(i, j, self._game.remote_player.color, edgecolor='black') for i, j in winning_path]
            self._game.game_state = GameState.ENDED
        else:
            i, j = a_move['marked_cell']
            self._game.insert_cell(i, j, Cell.REMOTE)
            self._game.current_player_turn = self._game.local_player if self._game.current_player_turn == self._game.remote_player else self._game.remote_player

    def fix_y(self, y):
        return self._canvas_size_y - y

    @staticmethod
    def calculate_player_colors(p1_name, p2_name):
        p1_color_hue = sum([ord(c) for c in p1_name+p2_name]) % 256 / 256
        p2_color_hue = (p1_color_hue + 0.5) % 1
        return p1_color_hue, p2_color_hue

if __name__ == "__main__":
    hex_interface = HexInterface()
    hex_interface._root.mainloop()
