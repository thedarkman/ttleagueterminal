from TTLeague import Match, Game, Player
from time import sleep
import requests
import json


p1 = Player("a3e572ef", "Simon")
p2 = Player("e142df52", "Jens")

m = Match(p1, p2)
g1 = Game(14, 12)
sleep(2)
g2 = Game(5, 11)
sleep(1)
g3 = Game(11, 9)
m.addGame(g1)
m.addGame(g2)
m.addGame(g3)

print(str(m))
print(m.getMatchDatasAsJson())
