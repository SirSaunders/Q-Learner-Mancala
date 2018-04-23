############################
# @Authors: Johnathan Saunders && Jatin Bhakta
# @Date: 4/18/18
# @Class: Graduate AI Class
###########################



from chalice import Chalice
import copy
import json as Json

cors_config = True
app = Chalice(app_name='game-server')
# AI player's ID
com_player = 0

boardLength = 14
# AI and Human's mancala positions
mancalaAI = 0
mancalaHuman = 7



# Checks if the move would allow the player to go again
# if it would allow a player to go again return points > 0
# #else 0 if they would not go again
def go_again_points(move, board):
    landedSpace = board[move[0]]
    if landedSpace['type'] == 'mancala':
        return 20
    return 0


# checks if the player has landed in an empty space
# and if they would be able to steal marbles from the opponent
# if they can not do both return zero
# if they can return score > 0
def empty_space_points(move, board):
    landedSpace = board[move[0]]
    player = board[move[0]]['player']
    score = 0
    if landedSpace['type'] != 'mancala' and landedSpace['marbles'] == 0 and landedSpace['player'] == player:
        accrossSpace = board[int((move[0] + (boardLength / 2)) % boardLength)]
        if (player == com_player):
            score = accrossSpace['marbles'] * 10

    return score


## returns points > 0 if mancala was points have increased
def increment_mancala_points(move):
    return 10 * move[1]


# added as a shorter way to use GetMove
# #this was done because pythong does not do overloading
# #and adding logic for default values would have been messy
def getMoveQuick(pos, board):
    space = board[pos]
    return getMove(pos, space['marbles'], board)


# updates the game board given the current bard and a move
# @return currentPos will return current postion after board update
# @return incrementedMancala will return how many times the player that moved manacala was incremented
# @return yourSideScore will return the number of marbles you placed on your side - marbles placed on opponent's side
# @return updatedBoard will return updated board after move
# @ return winnerDetails will return whether anyone has one and if so who won or tie
def getMove(pos, marbles, board):
    updatedBoard = copy.deepcopy(board)
    incrementedMancala = 0
    currentPos = pos
    yourSideScore = 0
    player = board[pos]['player']
    updatedBoard[currentPos]['marbles'] = 0
    winnerDetails = None

    if marbles == 0:
        return pos, 0, 0, board
    for i in range(marbles):
        currentPos = (currentPos + 1) % boardLength
        space = board[currentPos]
        if space['player'] == player:
            yourSideScore += 1
        else:
            yourSideScore -= 1
        if space['type'] == 'mancala':
            if space['player'] == player:
                incrementedMancala += 1
                updatedBoard[currentPos]['marbles'] += 1
            else:
                currentPos = (currentPos + 1) % boardLength
                updatedBoard[currentPos]['marbles'] += 1
        else:
            updatedBoard[currentPos]['marbles'] += 1
    landedSpace = updatedBoard[currentPos]
    if landedSpace['type'] != 'mancala' and landedSpace['marbles'] == 1 and landedSpace['player'] == player:
        accrossSpace = updatedBoard[int((boardLength - currentPos) % boardLength)]
        if (accrossSpace['marbles'] > 0):
            if (player == 0):
                updatedBoard[7]['marbles'] += accrossSpace['marbles'] + 1
            else:
                updatedBoard[0]['marbles'] += accrossSpace['marbles'] + 1
            updatedBoard[accrossSpace['space_id']]['marbles'] = 0
            updatedBoard[currentPos]['marbles'] = 0
    boardScore = getBoardScore(updatedBoard)
    if boardScore[0] == 9999999 or boardScore[1] == 9999999:
        if boardScore[0] == 9999999 and boardScore[1] == 9999999:
            winnerDetails = 'tie'
        elif boardScore[0] == 9999999:
            winnerDetails = 'AI'
        elif boardScore[1] == 9999999:
            winnerDetails = 'player'
        print(boardScore)
        print(winnerDetails)

    return currentPos, incrementedMancala, yourSideScore, updatedBoard, winnerDetails


# get a more accurate score of which player is in a better position to win
# returns board state scores for each player
# include method to get a better "score" of game: 1.5 * (marbles in mancala) + sum of marbles on your side
def getBoardScore(board):
    # initialized to current mancala marbles count
    # player1Score = board['space'][mancalaHuman]['marbles']
    # player2Score = board['space'][mancalaAI]['marbles']
    mancala1 = 0.5 * board[mancalaAI]['marbles']
    mancala2 = 0.5 * board[mancalaHuman]['marbles']
    player1Score = mancala1
    player2Score = mancala2
    nonMancalPointsPlayer1 = 0  # AI
    nonMancalPointsPlayer2 = 0

    for space in board:
        if space['player'] == 0:
            player1Score += space['marbles']
            if space['type'] == 'normal':
                nonMancalPointsPlayer1 += space['marbles']
        if space['player'] == 1:
            player2Score += space['marbles']
            if space['type'] == 'normal':
                nonMancalPointsPlayer2 += space['marbles']
    if nonMancalPointsPlayer1 == 0 or nonMancalPointsPlayer2 == 0:
        if player1Score - mancala1 < 24:
            player1Score = -99999999
        else:
            player1Score = 9999999
        if player2Score - mancala2 < 24:
            player2Score = -99999999
        else:
            player2Score = 9999999
    return player1Score, player2Score


# @return  the points for a given move for local search
def findPoints(moveFromPos, board):
    moveSpace = board[moveFromPos]
    marbles = moveSpace['marbles']
    move = getMove(moveSpace['space_id'], marbles, board)
    incrementMancalaPoints = increment_mancala_points(move)
    goAgainPoints = go_again_points(move, board)
    emptySpacePoints = empty_space_points(move, board)
    yourSideScore = move[2]
    return (incrementMancalaPoints + goAgainPoints + yourSideScore + emptySpacePoints), move[3]


# Traverses tree for local search, returns best points found
def searchMovePoints(board, cnt, pos, score, maxDepth):
    (points, updatedboard) = findPoints(pos, board)
    worstPoints = 999999
    bestPoints = 0
    if (go_again_points([pos], updatedboard) > 0):
        cnt -= 1  # increment back 1 so when it is incremented up no changes occurs
    if cnt >= maxDepth:
        return points
    else:
        if ((cnt + 1) % 2) == 1:  # max
            for i in range(1, 7):
                points = searchMovePoints(updatedboard, cnt + 1, i, points, maxDepth)
                if points > bestPoints:
                    bestPoints = points * (maxDepth - cnt + 1)
            return bestPoints + score
        else:
            for i in range(8, 13):  # min
                points = searchMovePoints(updatedboard, cnt + 1, i, points, maxDepth)
                if points < bestPoints:
                    bestPoints = points
            return bestPoints + score


# Traverses tree for min-max, returns best points for an end state found
def minMaxMove(board, cnt, pos, maxDepth):
    updatedboard = getMoveQuick(pos, board)[3]
    bestPoints = 0
    worstPoints = 999999
    if (go_again_points([pos], updatedboard) > 0):
        cnt -= 1  # increment back 1 so when it is incremented up no changes occurs
    if cnt >= maxDepth:
        points = getBoardScore(updatedboard)[0]
        return points
    else:
        if ((cnt + 1) % 2) == 1:  # max
            for i in range(1, 7):

                points = minMaxMove(updatedboard, cnt + 1, i, maxDepth)
                if points > bestPoints:
                    bestPoints = points
            return bestPoints
        else:
            for i in range(8, 13):  # min
                points = minMaxMove(updatedboard, cnt + 1, i, maxDepth)
                if worstPoints > points:
                    worstPoints = points
            return worstPoints


# finds best move AI can make
# @return bestMove returns move chosen as best move
# @return bestPoints returns points that bestMove had
def findMove(board):
    bestPoints = -99999999
    bestMove = 1
    for i in range(1, 7):
        if not (board['board']['space'][i]['marbles'] > 0):
            points = -1
        else:
            depthSearch = 0
            depthMinMax = 0
            points = searchMovePoints(board['board']['space'], 0, i, 0, depthSearch)
            points += minMaxMove(board['board']['space'], 0, i, depthMinMax) * depthSearch
            print(points)
        if points > bestPoints:
            bestPoints = points
            bestMove = i
    return bestMove, bestPoints


# endpoint for updating the board
# takes a board and move as an input
# returns updated board, who won id anyone, and whether the player can go again
@app.route('/update_board', methods=['POST'], cors=cors_config)
def updateBoard():
    app.log.debug('json')

    json = Json.loads( app.current_request.json_body)
    app.log.debug(json)
    move = json['move']
    board = json['board']['space']

    landed = getMove(move, board[move]['marbles'], board)
    json = {"board": {
        "space": landed[3]}}
    go_again = False
    json['winner'] = landed[4]
    if go_again_points(landed, board) > 0:
        go_again = True
    json['go_again'] = go_again
    return json


# endpoint for getting the AI's move
# takes a board as an input
# returns updated board, who won id anyone, and whether the AI should go again
@app.route('/get_move', methods=['POST'], cors=cors_config)
def updateBoard():
    print(app.current_request)

    json = Json.loads(app.current_request.json_body)
    print(json)
    board = json['board']['space']
    move = findMove(json)
    movePos = move[0]
    landed = getMove(movePos, board[movePos]['marbles'], board)
    json = {"board": {"space": landed[3]}}
    go_again = False
    json['winner'] = landed[4]
    if go_again_points(landed, board) > 0:
        go_again = True
    json['go_again'] = go_again
    return json
