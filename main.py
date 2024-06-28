from enum import Enum
from typing import TypedDict, Optional

import tkinter as tk
from tkinter import simpledialog
from themes import *
from colorsys import hsv_to_rgb
from dog.dog_interface import DogPlayerInterface
from dog.dog_actor import DogActor
from dog.start_status import StartStatus

theme = Theme()

class dog_message(TypedDict):
    match_status: str
    marked_cell: tuple[int, int]
    winning_path: Optional[list[tuple[int, int]]]

class GameState(Enum):
    WAITING = 0
    RUNNING = 1
    ENDED = 2
    WITHDRAWN = 3

class Cell(Enum):
    EMPTY = 0
    P1 = 1
    P2 = 2

class Player:
    def __init__(self, name, hue=-1) -> None:
        self._name: str = name
        self._hue: float = hue
        self._color, self._piece_color = self.calculate_colors()

    def calculate_colors(self) -> tuple[str, str]:
        if self._hue == -1: return theme.TEXT_COLOR, theme.TEXT_COLOR
        r1, g1, b1 = [hex(int(c*255))[2:] for c in hsv_to_rgb(self._hue, *theme.COLOR_BRIGHTNESS)]
        if len(r1) == 1: r1 = '0' + r1
        if len(g1) == 1: g1 = '0' + g1
        if len(b1) == 1: b1 = '0' + b1

        r, g, b = [hex(int(c*255))[2:] for c in hsv_to_rgb(self._hue, 0.3, 0.7)]
        if len(r) == 1: r = '0' + r
        if len(g) == 1: g = '0' + g
        if len(b) == 1: b = '0' + b

        self._color, self._piece_color =  "#" + r1 + g1 + b1, "#" + r + g + b
        return self._color, self._piece_color

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
        self.calculate_colors()

class Game:
    def __init__(self, size: int) -> None:
        self._size: int = size
        self._local_player: Player = None
        # Equivalent to restarting the game
        self._board: list[list[Cell]] = [[Cell.EMPTY for _ in range(size)] for _ in range(size)]
        self._player1: Player = None
        self._player2: Player = None
        self._current_player_turn: Player = None
        self._winner: Player = None
        self._game_state: GameState = GameState.WAITING
        self._winning_path: list[tuple[int, int]] = None

    def make_move(self, i: int, j: int) -> dog_message | None:
        if self.game_state != GameState.RUNNING: return None
        if self.current_player_turn != self.local_player: return None
        if self.board[i][j] != Cell.EMPTY: return None
        
        self.board[i][j] = Cell.P1 if self.current_player_turn == self.player1 else Cell.P2

        move = {}
        if winning_path := self.check_winner():
            self.game_state = GameState.ENDED
            self.winning_path = winning_path
            self.winner = self.local_player
            move['winning_path'] = winning_path
            move['match_status'] = 'finished'    
        else:
            self.switch_player_turn()
            move['marked_cell'] = (i, j)
            move['match_status'] = 'next'
        
        return move

    def receive_move(self, a_move: dog_message) -> None:
        if a_move['match_status'] == 'finished':
            self.game_state = GameState.ENDED
            self.winning_path = a_move['winning_path']
            self.winner = self.current_player_turn
        else:
            i, j = a_move['marked_cell']
            self.board[i][j] = Cell.P1 if self.current_player_turn == self.player1 else Cell.P2
            self.switch_player_turn()

    def receive_withdraw(self) -> None:
        self.game_state = GameState.WITHDRAWN
        self.winner = None

    def check_winner(self):
        queue, goal, cell = [], [], None
        if self.current_player_turn == self.player1:
            cell = Cell.P1
            for i in range(self.size):
                if self.board[i][0] == cell: queue.append((i, 0))
                if self.board[i][self.size-1] == cell: goal.append((i, self.size-1))
        else:
            cell = Cell.P2
            for i in range(self.size):
                if self.board[0][i] == cell: queue.append((0, i))
                if self.board[self.size-1][i] == cell: goal.append((self.size-1, i))

        if not queue or not goal: return None

        current_cell = None
        bfs_visited = set(queue)
        bfs_tree = {}

        while queue:
            current_cell = queue.pop(0)
            if current_cell in goal: break

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

    def cell_neighbors(self, i, j) -> set[tuple[int, int]]:
        neighbors = set()
        for x in range(-1, 2):
            for y in range(-1, 2):
                if (x == y == 0) or (x == -1 and y == -1) or (x == 1 and y == 1): continue
                if x+i < 0 or x+i >= self.size or y+j < 0 or y+j >= self.size: continue
                neighbors.add((x+i, y+j))

        return neighbors

    def restart(self):
        self.board = [[Cell.EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.player1 = None
        self.player2 = None
        self.current_player_turn = None
        self.winner = None
        self.game_state = GameState.WAITING
        self.winning_path = None

    def switch_player_turn(self):
        self.current_player_turn = self.player1 if self.current_player_turn == self.player2 else self.player2

    @property
    def size(self) -> int:
        return self._size
    
    @property
    def local_player(self) -> Player:
        return self._local_player

    @property
    def board(self) -> list[list[Cell]]:
        return self._board
    
    @property
    def player1(self) -> Player:
        return self._player1

    @property
    def player2(self) -> Player:
        return self._player2
    
    @property
    def current_player_turn(self) -> Player | None:
        return self._current_player_turn

    @property
    def winner(self) -> Player | None:
        return self._winner

    @property
    def game_state(self) -> GameState:
        return self._game_state

    @property
    def winning_path(self) -> list[tuple[int, int]]:
        return self._winning_path

    @local_player.setter
    def local_player(self, player: Player) -> None:
        self._local_player = player

    @board.setter
    def board(self, board: list[list[Cell]]) -> None:
        self._board = board
    
    @player1.setter
    def player1(self, player: Player) -> None:
        self._player1 = player

    @player2.setter
    def player2(self, player: Player) -> None:
        self._player2 = player

    @current_player_turn.setter
    def current_player_turn(self, player: Player) -> None:
        self._current_player_turn = player

    @winner.setter
    def winner(self, player: Player) -> None:
        self._winner = player

    @game_state.setter
    def game_state(self, game_state: GameState) -> None:
        self._game_state = game_state

    @winning_path.setter
    def winning_path(self, path: list[tuple[int, int]]) -> None:
        self._winning_path = path

class HexInterface(DogPlayerInterface):
    # Initialize
    def __init__(self) -> None:
        # DogPlayerInterface
        self._dog_server_interface = DogActor()
        self._dog_conneted = None

        # Screen and game info
        self._root = tk.Tk()
        self._game = Game(theme.GAME_SIZE)

        ### Screen components
        # Labels
        self.__game_title_label = tk.Label(self.root, text="Hex")
        self.__notification_label = tk.Label(self.root)
        self.__player1_label = tk.Label(self.root, text="Waiting")
        self.__player2_label = tk.Label(self.root, text="Waiting")
        self.__current_player_label = tk.Label(self.root)

        # Buttons
        self.__action_button = tk.Button()

        # Canva
        self.__canvas = tk.Canvas(self.root, width=theme.CANVAS_SIZE_X, height=theme.CANVAS_SIZE_Y)

        # Initialize screen
        self.build_screen()

        # Register local player and conect to DOG
        self.game.local_player = Player(simpledialog.askstring(title="Apelido de jogador", prompt="Qual o seu nome?"))
        dog_connection_message = self.dog_server_interface.initialize(self.game.local_player.name, self)
        self.__notification_label.configure(text=dog_connection_message)
        self.connected_dog = dog_connection_message.lower() == "conectado a dog server"
        self.update_screen()

    def update_screen(self):
        self.__canvas.delete("all")
        self.draw_board()
        p1 = p1c = p2 = p2c = current = currentc = action = action_message = None
        if self.connected_dog is False:  # Distinguir is False de None
            p1 = "Desconectado"
            p1c = theme.TEXT_COLOR
            p2 = "Desconectado"
            p2c = theme.TEXT_COLOR
            current = ""
            currentc = theme.TEXT_COLOR
            action = self._root.quit
            action_message = "Sair"
        elif self.game.game_state == GameState.WAITING:
            p1 = self.game.local_player.name if self.game.local_player else "Esperando"
            p1c = theme.TEXT_COLOR
            p2 = "Esperando"
            p2c = theme.TEXT_COLOR
            current = ""
            currentc = theme.TEXT_COLOR
            action = self.start_match
            action_message = "Começar"
        elif self.game.game_state == GameState.RUNNING:
            p1 = self.game.player1.name
            p1c = self.game.player1.color
            p2 = self.game.player2.name
            p2c = self.game.player2.color
            current = f"Vez de {self.game.current_player_turn.name}"
            currentc = self.game.current_player_turn.color
            action = self._root.quit
            action_message = "Desistir"
        elif self.game.game_state == GameState.ENDED:
            p1 = self.game.player1.name
            p1c = self.game.player1.color
            p2 = self.game.player2.name
            p2c = self.game.player2.color
            current = f"{self.game.winner.name} venceu!"
            currentc = self.game.winner.color
            action = self.restore_inital_state
            action_message = "Restaurar"
        elif self.game.game_state == GameState.WITHDRAWN:
            p1 = self.game.player1.name
            p1c = self.game.player1.color
            p2 = self.game.player2.name
            p2c = self.game.player2.color
            current = ""
            currentc = theme.TEXT_COLOR
            action = self.restore_inital_state
            action_message = "Restaurar"
            self.__notification_label.configure(text="Adversário desistiu!")

        self.__player1_label.configure(text=p1, fg=p1c)
        self.__player2_label.configure(text=p2, fg=p2c)
        self.__current_player_label.configure(text=current, fg=currentc)
        self.__action_button.configure(text=action_message, command=action)


    def draw_board(self):
        def handle_mouse_move(hexagon, out):
            if self.game.game_state != GameState.RUNNING: return
            if self.game.current_player_turn != self.game.local_player: return
            self.__canvas.itemconfig(hexagon, fill=theme.BACKGROUND_COLOR if out else self.game.current_player_turn.piece_color)
        if self.game.game_state != GameState.WAITING:
            self.draw_borders(self.game.player1)
            self.draw_borders(self.game.player2)
        for i in range(self.game.size):
            for j in range(self.game.size):
                if self.game.board[i][j] == Cell.EMPTY:
                    hexagon = self.draw_hexagon(i, j, theme.BACKGROUND_COLOR)
                    self.__canvas.tag_bind(hexagon, "<Button-1>", lambda e, i=i, j=j: self.choose_cell(i, j))
                    self.__canvas.tag_bind(hexagon, "<Enter>", lambda e, hexagon=hexagon: handle_mouse_move(hexagon, False))
                    self.__canvas.tag_bind(hexagon, "<Leave>", lambda e, hexagon=hexagon: handle_mouse_move(hexagon, True))
                elif self.game.board[i][j] == Cell.P1:
                    self.draw_hexagon(i, j, self.game.player1.piece_color)
                else:
                    self.draw_hexagon(i, j, self.game.player2.piece_color)
        if self.game.game_state == GameState.ENDED:
            self.draw_winning_path(self.game.winning_path)

    def build_screen(self):
        '''Configures the default styling and layout of the screen components.'''
        # Window assets
        self.root.title("Hex")
        self.root.iconphoto(False, tk.PhotoImage(file='assets/logo.png'))

        # Styling
        self.root.configure(bg=theme.BACKGROUND_COLOR)
        self.__game_title_label.configure(bg=theme.BACKGROUND_COLOR, fg=theme.TEXT_COLOR, font=("Helvetica", 24), pady=30)
        self.__notification_label.configure(bg=theme.BACKGROUND_COLOR, fg=theme.TEXT_COLOR)
        self.__player1_label.configure(bg=theme.BACKGROUND_COLOR, fg=theme.TEXT_COLOR)
        self.__player2_label.configure(bg=theme.BACKGROUND_COLOR, fg=theme.TEXT_COLOR)
        self.__current_player_label.configure(bg=theme.BACKGROUND_COLOR, fg=theme.TEXT_COLOR)
        self.__action_button.configure(**theme.DEFAULT_BUTTON)
        self.__canvas.configure(bg=theme.BACKGROUND_COLOR, highlightthickness=0)

        # Layout
        self.__game_title_label.grid(row=0, column=1)
        self.__notification_label.grid(row=1, column=1)

        self.__player1_label.grid(row=1, column=2, padx=10)
        self.__player2_label.grid(row=3, column=0, padx=10)
        self.__current_player_label.grid(row=1, column=0, padx=10)

        self.__action_button.grid(row=1, column=1, sticky="e", padx=10)

        # Board
        self.__canvas.grid(row=2, column=1, padx=10, pady=10)

        self.update_screen()

    # Draw Board
    def draw_hexagon(self, i: int, j: int, color, edgecolor=theme.HEXAGON_BORDER_COLOR) -> int:
        x, y = self.hex_starting_point(i, j)

        hexagon = self.__canvas.create_polygon(
            x, self.fix_y(y + theme.HEX_SIDE_SIZE_ROOT_3/2),
            x + 0.5*theme.HEX_SIDE_SIZE, self.fix_y(y + theme.HEX_SIDE_SIZE_ROOT_3),
            x + 1.5*theme.HEX_SIDE_SIZE, self.fix_y(y + theme.HEX_SIDE_SIZE_ROOT_3),
            x + 2.0*theme.HEX_SIDE_SIZE, self.fix_y(y + theme.HEX_SIDE_SIZE_ROOT_3/2),
            x + 1.5*theme.HEX_SIDE_SIZE, self.fix_y(y),
            x + 0.5*theme.HEX_SIDE_SIZE, self.fix_y(y),

            width=theme.HEXAGON_BORDER_WIDTH,
            fill=color,
            outline=edgecolor,
            tags="hexagon"
        )
        return hexagon

    def hex_starting_point(self, i: int, j: int) -> tuple[int, int]:
        i, j = self.convert_ij(i, j)

        n = self.game.size - abs(i+1-self.game.size)

        x = i*1.5*theme.HEX_SIDE_SIZE
        y = (theme.CANVAS_SIZE_Y - n*theme.HEX_SIDE_SIZE_ROOT_3)/2

        y += j*theme.HEX_SIDE_SIZE_ROOT_3
        x += theme.CANVAS_PADDING

        return x, y

    def convert_ij(self, i: int, j: int) -> tuple[int, int]:
        m = [[(x, y) for y in range(self.game.size)] for x in range(self.game.size)]
        tilt = []

        for x in range(self.game.size):
            tilt.append([m[i-x][self.game.size-i-1] for i in range(self.game.size) if i>=x])
            tilt.append([m[i][self.game.size-i+x-1] for i in range(self.game.size) if i>=x])        
        tilt = sorted(tilt[1:])
        for x, diagonal in enumerate(tilt):
            for y, cell in enumerate(diagonal):
                if cell == (i, j):
                    return x, y
        return -1, -1

    def draw_borders(self, player: Player):
        start_coords = (
            self.hex_starting_point(0, 0),
            self.hex_starting_point(0, self.game.size-1),
            self.hex_starting_point(self.game.size-1, 0),
            self.hex_starting_point(self.game.size-1, self.game.size-1)
        )
                
        offsets = (
            (-theme.HEX_SIDE_SIZE, theme.HEX_SIDE_SIZE_ROOT_3/2),
            (theme.HEX_SIDE_SIZE, -theme.HEX_SIDE_SIZE_ROOT_3*1/6),
            (1*theme.HEX_SIDE_SIZE, theme.HEX_SIDE_SIZE_ROOT_3*7/6),
            (3*theme.HEX_SIDE_SIZE, theme.HEX_SIDE_SIZE_ROOT_3/2)
        )
        coords = [
            [x+y for x, y in zip(start_coords[0], offsets[0])],
            [x+y for x, y in zip(start_coords[1], offsets[1])],
            [x+y for x, y in zip(start_coords[2], offsets[2])],
            [x+y for x, y in zip(start_coords[3], offsets[3])]
        ]

        if player == self.game.player1:
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

    def draw_winning_path(self, path: list[tuple[int, int]]):
        for i, j in path:
            self.draw_hexagon(i, j, self.game.current_player_turn.color)

    def fix_y(self, y: int) -> int:
        return theme.CANVAS_SIZE_Y - y

    # StartMatch
    def start_match(self):
        start_status = self.dog_server_interface.start_match(2)
        if str(start_status.get_code()) in '01': self.__notification_label.configure(text=start_status.get_message())
        else: self.start_game(start_status)

    # ReceiveStart
    def receive_start(self, start_status: StartStatus) -> None:
        if str(start_status.get_code()) in "01": self.__notification_label.configure(text=start_status.get_message())
        else: self.start_game(start_status, True)

    # StartGame
    def start_game(self, start_status: StartStatus, received=False):
        '''Sets things up for when a match starts, depending on who started it.'''
        self.restore_inital_state()
        
        players = start_status.get_players()
        # I'm not sure if this check is necessary
        if len(players) != 2:
            print("How'd you get here")
            print(players)
            return

        p1, p2 = players
        if received: p1, p2 = p2, p1
        p1_name, p2_name = p1[0], p2[0]
        p1_hue, p2_hue = self.calculate_player_colors(p1_name, p2_name)

        self.game.player1 = Player(p1_name, p1_hue)
        self.game.player2 = Player(p2_name, p2_hue)
        self.game.local_player = self.game.player2 if received else self.game.player1

        self.game.game_state = GameState.RUNNING
        p1_turn = (str(p1[2]) == "1")
        self.game.current_player_turn = self.game.player1 if p1_turn else self.game.player2
        self.update_screen()

    def restore_inital_state(self):
        self.game.restart()
        self.update_screen()

    # ChooseCell
    def choose_cell(self, i, j):
        if move := self.game.make_move(i, j):
            self.update_screen()
            self.dog_server_interface.send_move(move)

    # ReceiveMove
    def receive_move(self, a_move: dog_message):
        self.game.receive_move(a_move)
        self.update_screen()

    # ReceiveLeave
    def receive_withdrawal_notification(self):
        self.game.receive_withdraw()
        self.update_screen()

    # Auxiliars
    @staticmethod
    def calculate_player_colors(p1_name, p2_name):
        p1_color_hue = sum([ord(c) for c in p1_name+p2_name]) % 256 / 256
        p2_color_hue = (p1_color_hue + 0.5) % 1
        return p1_color_hue, p2_color_hue

    @property
    def root(self):
        return self._root
    
    @property
    def game(self):
        return self._game

    @property
    def dog_server_interface(self):
        return self._dog_server_interface
    
    @property
    def connected_dog(self):
        return self._dog_conneted
    
    @connected_dog.setter
    def connected_dog(self, connected):
        self._dog_conneted = connected

if __name__ == "__main__": HexInterface().root.mainloop()
