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
last_players_names = []

players = []

def on_connect():
    print('connect')
    print("Let's scan a tag please ...")
    print("... got one: e142df52")
    print("sending socket message ...")
    socketIO.emit('requestPlayerByTagId', {'tagId': 'e41248e7'})

    sleep(2)

    print("Let's scan a tag please ...")
    print("... got one: 8848087")
    print("sending socket message ...")
    socketIO.emit('requestPlayerByTagId', {'tagId': '8848087'})

    sleep(2)

def on_refresh_data(*args):
    print('refreshedData', args)
    data = args[0]
    elo_changes = {}
    print("data type: "+ str(type(data)))
    print(str(data['players']))
    print("players type: " + str(type(data['players'])))
    print('last players names'+ str(last_players_names))
    for player in data['players']:
        if player['name'] in last_players_names:
            print(player['name'] + ' '+ str(player['eloChange']))
            elo_changes.update({player['name']: player['eloChange']})

    for player, change in elo_changes.items():
        msg = '{:11s} {:4d}'.format(player, change)
        for c in msg:
            print(c)
    socketIO.disconnect()

def on_result_player(*args):
    global last_players_names
    print("received Player name: " + args[0]['name'] + " with tagId: " + args[0]['tagId'])
    players.append(Player(args[0]['tagId'], args[0]['name']))
    if len(players) == 2:
        print("Got 2 players: "+ str([p.__dict__ for p in players]))
        last_players_names = [ players[0].name, players[1].name ]
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
socketIO.wait(seconds=30)




