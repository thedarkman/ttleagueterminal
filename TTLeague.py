import time
import json

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
 
  # data format for each match data: { w: 'Horst', l: 'Steffen Krause', diff: 2, date: 1490262281602 }
  def getMatchDatasAsJson(self):
      data = []
      homePoints = 0
      guestPoints = 0
      for g in self.games:
         if g.home > g.guest:
            w = self.player1.name
            l = self.player2.name
            diff = g.home -g.guest
         else:
            w = self.player2.name
            l = self.player1.name
            diff = g.guest - g.home
         print('home: {:d}, guest: {:d}'.format(homePoints, guestPoints))
         data.append({'w': w, 'l': l, 'diff': diff, 'timestamp': g.timestamp})
      return json.dumps(data)
         
 
  def __str__(self):
    games_str = json.dumps([g.__dict__ for g in self.games]) 
    return "Match: {} vs {}; Sets: {}".format(str(self.player1), str(self.player2), games_str)

class Game:
  def __init__(self, home=0, guest=0):
    self.home = home
    self.guest = guest
    self.timestamp = int(time.time()*1000)

  def __str__(self):
    return str(self.__dict__)

class Player:
  def __init__(self, nfcTag="", name=""):
    self.nfcTag = nfcTag
    self.name = name  

  def __str__(self):
    return str(self.__dict__)
