from TTLeague import Match, Game, Player
from time import sleep
from socketIO_client import SocketIO, LoggingNamespace
import json

# init empty configuration
config = {}

try:
   # try to load config from file
   config = json.load(open('config.json'))
except Exception, e:
   print('Error while getting config: '+ str(e))
   exit()


socketIO = None

players = []

def on_connect():
    print('connect')
    print("Let's scan a tag please ...")
    print("... got one: e142df52")
    print("sending socket message ...")
    socketIO.emit('requestPlayerByTagId', {'tagId': 'e142df52'})

    sleep(2)

    print("Let's scan a tag please ...")
    print("... got one: a3e572ef")
    print("sending socket message ...")
    socketIO.emit('requestPlayerByTagId', {'tagId': 'a3e572ef'})

    sleep(2)

def on_refresh_data(*args):
    print('refreshedData', args)
    socketIO.disconnect()

def on_result_player(*args):
    print("received Player name: " + args[0]['name'] + " with tagId: " + args[0]['tagId'])
    players.append(Player(args[0]['tagId'], args[0]['name']))
    if len(players) == 2:
        print("Got 2 players: "+ str([p.__dict__ for p in players]))
        add_match()

def add_match():
    if len(players) == 2:
        print("will add a match with 3 sets ...")
        m = Match(players[0], players[1])
        g1 = Game(14, 12)
        g2 = Game(5, 11)
        g3 = Game(11, 6)
        m.add_game(g1)
        m.add_game(g2)
        m.add_game(g3)
        matchDatas = m.get_match_data()
        print("Match data to send: "+ str(matchDatas))
        socketIO.emit('addMatch', matchDatas)


socketIO = SocketIO(config['url'], verify=False)
socketIO.on('connect', on_connect)
socketIO.on('refreshedData', on_refresh_data)
socketIO.on('resultPlayer', on_result_player)
socketIO.wait()




