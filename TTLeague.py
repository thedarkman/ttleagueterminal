

class TTLeague:
  def __init__(self, setCount=3):
    self.setCount = setCount

  def __str__(self):
    return str(self.__dict__)

class Match:
  def __init__(self, player1, player2):
      self.games = []
      self.player1 = player1
      self.player2 = player2

  def addGame(self, game):
      self.games.append(game)
  
  def __str__(self):
    games_str = ''
    for g in self.games:
      games_str += str(g)
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
