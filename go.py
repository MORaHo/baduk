from variables import SIZE, run, height, width, beige, LINE_COLOUR, space, COLOUR_ARRAY, PLAYER_ARRAY, current_player, block, liberties, opposing_player, seki_counter, moves

import os
import sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'

import pygame as pg
import numpy

copy = numpy.copy

### LOCATION PATH

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

### PIECE CONSTANTS

EMPTY    =  0
BLACK    =  1
WHITE    =  2
RESTORE  =  3
MARKER   =  4
OFFBOARD =  7
LIBERTY  =  8


### GENERATE AND POPULATE BOARD
prefill_board = [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


## ADD OFFBOARD IN CELLS

for i in range(SIZE):
    for j in range(SIZE):
        if i == 0 or j == 0 or i == SIZE-1 or j == SIZE-1: prefill_board[i][j] = OFFBOARD


## MAKE INTO MATRIX
board = numpy.array(prefill_board,dtype=object).reshape(SIZE,SIZE)

### GAME & BOARD LOGIC FUNCTIONS

def get_mouse_position():

    position = pg.mouse.get_pos()
    x_position = position[0] # x component of mouse position
    y_position = position[1] # y component of mouse position

    return y_position, x_position # I'm doing this since when finding a cell we need find the array at the correct y and then find the cell at x


# find position in matrix
def ui_position_board_cell(position):
    return int((position - space/2) // space) + 1  # return position in board matrix, integer since float not usable, +1 for offset


# clear block of captured stones
def remove_stones():

    for stone in block: #we clear all stones in the captured block

        stone_row = stone[0]
        stone_column = stone[1]
        board[stone_row][stone_column] = EMPTY #we don't need to remove liberties since there are none


def clear_block_and_liberties():
    
    global block, liberties
    block = []
    liberties = []

def remove_markings_and_liberties():

    clear_block_and_liberties()

    for y in range(SIZE):
        for x in range(SIZE):

            if board[y][x] != OFFBOARD: #bitwise and will break if we do it with OFFBOARD so we have to skip it
                val = board[y][x]
                new_val = val & 3
                board[y][x] = new_val #restores cell to original value since markings and liberties are cleared with bitwise sommation


def flood(x,y,colour): #function to find components of a group, used to determine if the given group has liberties
    
    stone = board[y][x]
    if stone == OFFBOARD: return

    if stone and stone & colour and (stone & MARKER) == 0: #If there piece is a stone of the colour (do bit math for explaination)

        #add to known block of stones of the same colour that are connected
        block.append((y,x))
        
        #Marking the stone so we don't infinitely check stones, this is why we do that bit math is the condition
        board[y][x] |= MARKER #bitwise OR, meaning all bits that are active in either element will also be in the new value

        #Floodfill, recursively flood adjacent cells
        flood(x,y-1,colour) #flood north
        flood(x,y+1,colour) #flood south
        flood(x-1,y,colour) #flood west
        flood(x+1,y,colour) #flood east

    elif stone == EMPTY: #If a stone adjacent to the block is empty that is a liberty that can still be exploited

        # We mark the liberty and save it
        board[y][x] == LIBERTY #not used but is useful
        liberties.append((y,x))

    return liberties #we return the liberties which pertain to the block which the piece we are looking at pertains to


# function to check if there the given colour is capturing
def captures(given_colour):

    check = False
    colour = PLAYER_ARRAY[3-given_colour] #we swap since this function checks if block of stones is captured, ergo if the colour captures

    for y in range(SIZE):
        for x in range(SIZE):

            stone = board[y][x]

            if stone == OFFBOARD: continue

            if stone & colour: 

                flood(x,y,colour) # Floodfill to find if the block which the stone pertains to has any remaining liberties

                if len(liberties) == 0: # if there a 0 liberties, the block has been captured, it can be cleared

                    #if the move is 'ko' move but causes the capture of stone, then it is not allowed, unless it's the second move, in which it is dealt afterwards

                    check = True #confirms that there has been a capture
                    remove_stones() #remove the stones 

                #we can remove all markers and liberties, allowing for the next iteration
                remove_markings_and_liberties()   
             
    return check


def place_stone(y,x):
    board[y][x] = current_player


def remove_stone(y,x):
    board[y][x] = EMPTY


def determine_if_neighbour(cell_row,cell_column):
    
    if_neighbour = False
    last_move_row = moves[opposing_player][-1][0]
    last_move_column = moves[opposing_player][-1][1]

    if last_move_row == cell_row and last_move_column == cell_column -1: if_neighbour = True
    if last_move_row == cell_row and last_move_column == cell_column +1: if_neighbour = True
    if last_move_row == cell_row-1 and last_move_column == cell_column: if_neighbour = True
    if last_move_row == cell_row+1 and last_move_column == cell_column: if_neighbour = True
        
    return if_neighbour


### PYGAME INITIATION

## This is pretty straight forward
pg.init()
CLOCK = pg.time.Clock()
screen = pg.display.set_mode((width,height+80),0,32)
pg.display.set_caption("Baduk")
pygame_icon = pg.image.load(os.path.join(__location__,'app_icon.png'))
pg.display.set_icon(pygame_icon)


### DRAWING

def draw_board():
    screen.fill(beige) # Wood coloured background

    #draw the lines, we use -2 to compensate for the size value considering the offboard on all sides.
    for i in range(1,SIZE-1): # starting at 1 and ending 1 before since the size is taking the addition offset space
        pg.draw.line(screen, LINE_COLOUR, ( space * i , space ), ( space * i, (SIZE-2) * space ), 1) # Vertical lines
        pg.draw.line(screen, LINE_COLOUR, ( space , space * i ), ( (SIZE-2) * space , space * i), 1) # Horizontal lines
    
    #draw the pieces on the board
    for i in range(SIZE):
        for j in range(SIZE):
            if board[j][i] == OFFBOARD: continue # Skip if not part of the board
            
            elif board[j][i] != EMPTY: # If there is a piece
                try:
                    stone_colour = COLOUR_ARRAY[board[j][i]] # the array maps the piece in the position to the colour that needs to be shown
                    position_array = (i * space , j * space) # since pygame uses (x,y) we don't put y first like on board
                    pg.draw.circle(screen,stone_colour,position_array,20)
                except: pass

    pg.draw.rect(screen,COLOUR_ARRAY[current_player],(space,height,width-2*space,space)) #turn indicator

    pg.display.update()
draw_board() #I'm calling it so that it doesn't start on a black screen


### GAMELOOP

while run:

    for event in pg.event.get():

        if event.type == pg.QUIT: # When x pressed end game (superfluous comment and unneccessary on Hyprland)
            sys.exit()
            run = False

        if event.type == pg.MOUSEBUTTONDOWN: # If mouse is pressed
        
            ## Game Logic
            mouse_position = get_mouse_position() # get the mouse position in the pygame window

            
            #Determine matrix position values
            cell_row = ui_position_board_cell(mouse_position[0])
            cell_column = ui_position_board_cell(mouse_position[1])
            
            
            # Check if there is already a stone in the targetted cell 
            if board[cell_row][cell_column] != EMPTY or board[cell_row][cell_row] == OFFBOARD:
                continue # this solves issue of clicking on offset since that is occupied by offboard value in the board so it's fine0
            
            fallback_board = copy(board) #board that will be used as reference, copy only copies the values rather than the pointer, allowing for the comparison.
            place_stone(cell_row,cell_column)

            if seki_counter == 1:
                
                captures(opposing_player)
                posticipate_board = copy(board)
                    
                if ((fallback_board == posticipate_board).all()) == True and (determine_if_neighbour(cell_row,cell_column)) == True:
                    continue

                seki_counter = 0
                board = copy(fallback_board)
                place_stone(cell_row,cell_column)

                if captures(opposing_player) == True:

                    board = numpy.copy(fallback_board)
                    place_stone(cell_row, cell_column)

                    if captures(current_player) != True:

                        board = copy(fallback_board)
                        seki_counter = 1
                        continue
                        
                    moves[current_player].append((cell_row,cell_column))
                    opposing_player = PLAYER_ARRAY[current_player]
                    current_player  = PLAYER_ARRAY[3-current_player]
                    seki_counter = 1
                    draw_board()
                    continue
                
                elif captures(current_player) == True:
                    
                    moves[current_player].append((cell_row,cell_column))
                    opposing_player = PLAYER_ARRAY[current_player]
                    current_player  = PLAYER_ARRAY[3-current_player]
                    draw_board()
                    continue
                
                else:
                    moves[current_player].append((cell_row,cell_column))
                    opposing_player = PLAYER_ARRAY[current_player]
                    current_player  = PLAYER_ARRAY[3-current_player]
                    draw_board()
                    continue

            seki_counter = 0

            if captures(opposing_player) == True:

                board = copy(fallback_board)
                place_stone(cell_row,cell_column)

                if captures(current_player) != True:
                    board = numpy.copy(fallback_board)
                    continue

                moves[current_player].append((cell_row,cell_column))
                opposing_player = PLAYER_ARRAY[current_player]
                current_player  = PLAYER_ARRAY[3-current_player]
                seki_counter = 1
                draw_board()
                continue
            
            elif captures(current_player) == True:
                moves[current_player].append((cell_row,cell_column))
                opposing_player = PLAYER_ARRAY[current_player]
                current_player  = PLAYER_ARRAY[3-current_player]
                draw_board()
                continue

            else:
                moves[current_player].append((cell_row,cell_column))
                opposing_player = PLAYER_ARRAY[current_player]
                current_player  = PLAYER_ARRAY[3-current_player]
                draw_board()
                continue


    pg.display.update() #Update pygame at end of move
            

pg.quit()
final_board = copy(board)
ending = input()





