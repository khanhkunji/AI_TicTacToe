
from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import List, Optional, Tuple

# Board values
# EMPTY = 0, HUMAN = -1, AI = +1
Cell = int
Board = List[List[Cell]]


def other(player: int) -> int:
    return -player


def make_board() -> Board:
    return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


def coords_from_choice(choice: int) -> Tuple[int, int]:
    """Map 1..9 to (row, col) in reading order.
    1 2 3
    4 5 6
    7 8 9
    """
    idx = choice - 1
    return divmod(idx, 3)


def empty_cells(board: Board) -> List[Tuple[int, int]]:
    cells: List[Tuple[int, int]] = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                cells.append((i, j))
    return cells


def wins(board: Board, player: int) -> bool:
    win_states = [
        # rows
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        # cols
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        # diagonals
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]
    for line in win_states:
        if all(board[i][j] == player for i, j in line):
            return True
    return False


def game_over(board: Board) -> bool:
    return wins(board, +1) or wins(board, -1) or not empty_cells(board)


def evaluate(board: Board, ai_player: int) -> int:
    """Return +1 if AI wins, -1 if Human wins, 0 otherwise from AI perspective."""
    if wins(board, ai_player):
        return +1
    if wins(board, other(ai_player)):
        return -1
    return 0


@dataclass
class MinimaxResult:
    row: int
    col: int
    score: int


def minimax_alpha_beta(
    board: Board,
    depth: int,
    current: int,
    ai_player: int,
    alpha: int,
    beta: int,
) -> MinimaxResult:
    """
    Alpha-Beta Minimax with depth-based tie-break:
    - earlier wins are better, later losses are better
    Score scaled by (10 + depth) so that win at higher remaining depth is stronger.
    """
    if depth == 0 or game_over(board):
        base = evaluate(board, ai_player)
        return MinimaxResult(-1, -1, base * (10 + depth))

    best_row, best_col = -1, -1

    if current == ai_player:
        max_eval = -10_000
        for (i, j) in empty_cells(board):
            board[i][j] = current
            res = minimax_alpha_beta(board, depth - 1, other(current), ai_player, alpha, beta)
            board[i][j] = 0
            if res.score > max_eval:
                max_eval = res.score
                best_row, best_col = i, j
            alpha = max(alpha, res.score)
            if beta <= alpha:
                break  # beta cut-off
        return MinimaxResult(best_row, best_col, max_eval)
    else:
        min_eval = +10_000
        for (i, j) in empty_cells(board):
            board[i][j] = current
            res = minimax_alpha_beta(board, depth - 1, other(current), ai_player, alpha, beta)
            board[i][j] = 0
            if res.score < min_eval:
                min_eval = res.score
                best_row, best_col = i, j
            beta = min(beta, res.score)
            if beta <= alpha:
                break  # alpha cut-off
        return MinimaxResult(best_row, best_col, min_eval)


@dataclass
class TicTacToe:
    ai_symbol: str = "O"  # default AI 'O'
    human_symbol: str = "X"
    ai_player: int = +1
    board: Board = field(default_factory=make_board)
    difficulty: str = "1"  # easy, normal, hard, impossible

    def _difficulty_params(self) -> tuple[float, int, bool]:
        """Return (p_random, depth_limit, use_center_heuristic)."""
        diff = self.difficulty.lower()
        if diff == "1":
            return 0.6, 1, False
        if diff == "2":
            return 0.2, 3, False
        if diff == "3":
            return 0.05, 9, True
        # impossible
        return 0.0, 9, True

    def symbol_for(self, cell: int) -> str:
        if cell == +1:
            return self.ai_symbol
        if cell == -1:
            return self.human_symbol
        return " "

    def render(self) -> None:
        # Show numbers for empty cells to guide the player
        cells = []
        for i in range(3):
            row_display = []
            for j in range(3):
                cell = self.board[i][j]
                if cell == 0:
                    idx = i * 3 + j + 1
                    row_display.append(str(idx))
                else:
                    row_display.append(self.symbol_for(cell))
            cells.append(row_display)

        print("\nCurrent board:")
        for r in range(3):
            print(" " + " | ".join(cells[r]))
            if r < 2:
                print("---+---+---")

    def human_move(self) -> None:
        while True:
            try:
                choice = int(input("Chọn ô (1-9): ").strip())
            except ValueError:
                print("Nhập số 1..9.")
                continue
            if not (1 <= choice <= 9):
                print("Ngoài phạm vi 1..9.")
                continue
            i, j = coords_from_choice(choice)
            if self.board[i][j] != 0:
                print("Ô đã được đánh.")
                continue
            self.board[i][j] = -1
            break

    def ai_move(self) -> None:
        empties = empty_cells(self.board)
        depth = len(empties)
        p_random, depth_limit, use_center = self._difficulty_params()

        # Random mistake with probability p_random
        if empties and random.random() < p_random:
            i, j = random.choice(empties)
            self.board[i][j] = self.ai_player
            return

        # Optional first-move center heuristic for harder levels
        if use_center and depth == 9 and self.board[1][1] == 0:
            i, j = 1, 1
            self.board[i][j] = self.ai_player
            return

        eff_depth = min(depth, depth_limit)
        if eff_depth == 0:
            # no lookahead left; pick first legal
            i, j = empties[0]
            self.board[i][j] = self.ai_player
            return

        res = minimax_alpha_beta(
            self.board, eff_depth, self.ai_player, self.ai_player, alpha=-10_000, beta=10_000
        )
        i, j = res.row, res.col
        if i == -1:
            i, j = empties[0]
        self.board[i][j] = self.ai_player

    def status(self) -> Optional[str]:
        if wins(self.board, self.ai_player):
            return "AI thắng."
        if wins(self.board, other(self.ai_player)):
            return "Bạn thắng."
        if not empty_cells(self.board):
            return "Hòa."
        return None

    def play(self) -> None:
        print("Cờ ca-rô 3x3. Bạn là 'X', AI là 'O' (mặc định).")
        # Choose difficulty
        diff = input("""Chọn độ khó\n1.easy\n2.normal\n3.hard\n4.impossible\n(mặc định normal): """).strip().lower()
        print(f"Bạn chọn chế độ {diff}\n")
        if diff in {"1", "2", "3", "4"}:
            self.difficulty = diff
        else:
            self.difficulty = "normal"
        # Let user choose symbol
        choose = input("Bạn muốn đi 'X' trước hay 'O' sau? (X/O, mặc định X): ").strip().upper()
        if choose == "O":
            # Human is O, AI is X
            self.human_symbol, self.ai_symbol = "O", "X"
            self.ai_player = -1  # AI uses -1 now, human uses +1
            # flip existing board encoding by interpreting input functions accordingly
            # To keep logic simple, we instead swap meaning of human moves:
            print("Bạn đi sau.")
        else:
            print("Bạn đi trước.")

        self.render()

        # Define turn order based on symbols:
        # Internal encoding is: human = -1, AI = +1 by default.
        # If the user chose O, we keep board math the same but adjust input/labels.
        # Turn order:
        human_turn = True if choose != "O" else False

        while True:
            if human_turn:
                self.human_move()
            else:
                self.ai_move()

            self.render()
            s = self.status()
            if s:
                print(s)
                break
            human_turn = not human_turn


def main() -> None:
    game = TicTacToe()
    game.play()


if __name__ == "__main__":
    main()
