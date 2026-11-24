
"""
Course: CSE 351 
Assignment: 08 Prove Part 2
File:   prove_part_2.py
Author: Makay Crandall

Purpose: Part 2 of assignment 8, finding the path to the end of a maze using recursion.

Instructions:
- Do not create classes for this assignment, just functions.
- Do not use any other Python modules other than the ones included.
- You MUST use recursive threading to find the end of the maze.
- Each thread MUST have a different color than the previous thread:
    - Use get_color() to get the color for each thread; you will eventually have duplicated colors.
    - Keep using the same color for each branch that a thread is exploring.
    - When you hit an intersection spin off new threads for each option and give them their own colors.

This code is not interested in tracking the path to the end position. Once you have completed this
program however, describe how you could alter the program to display the found path to the exit
position:

What would be your strategy?

My strategy would be to keep track of the positions visited by each thread
using a list. When a thread reaches an intersection, I would create new
threads and give each one a copy of the current path. Each thread would
continue adding positions to its path as it explores. When a thread finds
the exit, it would have the complete path to display.

Why would it work?

It would work because each thread would maintain its own path without
interfering with the paths of other threads. The thread that finds the exit
would have a record of every position it visited from the starting point
to the ending position. This path could then be used to display the
successful route through the maze.

"""

import math
import threading 
from screen import Screen
from maze import Maze
import sys
import cv2

# Include cse 351 files
from cse351 import *

SCREEN_SIZE = 700
COLOR = (0, 0, 255)
COLORS = (
    (0,0,255),
    (0,255,0),
    (255,0,0),
    (255,255,0),
    (0,255,255),
    (255,0,255),
    (128,0,0),
    (128,128,0),
    (0,128,0),
    (128,0,128),
    (0,128,128),
    (0,0,128),
    (72,61,139),
    (143,143,188),
    (226,138,43),
    (128,114,250)
)
SLOW_SPEED = 100
FAST_SPEED = 0

# Globals
current_color_index = 0
thread_count = 0
stop = False
speed = SLOW_SPEED

# ADDED: Lock and list to manage threads safely
state_lock = threading.Lock()
threads = []


def get_color():
    """ Returns a different color when called """
    global current_color_index
    if current_color_index >= len(COLORS):
        current_color_index = 0
    color = COLORS[current_color_index]
    current_color_index += 1
    return color


# ADDED: Recursive function to search the maze
def search_maze(maze, row, col, color):
    """ Recursively searches the maze using threads. """

    global stop
    global thread_count
    global threads

    # Check and mark the position safely
    with state_lock:

        if stop:
            return

        # Check if the exit has been found
        if maze.at_end(row, col):
            stop = True
            return

        # Check if this position is available
        if not maze.can_move_here(row, col):
            return

        # Move to this position
        maze.move(row, col, color)

        # Find available neighboring positions
        moves = maze.get_possible_moves(row, col)

    # Stop if there are no available moves
    if len(moves) == 0:
        return

    # Create a new thread for each additional path
    for next_row, next_col in moves[:-1]:

        with state_lock:

            if stop:
                return

            # Give the new thread its own color
            new_color = get_color()

            # Count the new thread
            thread_count += 1

            # Create the new thread
            new_thread = threading.Thread(
                target=search_maze,
                args=(maze, next_row, next_col, new_color)
            )

            # Save the thread
            threads.append(new_thread)

        # Start the new thread
        new_thread.start()

    # Continue searching the final path using the current thread
    next_row, next_col = moves[-1]

    search_maze(maze, next_row, next_col, color)


# ADDED: Start the recursive threaded search
def solve_find_end(maze):
    """ Finds the end position using threads. Nothing is returned. """

    global stop
    global thread_count
    global current_color_index
    global threads

    # Reset global variables
    with state_lock:
        stop = False
        thread_count = 0
        current_color_index = 0
        threads = []

    # Get the starting position
    start_row, start_col = maze.get_start_pos()

    # Get the starting color
    start_color = get_color()

    # Start searching recursively
    search_maze(maze, start_row, start_col, start_color)

    # Wait for every created thread to finish
    index = 0

    while True:

        with state_lock:
            if index >= len(threads):
                break

            current_thread = threads[index]

        current_thread.join()
        index += 1


def find_end(log, filename, delay):
    """ Do not change this function """

    global thread_count
    global speed

    # create a Screen Object that will contain all of the drawing commands
    screen = Screen(SCREEN_SIZE, SCREEN_SIZE)
    screen.background((255, 255, 0))

    maze = Maze(screen, SCREEN_SIZE, SCREEN_SIZE, filename, delay=delay)

    solve_find_end(maze)

    log.write(f'Number of drawing commands = {screen.get_command_count()}')
    log.write(f'Number of threads created  = {thread_count}')

    done = False
    while not done:
        if screen.play_commands(speed): 
            key = cv2.waitKey(0)
            if key == ord('1'):
                speed = SLOW_SPEED
            elif key == ord('2'):
                speed = FAST_SPEED
            elif key == ord('q'):
                exit()
            elif key != ord('p'):
                done = True
        else:
            done = True


def find_ends(log):
    """ Do not change this function """

    files = (
        ('very-small.bmp', True),
        ('very-small-loops.bmp', True),
        ('small.bmp', True),
        ('small-loops.bmp', True),
        ('small-odd.bmp', True),
        ('small-open.bmp', False),
        ('large.bmp', False),
        ('large-loops.bmp', False),
        ('large-squares.bmp', False),
        ('large-open.bmp', False)
    )

    log.write('*' * 40)
    log.write('Part 2')
    for filename, delay in files:
        filename = f'./mazes/{filename}'
        log.write()
        log.write(f'File: {filename}')
        find_end(log, filename, delay)
    log.write('*' * 40)


def main():
    """ Do not change this function """
    sys.setrecursionlimit(5000)
    log = Log(show_terminal=True)
    find_ends(log)


if __name__ == "__main__":
    main()
