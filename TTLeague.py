import time
import json


class TTLeague:
    def __init__(self, setCount=3):
        self.setCount = setCount

    def __str__(self):
        return str(self.__dict__)


class Match:
    def __init__(self, player1, player2):
        # type: (Player, Player) -> None
        self.timestamp = int(time.time() * 1000)
        self.games = []
        self.player1 = player1
        self.player2 = player2

    def add_game(self, game):
        # type: (Game) -> None
        self.games.append(game)

    # data format for each match data: { w: 'Horst', l: 'Steffen Krause', diff: 2, date: 1490262281602 }
    def match_data_as_json(self):
        # type: (None) -> str
        data = self.get_match_data()
        return json.dumps(data)

    def get_match_data(self):
        # type: (None) -> dict
        data = []
        for g in self.games:
            if g.home > g.guest:
                w = self.player1.name
                l = self.player2.name
                diff = g.home - g.guest
            else:
                w = self.player2.name
                l = self.player1.name
                diff = g.guest - g.home
            self.timestamp += 1
            data.append({'w': w, 'l': l, 'diff': diff, 'date': self.timestamp})
        return data

    def __str__(self):
        games_str = json.dumps([g.__dict__ for g in self.games])
        return "Match: {} vs {}; Sets: {}".format(str(self.player1), str(self.player2), games_str)


class Game:
    def __init__(self, home=0, guest=0):
        self.home = home
        self.guest = guest

    def __str__(self):
        return str(self.__dict__)


class Player:
    def __init__(self, nfcTag="", name=""):
        self.nfcTag = nfcTag
        self.name = name

    def __str__(self):
        return str(self.__dict__)
