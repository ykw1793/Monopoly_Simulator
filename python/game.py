import pandas as pd
import numpy as np

from typing import Callable

import sys
import random
import datetime
import re

class Game:
    def __init__(self, num_players: int, run: bool=False):
        self.card_type_street: str = 'Street'
        self.card_type_railroad: str = 'Railroad'
        self.card_type_utility: str = 'Utility'

        self.jail_exit_method_stay: int = -1
        self.jail_exit_method_pay: int = 0
        self.jail_exit_method_card: int = 1
        self.jail_exit_method_roll_double: int = 2

        self.colors: list[str] = ['b', 'l', 'p', 'o', 'r', 'y', 'g', 'd']

        self.num_players: int = num_players
        self.active_players: list[int] = list(range(1, self.num_players+1))

        # self.seed = random.randrange(sys.maxsize)
        self.seed = 0
        random.seed(self.seed)

        self.cols: list[str] = [
            self.label_round(),
            self.label_player_idx(),
            self.label_dice_value(),
            self.label_bank_money()
        ]
        self.cols += [self.label_player_money(i+1) for i in range(num_players)]
        self.cols += [self.label_player_pos(i+1) for i in range(num_players)]

        for s in self.all_street_ids():
            self.cols += [self.label_street_owner(s), self.label_street_level(s)]
        for i in range(4):
            self.cols.append(self.label_railroad_owner(i+1))
        for i in range(2):
            self.cols.append(self.label_utility_owner(i+1))

        self.cols += [self.label_cc_jail_free_owner(), self.label_ch_jail_free_owner()]

        self.get_label_index: Callable[[str], int] = lambda label: self.cols.index(label)

        start_player: int = self.get_start_player_idx()

        self.data: list[list[int]] = []
        self.notes: list[str] = []
        self.note_entry: str = ''

        r: list[int] = [1, start_player, 0, 20580-num_players*1500]
        r += [1500] * num_players
        r += [0] * num_players
        r += [0] * (len(self.cols)-len(r))

        self.data.append(r)

        self.ch_lst: list[int] = list(range(1,17))
        random.shuffle(self.ch_lst)
        self.cc_lst: list[int] = list(range(1,17))
        random.shuffle(self.cc_lst)

        self.save_dir = './log'
        self.file_name = f'{self.save_dir}/data_ranseed{self.seed}_strtplyr{start_player}.csv'

        if run:
            self.run()

    #** Label methods **#

    def label_round(self) -> str: return 'Round'
    def label_player_idx(self) -> str: return 'Round Player'
    def label_dice_value(self) -> str: return 'Dice Value'
    def label_bank_money(self) -> str: return 'Bank Money'
    def label_player_pos(self, plyr_idx: int) -> str: return f'Player {plyr_idx} Pos'
    def label_player_money(self, plyr_idx: int) -> str: return f'Player {plyr_idx} Money'
    def label_street_owner(self, id: str) -> str: return f'{self.card_type_street} {id} Owner'
    def label_street_level(self, id: str) -> str: return f'{self.card_type_street} {id} Level'
    def label_railroad_owner(self, n: int) -> str: return f'{self.card_type_railroad} r{n}'
    def label_utility_owner(self, n: int) -> str: return f'{self.card_type_utility} u{n}'
    def label_cc_jail_free_owner(self) -> str: return 'CC Jail Free Card Owner'
    def label_ch_jail_free_owner(self) -> str: return 'CH Jail Free Card Owner'

    def extract_card_type(self, s: str) -> str: return s.split()[0]
    def extract_card_id(self, s: str) -> str: return s.split()[1]
    def extract_card_color_from_id(self, id: str) -> str: return id[0]
    def extract_card_color_idx_from_id(self, id: str) -> int: return self.colors.index(self.extract_card_color_from_id(id))
    def extract_card_idx_from_id(self, id: str) -> int: return int(id[1])

    def all_street_ids(self) -> list[str]:
        sts: list[tuple[str, int]] = list(zip(self.colors, [2] + ([3] * (len(self.colors)-2)) + [2]))
        ret: list[str] = []
        for c,i in sts:
            for j in range(1, i+1):
                ret.append(f'{c}{j}')
        return ret

    #** Get methods **#

    def get_data(self, label: str, idx: int=-1) -> int: return self.data[idx][self.get_label_index(label)]
    def get_round(self, idx: int=-1) -> int: return self.get_data(self.label_round(), idx)
    def get_money(self, plyr_idx: int, idx: int=-1) -> int: return self.get_data(self.label_bank_money() if plyr_idx == 0 else self.label_player_money(plyr_idx), idx)
    def get_bank_money(self, idx: int=-1) -> int: return self.get_money(0, idx)
    def get_player_money(self, plyr_idx: int, idx: int=-1) -> int: return self.get_money(plyr_idx, idx)
    def get_player_idx(self, idx: int=-1) -> int: return self.get_data(self.label_player_idx(), idx)
    def get_dice_value(self, idx: int=-1) -> int: return self.get_data(self.label_dice_value(), idx)
    def get_player_pos(self, plyr_idx: int, idx: int=-1) -> int: return self.get_data(self.label_player_pos(plyr_idx), idx)
    def get_card_owner(self, pos: int, idx: int=-1) -> int: return self.get_data(self.pos_to_card(pos), idx)
    def get_cc_jail_free_owner(self, idx: int=-1) -> int: return self.get_data(self.label_cc_jail_free_owner(), idx)
    def get_ch_jail_free_owner(self, idx: int=-1) -> int: return self.get_data(self.label_ch_jail_free_owner(), idx)

    def get_street_level(self, id_pos: str | int, idx: int=-1) -> int:
        if type(id_pos) == int:
            id = self.extract_card_id(self.pos_to_card(id_pos))
            return self.get_data(self.label_street_level(id), idx)
        elif type(id_pos) == str:
            return self.get_data(self.label_street_level(id_pos), idx)
        else:
            raise TypeError

    def get_card_level(self, label: str) -> int:
        if self.extract_card_type(label) == self.card_type_street:
            self.get_street_level(self.extract_card_id(label))
        else:
            return 0

    def get_all_card_owner_data(self, idx: int=-1) -> dict[str, int]:
        label = self.label_street_owner('').split()
        cols = [x for x in self.cols if x.split()[::2] == label]
        cols += [x for x in self.cols if self.extract_card_type(x) == self.card_type_railroad]
        cols += [x for x in self.cols if self.extract_card_type(x) == self.card_type_utility]
        return {k: self.get_data(k, idx) for k in cols}

    #** Set methods **#

    def set_data(self, label: str, val: int) -> None: self.data[-1][self.get_label_index(label)] = val
    def set_round(self, val: int) -> None: self.set_data(self.label_round(), val)
    def set_money(self, plyr_idx: int, val: int) -> None: return self.set_data(self.label_bank_money() if plyr_idx == 0 else self.label_player_money(plyr_idx), val)
    def set_bank_money(self, val: int) -> None: return self.set_money(0, val)
    def set_player_money(self, plyr_idx: int, val: int) -> None: return self.set_money(plyr_idx, val)
    def set_player_idx(self, val: int) -> None: return self.set_data(self.label_player_idx(), val)
    def set_dice_value(self, val: int) -> None: return self.set_data(self.label_dice_value(), val)
    def set_player_pos(self, plyr_idx: int, val: int) -> None: return self.set_data(self.label_player_pos(plyr_idx), val)
    def set_card_owner(self, pos: int, plyr_idx: int) -> None: return self.set_data(self.pos_to_card(pos), plyr_idx)
    def set_cc_jail_free_owner(self, plyr_idx: int) -> int: return self.get_data(self.label_cc_jail_free_owner(), plyr_idx)
    def set_ch_jail_free_owner(self, plyr_idx: int) -> int: return self.get_data(self.label_ch_jail_free_owner(), plyr_idx)

    def add_note_entry(self, note: str, end: str=';') -> None:
        self.note_entry += note + end

    def reset_note_entry(self) -> None: self.note_entry = ''

    def add_note_to_list(self) -> None:
        self.notes.append(self.note_entry)
        self.reset_note_entry()

    #** Single liners **#

    def has_enough_money(self, plyr_idx: int, amt: int) -> bool: return self.get_money(plyr_idx) >= amt
    def player_in_jail(self, plyr_idx: int, idx: int=-1) -> bool: return self.get_data(self.label_player_pos(plyr_idx), idx) == -1
    def sum_dice_value(self, dice_value: int | list[int]) -> int:
        if type(dice_value) == int:
            return (dice_value//10) + (dice_value%10)
        elif type(dice_value) == list:
            return dice_value[0] + dice_value[1]

    def go_to_jail(self, plyr_idx: int) -> None:
        ret = self.move(plyr_idx, -1, False, False)
        self.add_note_entry(f'gtj.p{plyr_idx}')
        return ret

    #** Info methods **#

    def street_id_to_street_idx(self, id: str) -> int:
        color_idx = self.extract_card_color_idx_from_id(id)
        return (3 * color_idx) + self.extract_card_idx_from_id(id) - 1

    def cost(self, pos: int) -> int:
        label = self.pos_to_card(pos)
        typ = self.extract_card_type(label)
        if typ == self.card_type_street:
            d = [60, 60, None, 100, 100, 120, 140, 140, 160, 180, 180, 200,
                 220, 220, 240, 260, 260, 280, 300, 300, 320, 350, 400, None]
            return d[self.street_id_to_street_idx(self.extract_card_id(label))]
        elif typ == self.card_type_railroad:
            return 200
        else: # utility
            return 150
        
    def rent(self, pos: int) -> int:
        label = self.pos_to_card(pos)
        typ = self.extract_card_type(label)
        id = self.extract_card_id(label)
        if typ == self.card_type_street:
            d = [[2, 4, 10, 30, 90, 160, 250],
                 [4, 8, 20, 60, 180, 320, 450],
                 None,
                 [6, 12, 30, 90, 270, 400, 550],
                 [6, 12, 30, 90, 270, 400, 550],
                 [8, 16, 40, 100, 300, 450, 600],
                 [10, 20, 50, 150, 450, 625, 750],
                 [10, 20, 50, 150, 450, 625, 750],
                 [12, 24, 60, 180, 500, 700, 900],
                 [14, 28, 70, 200, 550, 750, 950],
                 [14, 28, 70, 200, 550, 750, 950],
                 [16, 32, 80, 220, 600, 800, 1000],
                 [18, 36, 90, 250, 700, 875, 1050],
                 [18, 36, 90, 250, 700, 875, 1050],
                 [20, 40, 100, 300, 750, 925, 1100],
                 [22, 44, 110, 330, 800, 975, 1150],
                 [22, 44, 110, 330, 800, 975, 1150],
                 [24, 48, 120, 360, 850, 1025, 1200],
                 [26, 52, 130, 390, 900, 1100, 1275],
                 [26, 52, 130, 390, 900, 1100, 1275],
                 [28, 56, 150, 450, 1000, 1200, 1400],
                 [35, 70, 175, 500, 1100, 1300, 1500],
                 [50, 100, 200, 600, 1400, 1700, 2000],
                 None]
            lvl = self.get_street_level(pos)
            return d[self.street_id_to_street_idx(id)][lvl]
        elif typ == self.card_type_railroad:
            l = [1,2,3,4]
            l.remove(self.extract_card_idx_from_id(id))
            cnt = 1
            owner = self.get_card_owner(pos)
            for i in l:
                cnt += int(self.get_data(self.label_railroad_owner(i)) == owner)
            rl = [25, 50, 100, 200]
            return rl[cnt-1]
        else:
            owner = self.get_card_owner(pos)
            idx = self.extract_card_idx_from_id(id)
            mul = 4 + 6 * int(self.get_data(self.label_utility_owner(1 if idx == 2 else 2)) == owner)
            return mul * self.sum_dice_value(self.get_dice_value())
        
    def house_hotel_price(self, label: str) -> int:
        color_idx = self.extract_card_color_idx_from_id(label)
        return 50*((color_idx//2)+1)
        
    def num_houses(self, card_lvl: int) -> int:
        if card_lvl in [-1,0,1,6]:
            return 0
        return card_lvl-1
    
    def num_hotels(self, card_lvl: int) -> int:
        return card_lvl//6
    
    def mortgage_value(self, label: str) -> int:
        typ: str = self.extract_card_type(label)
        if typ == self.card_type_street:
            vals: list[int] = [30] * 2
            for v in range(50, 170, 20):
                vals += [v] * 2
                vals.append(v+10)
            vals += [175, 200]
            vals[self.extract_card_idx_from_id(self.extract_card_id(label))]
        elif typ == self.card_type_railroad:
            return 100
        else:
            return 75

    #** Pay methods **#

    def pay(self, to, fr, amt, note_desc: str=''):
        assert not (to == 0 and fr == 0)
        if not self.has_enough_money(fr, amt):
            if fr == 0:
                self.set_bank_money(amt)
            else:
                tot = self.total_assets(fr)
            
        self.set_money(to, self.get_money(to) + amt)
        self.set_money(fr, self.get_money(fr) - amt)

        if note_desc:
            note_desc = f'({note_desc})'
        self.add_note_entry(f'p{note_desc}.p{fr}>p{to}.${amt}')

    def pay_rent(self, plyr_idx: int, pos: int, ch: bool=False):
        if ch:
            if pos in [5,15,25,35]: # Railroad
                self.pay(self.get_card_owner(pos), plyr_idx, 2*self.rent(pos))
            elif pos in [12,28]: # Utility
                dice = self.roll_dice()
                self.pay(self.get_card_owner(pos), plyr_idx, 10*self.sum_dice_value(dice))
        else:
            self.pay(self.get_card_owner(pos), plyr_idx, self.rent(pos), 'r')

    def pay_street_repairs(self, plyr_idx: int, val: list[int] | tuple[int]):
        num_houses: int = 0
        num_hotels: int = 0
        owner_data: dict[str, int] = self.get_all_card_owner_data()
        for label, owner in owner_data.items():
            if owner == plyr_idx:
                lvl: int = self.get_card_level(label)
                num_houses += self.num_houses(lvl)
                num_hotels += self.num_hotels(lvl)
        amt: int = (num_houses * val[0]) + (num_hotels * val[1])
        self.pay_bank(plyr_idx, amt)
    
    def pay_bank(self, plyr_idx: int, amt: int): return self.pay(0, plyr_idx, amt)
    def pay_go(self, plyr_idx): return self.pay(plyr_idx, 0, 200, 'g')
    def pay_jail(self, plyr_idx): return self.pay(0, plyr_idx, 50, 'j')
    def pay_inctax(self, plyr_idx): return self.pay(0, plyr_idx, 200, 'it')
    def pay_luxtax(self, plyr_idx): return self.pay(0, plyr_idx, 100, 'lt')

    #** Other methods **#

    def buy(self, plyr_idx: int, pos: int) -> None:
        cost: int = self.cost(pos)
        self.pay_bank(plyr_idx, cost)
        self.set_card_owner(pos, plyr_idx)
        self.add_note_entry(f'b.p{plyr_idx}.c{pos}({self.extract_card_id(self.pos_to_card(pos))})')

    def buy_or_pay_rent(self, plyr_idx, ch: bool=False):
        pos: int = self.get_player_pos(plyr_idx)
        card_owner: int = self.get_card_owner(pos)
        if card_owner == 0: # Not owned
            self.buy(plyr_idx, pos)
        else: # Owned
            self.pay_rent(plyr_idx, pos, ch)

    def ch(self, plyr_idx: int):
        self.add_note_entry(f'ch.p{plyr_idx}', end='.')
        i = self.ch_lst.pop(0)
        if self.eval_ch(i, plyr_idx):
            self.ch_lst.append(i)
        else:
            self.set_ch_jail_free_owner(plyr_idx)

    def eval_ch(self, i: int, plyr_idx: int):
        match i:
            case 1: # get out of jail free card
                self.add_note_entry('gjf')
            case n if 1 < n < 7: # move to pos
                d: dict[int, int] = {2:39, 3:0, 4:24, 5:11, 6:5}
                self.add_note_entry(f'mv{d[i]}')
                self.move_and_evaluate(plyr_idx, d[i], False)
            case n if 6 < n < 10:  # nearest railroad/utility
                if i == 9:
                    self.add_note_entry('nu')
                    d: dict[int, int] = {7:12, 22:28, 36:12}
                else:
                    self.add_note_entry('nrr')
                    d: dict[int, int] = {7:15, 22:25, 36:5}
                pos = d[self.get_player_pos(plyr_idx)]
                self.move(plyr_idx, pos, False)
                self.buy_or_pay_rent(plyr_idx, True)
            case 10 | 11: # collect money
                d: dict[int, int] = {10:50, 11:150}
                self.add_note_entry(f'g{d[i]}')
                self.pay(plyr_idx, 0, d[i])
            case 12: # move back 3
                self.add_note_entry('bk3')
                self.move_and_evaluate(plyr_idx, -3)
            case 13: # go to jail
                self.add_note_entry('gtj')
                self.go_to_jail(plyr_idx)
            case 14: # street repairs
                self.add_note_entry('rep')
                self.pay_street_repairs(plyr_idx, [25, 100])
            case 15: # pay 15
                self.add_note_entry('p15')
                self.pay_bank(plyr_idx, 15)
            case 16: # pay each player 50
                self.add_note_entry('pep')
                for p in self.active_players:
                    if p != plyr_idx:
                        self.pay(p, plyr_idx, 50)
        return i > 1 # keep get out of jail free card

    def cc(self, plyr_idx: int):
        self.add_note_entry(f'cc.p{plyr_idx}', end='.')
        i = self.cc_lst.pop(0)
        if self.eval_cc(i, plyr_idx):
            self.cc_lst.append(i)
        else:
            self.set_cc_jail_free_owner(plyr_idx)

    def eval_cc(self, i: int, plyr_idx: int):
        match i:
            case 1: # get out of jail free card
                self.add_note_entry('gjf')
            case 2: # move to go
                self.add_note_entry('mv0')
                self.move_and_evaluate(plyr_idx, 0, False)
            case n if 2 < n < 11: # collect money
                d: dict[int, int] = {3:200, 4:50, 5:100, 6:20, 7:100, 8:25, 9:10, 10:100}
                self.add_note_entry(f'g{d[i]}')
                self.pay(plyr_idx, 0, d[i])
            case n if 10 < n < 14: # pay money
                d: dict[int, int] = {11:50, 12:100, 13:50}
                self.add_note_entry(f'p{d[i]}')
                self.pay_bank(plyr_idx, d[i])
            case 14: # go to jail
                self.add_note_entry('gtj')
                self.go_to_jail(plyr_idx)
            case 15: # collect 10 from each player
                self.add_note_entry('cep')
                for p in self.active_players:
                    if p != plyr_idx:
                        self.pay(plyr_idx, p, 10)
            case 16: # street repairs
                self.add_note_entry('rep')
                self.pay_street_repairs(plyr_idx, [40, 115])
        return i > 1 # keep get out of jail free card

    def get_start_player_idx(self) -> int:
        return self.active_players[0]

    def move(self, plyr_idx: int, n: int, rel: bool=True, collect_go: bool=True) -> None:
        old_pos: int = self.get_player_pos(plyr_idx)
        new_pos: int = (old_pos + n) % 40 if rel else n
        self.set_player_pos(plyr_idx, new_pos)
        if new_pos < old_pos and collect_go:
            self.pay_go(plyr_idx)

    def eval_pos(self, plyr_idx: int):
        pos = self.get_data(self.label_player_pos(plyr_idx))
        if pos in [10,20]: # jail/free parking
            self.add_note_entry('pass')
            pass
        elif pos == 30: # go to jail
            self.go_to_jail(plyr_idx)
        elif pos in [2, 17, 33]:
            self.cc(plyr_idx)
        elif pos in [7, 22, 36]:
            self.ch(plyr_idx)
        else:
            self.buy_or_pay_rent(plyr_idx)

    def move_and_evaluate(self, plyr_idx: int, n: int, rel: bool=True, collect_go: bool=True):
        self.move(plyr_idx, n, rel, collect_go)
        self.eval_pos(plyr_idx)
    
    def pos_to_card(self, pos: int) -> str:
        if pos in [5,15,25,35]:
            return self.label_railroad_owner((pos//10)+1)
        elif pos in [12,28]:
            return self.label_utility_owner(pos//12)
        else:
            color: str = self.colors[pos//5]
            if color in ['b', 'd']:
                idx = int(pos in [3,39])+1
            else:
                if pos == (pos//5)*5+1:
                    idx = 1
                elif pos == (pos//5)*5+4:
                    idx = 3
                else:
                    idx = 2
            return self.label_street_owner(color + str(idx))
    
    def roll_dice(self, n=1):
        l = []
        for _ in range(n):
            l.append([random.randint(1,6), random.randint(1,6)])
        return l
    
    def add_data_row(self, same_player: bool=False) -> None:
        self.add_note_to_list()
        self.data.append(self.data[-1].copy())
        self.increment_round(same_player)
    
    def increment_round(self, same_player: bool=False) -> None:
        if not same_player:
            next_idx = (self.active_players.index(self.get_player_idx()) + 1) % self.num_players
            next_player = self.active_players[next_idx]
            self.set_data(self.label_player_idx(), next_player)
            if next_player == self.get_data(self.label_player_idx(), 0):
                self.set_round(self.get_round() + 1)

    def choose_jail_exit_method(self, plyr_idx: int):
        return self.jail_exit_method_pay

    def get_out_of_jail(self, plyr_idx: int) -> tuple[bool,bool]:
        method = self.choose_jail_exit_method(plyr_idx)
        if method == self.jail_exit_method_stay:
            return False, False
        if method == self.jail_exit_method_pay:
            self.pay_jail(plyr_idx)
            self.set_player_pos(plyr_idx, 10)
            return True, True
        if method == self.jail_exit_method_card:
            raise NotImplementedError
        if method == self.jail_exit_method_roll_double:
            dice = self.roll_dice()
            if dice[0] == dice[1]:
                self.set_player_pos(plyr_idx, 10 + self.sum_dice_value(dice))
                return True, False

    def declare_bankrupcy(self, plyr_idx: int) -> None:
        self.active_players.remove(plyr_idx)

    def is_bankrupt(self, plyr_idx: int) -> bool:
        return self.get_player_money(plyr_idx) < 0
    
    def total_assets(self, plyr_idx: int) -> int:
        tot: int = self.get_player_money(plyr_idx)
        owner_data: dict[str, int] = self.get_all_card_owner_data()
        for label, owner in owner_data.items():
            if owner == plyr_idx:
                lvl = self.get_card_level(label)
                num_houses = self.num_houses(lvl)
                num_hotels = self.num_hotels(lvl)
                mortgage = self.mortgage_value(label)
                tot += mortgage + (num_houses*self.house_hotel_price(label)) + ()
                
    def execute_non_turn_moves(self, plyr_idx: int):
        pass

    def exit_loop(self) -> bool:
        cnt = 0
        for plyr_idx in range(1, self.num_players+1):
            cnt += int(not self.is_bankrupt(plyr_idx))
        return cnt == 1

    def run(self):
        doubles = lambda l: l[0] == l[1]
        dice_value = lambda l: int(f'{l[0]}{l[1]}')

        while True:
        # while not self.exit_loop() or self.get_round() > 100:
            if self.exit_loop():
                print('exit condition')
                break
            if self.get_round() > 30:
                print('exit rounds')
                break

            roll_dice = True
            plyr_idx = self.get_player_idx()

            for p in self.active_players:
                if p == plyr_idx:
                    continue
                self.execute_non_turn_moves(p) # trading, buying, selling

            if self.player_in_jail(plyr_idx):
                got_out, roll_dice = self.get_out_of_jail(plyr_idx)
                if not got_out:
                    self.add_data_row()
                    continue
            if roll_dice:
                dice_rolls = self.roll_dice(3)
                dbl = [doubles(l) for l in dice_rolls]
                if all(dbl):
                    self.go_to_jail(plyr_idx)
                for i in range(len(dbl)):
                    self.set_dice_value(dice_value(dice_rolls[i]))
                    self.move_and_evaluate(plyr_idx, sum(dice_rolls[i]))
                    if dbl[i] == False:
                        break
                    self.add_data_row(same_player=True)
                self.add_data_row()

        self.data.pop()
        self.save()
        
    def save(self) -> None:
        arr = pd.DataFrame(self.data, columns=self.cols)
        arr['Notes'] = self.notes
        arr.to_csv(self.file_name, index=False)

if __name__ == '__main__':
    g = Game(2)
    g.run()