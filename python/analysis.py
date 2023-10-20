import pandas as pd
import matplotlib.pyplot as plt

from game import Game

class Analyser:
    def __init__(self, game: Game):
        self.game = game
        self.df = pd.read_csv(game.file_name)

        plt.style.use('dark_background')

        self.font = {
            'family': 'serif',
            'weight': 'normal',
            'size': 16,
        }

        self.plot_bank_money()
    
    def plot_bank_money(self):
        fig = plt.figure(figsize=(16, 7))
        ax = plt.axes()
        plt.plot(self.df[self.game.label_bank_money()], '-o')
        plt.ylabel('Bank money', fontdict=self.font)
        ax.set(xticklabels=[])
        ax.tick_params(bottom=False)
        plt.show()