import os

import math
import numpy
import tensorflow

import board
import engine

NETWORK_LOCATION = os.path.join(os.path.dirname(__file__), "network.tflite")
interpreter = tensorflow.lite.Interpreter(model_path=NETWORK_LOCATION)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()


def preprocess_board_object(board_object):
    black_board = board.board_array(board_object.bitboard_black)
    white_board = board.board_array(board_object.bitboard_white)

    board_input = [[] for _ in range(board.BOARD_SIZE)]
    for index, black in enumerate(black_board):
        board_input[index // 8].append((black, white_board[index]))

    if board_object.side == board.BLACK:
        extra_input = (1, 0)
    else:
        extra_input = (0, 1)

    return board_input, extra_input


TANH_LIMIT = 1 - 10 ** (-16)


def inverse_tanh(x):
    x = max(-TANH_LIMIT, min(TANH_LIMIT, x))
    return (1 / 2) * math.log((x + 1) / (1 - x))


SQUARED_FACTOR = math.log(64) / math.log(inverse_tanh(TANH_LIMIT)) + 10 ** (-12)


def inverse_tanh_squared(x):
    x = max(-TANH_LIMIT, min(TANH_LIMIT, x))
    return (x / abs(x)) * inverse_tanh(abs(x)) ** SQUARED_FACTOR


def evaluate(board_object):
    black_score, white_score = board_object.score()

    # if the game is over
    if board_object.is_game_over():
        if black_score > white_score:
            return engine.INFINITY - white_score - 1
        elif black_score < white_score:
            return -engine.INFINITY + black_score + 1
        else:
            return 0

    inputs = preprocess_board_object(board_object)
    interpreter.set_tensor(input_details[0]["index"], numpy.array([inputs[0]]).astype(numpy.float32))
    interpreter.set_tensor(input_details[1]["index"], numpy.array([inputs[1]]).astype(numpy.float32))
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]["index"])

    return int(100 * inverse_tanh_squared(output))
