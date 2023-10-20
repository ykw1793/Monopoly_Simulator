from game import Game
from analysis import Analyser

if __name__ == '__main__':
    game = Game(4)
    try:
        game.run()
    except NotImplementedError:
        print('not implemented error raised')
        pass
    analyser = Analyser(game)
    