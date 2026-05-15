import logging
logger = logging.getLogger(__name__)

class TicTacToeGame:
    def __init__(self) -> None:
        self.board = [" " for _ in range(9)]
        self.current_player = "X"
        logger.info("Nowa gra w kółko i krzyżyk została zainicjalizowana.")
    def make_move(self, position) -> bool:
        if not (0 <= position <= 8):
            logger.warning(f"Próba ruchu poza planszę: {position}")
            return False
        if self.board[position] != " ":
            logger.warning(f"Próba ruchu na zajęte pole: {position}")
            return False
        else:
            self.board[position] = self.current_player
            logger.info(f"Gracz {self.current_player} zajął pole {position}")
            if self.current_player == "X":
                self.current_player = "O"
            else:
                self.current_player = "X"
        return True

    def display_board(self) -> None:
        # Pobieramy wartości z listy i układamy je w rzędy
        print(f" {self.board[0]} | {self.board[1]} | {self.board[2]} ")
        print("-----------")
        print(f" {self.board[3]} | {self.board[4]} | {self.board[5]} ")
        print("-----------")
        print(f" {self.board[6]} | {self.board[7]} | {self.board[8]} ")

    def check_winner(self) -> str | None:
        win_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8), # poziomy
        (0, 3, 6), (1, 4, 7), (2, 5, 8), # piony
        (0, 4, 8), (2, 4, 6)             # skosy
        ]
        for a, b, c in win_combinations:
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] != " ":
                logger.info(f"Gra zakończona. Wygrywa: {self.board[a]}")
                return self.board[a]
        if " " not in self.board:
            logger.info("Gra zakończona. Remis.")
            return "Draw"
        return None
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    game = TicTacToeGame()
    while True:
        game.display_board()
        try: 
            ruch = int(input(f"Gracz {game.current_player}, podaj numer pola (0-8):"))
            wykonanie_ruchu = game.make_move(ruch)
            if not wykonanie_ruchu:
                print("Pozycja jest już zajęta. Spróbuj innej :)")
            if wykonanie_ruchu:
                print(wykonanie_ruchu)
            wynik_gry = game.check_winner()
            if wynik_gry:
                game.display_board()
                if wynik_gry == "Draw":
                    print("Wynik to Remis!")
                else:
                    print(f"Wygrała osoba grająca jako: {wynik_gry}")
                break
        except (TypeError, ValueError, IndexError):
            print("Podaj liczbę od 0 do 8")
            continue
