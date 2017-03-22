from TTLeague import Match, Game, Player
import requests
import json


p1 = Player("a3e572ef", "Simon")
p2 = Player("e142df52", "Jens")

m = Match(p1, p2)
g1 = Game(14, 12)
g2 = Game(11,9)
m.addGame(g1)
m.addGame(g2)

print(str(m))
