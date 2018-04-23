import numpy as np
import gym
import copy
import requests
import json as Json
import hashlib
from random import randint

import time

board = {
    "board": {
        "space": [{
            "type": "mancala",
            "marbles": 0,
            "space_id": 0,
            "player": 1
        },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 1,
                "player": 0
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 2,
                "player": 0
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 3,
                "player": 0
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 4,
                "player": 0
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 5,
                "player": 0
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 6,
                "player": 0
            },
            {
                "type": "mancala",
                "marbles": 0,
                "space_id": 7,
                "player": 0
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 8,
                "player": 1
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 9,
                "player": 1
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 10,
                "player": 1
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 11,
                "player": 1
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 12,
                "player": 1
            },
            {
                "type": "normal",
                "marbles": 4,
                "space_id": 13,
                "player": 1
            }
        ]
    }
}
currentBoard = copy.deepcopy(board)
totalTies=0
totalWins=0
totalLoses=0
alpha = 0.618
G = 0

env = gym.make("Taxi-v2")


def reset():
    global currentBoard
    currentBoard = copy.deepcopy(board)
    updateBoard(randint(0, 5))
    time.sleep(5)
    return int(hashlib.sha256(str(currentBoard['board']).encode('utf-8')).hexdigest(), 16) % 10 ** 8



print(env.action_space)
Q = None
try:
    Q = np.loadtxt('test2.txt')
    print('Loaded Trained Q Learner')
except OSError:
    print('No previous pretrained Q learner  found')
if Q is None:
    Q = np.zeros([(7 ** 10), 6])
    print('starting new Q learner')



def aiGo():
    global currentBoard
    global totalTies
    global totalLoses
    global totalWins
    headers = {'content-type': 'application/json'}
    json = str({'board': currentBoard['board']}).replace('\'', '\"')
    r = requests.post("http://127.0.0.1:8000/get_move", json=json, headers=headers)
    response = r.json()
    currentBoard = response
    state = int(hashlib.sha256(str(response['board']).encode('utf-8')).hexdigest(), 16) % 10 ** 8
    if response['go_again']:
        return aiGo()
    elif response['winner'] == 'player':
        totalWins+=1
        return state, 1, True, 1
    elif response['winner'] == 'AI':
        totalLoses+=1
        return state, -1, True, 1
    elif response['winner'] == 'tie':
        totalTies+=1
        return state, 0.75, True, 1
    else:
        return state, 0, False, 1


def updateBoard(move):
    move += 8
    global currentBoard
    global totalTies
    global totalLoses
    global totalWins
    state = int(hashlib.sha256(str(currentBoard['board']).encode('utf-8')).hexdigest(), 16) % 10 ** 8
    if currentBoard['board']['space'][move]['marbles'] == 0:
        return state, -25, False, 1
    headers = {'content-type': 'application/json'}
    json = str({'move': move, 'board': currentBoard['board']}).replace('\'', '\"')
    r = requests.post("http://127.0.0.1:8000/update_board", json=json, headers=headers)
    response = r.json()
    currentBoard = response
    state = int(hashlib.sha256(str(response['board']).encode('utf-8')).hexdigest(), 16) % 10 ** 8
    if response['go_again']:
        return state, 0, False, 1
    elif response['winner'] == 'player':
        totalWins+=1
        return state, 1, True, 1
    elif response['winner'] == 'AI':
        totalLoses+=1
        return state, -1, True, 1
    elif response['winner'] == 'tie':
        totalTies+=1
        return state, 0.75, True, 1
    else:
        return aiGo()


for episode in range(1, 5000):
    done = False
    G, reward = 0, 0
    state = reset()
    sameStateCnt = 0
    while not done:
        try:
            action = np.argmax(Q[state])  # 1
            state2, reward, done, info = updateBoard(action)  # 2
            Q[state, action] += alpha * (reward + np.max(Q[state2]) - Q[state, action])  # 3
            G += reward
            if (state == state2):
                sameStateCnt += 1
            else:
                sameStateCnt = 0
            state = state2
            if(sameStateCnt > 30):
                done = True
                print('Error same state loop. Restarting episode. ')
        except KeyError:
            done = True
            print('Random KeyError. Restarting episode. ')

    if episode % 10 == 0:
        print('Episode {} Total Reward: {} Total Wins: {} Total Loses: {} Total Ties: {}'.format(episode, G,totalWins,totalLoses,totalTies))
        #np.savetxt('test2.txt', Q)

def exit_handler():
    print ('My application is ending!')

