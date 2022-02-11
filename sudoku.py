import numpy as np
import pygame
import pygame_widgets
from pygame_widgets.button import Button
import random
from typing import Union


class SudokuCell:
    def __init__(self, screen, pos, side, grid_value, ij):
        self.screen = screen
        self.x, self.y = pos
        self.z = side
        self.i, self.j = ij
        self.val = grid_value
        self.writeable = not bool(grid_value)
        self.supVals = ''
        self.rect = pygame.Rect(self.x, self.y, self.z, self.z)

        self.wrong = False
        self.fontWrongColor = (250, 100, 100)

        self.borderColor = (175, 175, 175)
        self.fontSmallSize = self.z // 4
        self.fontSmallColor = (200, 200, 200)
        self.fontSmall = pygame.font.SysFont('Comic Sans MS', self.fontSmallSize)

        self.fontNormalSize = self.z // 2
        self.fontNormalColor = (200, 200, 200)
        self.fontLockedColor = (25, 25, 25)
        self.fontNormal = pygame.font.SysFont('Comic Sans MS', self.fontNormalSize)

    def string(self, val):
        return str(val) if val else ' '

    def draw_border(self, color=None, width=1):
        if color is None:
            color = self.borderColor
        pygame.draw.rect(self.screen, color, self.rect, width=width)

    def draw_val(self):
        color = self.fontWrongColor if self.wrong else self.fontNormalColor if self.writeable else self.fontLockedColor
        text = self.fontNormal.render(self.string(self.val), True, color)
        textRect = text.get_rect(center=self.rect.center)
        self.screen.blit(text, textRect)

    def change_val(self, val):
        self.val = val
        self.wrong = False

    def delete_val(self):
        self.val = 0
        self.wrong = False

    def draw_supVals(self):
        text = self.fontSmall.render(' ' + self.supVals, True, self.fontSmallColor)
        self.screen.blit(text, self.rect)

    def add_supVal(self, val):
        val = self.string(val)
        if val not in self.supVals:
            self.supVals += self.string(val)
            self.supVals = ''.join(sorted(self.supVals))

    def remove_supVal(self):
        self.supVals = self.supVals[:-1]

    def delete_supVals(self):
        self.supVals = ''

    def draw(self):
        self.draw_border()
        self.draw_val()
        self.draw_supVals()


class SudokuGame:
    def __init__(self, grid: Union[str, np.ndarray] = None):
        pygame.display.set_caption('Sudoku')

        self.running = True
        self.change_grid = False
        self.victory = False

        self.fullscreen = False

        self.FPS = 30

        self.n = 9
        self.sqrt = int(self.n**0.5)
        self.w = self.n + 8
        self.h = self.n + 2

        self.fpsClock = pygame.time.Clock()
        self.resList = [(1920, 1080), (1600, 900), (1280, 720), (640, 360), (320, 180)]
        self.screenSize = (1280, 720)
        self.width, self.height = self.screenSize
        width_unit = self.width // self.w
        height_unit = self.height // self.h
        self.unit = min(width_unit, height_unit)
        self.gridX = (self.width - self.n*self.unit) // 2
        self.gridY = (self.height - self.n*self.unit) // 2

        self.buttonWidth = 2*self.unit
        self.buttonHeight = 1*self.unit

        self.screen = pygame.display.set_mode(self.screenSize)
        self.screenBox = self.screen.get_rect()

        self.fontSmall = self.unit // 4
        self.fontNormal = self.unit // 2

        self.backgroundColor = (50, 50, 50)
        self.boxBorderColor = (200, 200, 200)
        self.boxBackgroundColor1 = (125, 125, 125)
        self.boxBackgroundColor2 = (100, 100, 100)

        self.keys = {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
                     'sup_hold': pygame.K_LCTRL, 'sup_toggle': pygame.K_F1,
                     'adjust_hold': pygame.K_RCTRL, 'adjust_toggle': pygame.K_F2,
                     'check': pygame.K_F3, 'solve': pygame.K_F4,
                     'remove': pygame.K_BACKSPACE, 'delete': pygame.K_DELETE,
                     'val1': (pygame.K_1, pygame.K_KP_1), 'val2': (pygame.K_2, pygame.K_KP_2),
                     'val3': (pygame.K_3, pygame.K_KP_3), 'val4': (pygame.K_4, pygame.K_KP_4),
                     'val5': (pygame.K_5, pygame.K_KP_5), 'val6': (pygame.K_6, pygame.K_KP_6),
                     'val7': (pygame.K_7, pygame.K_KP_7), 'val8': (pygame.K_8, pygame.K_KP_8),
                     'val9': (pygame.K_9, pygame.K_KP_9),
                     'save_grid': pygame.K_s, 'get_grid': pygame.K_g
                     }

        self.selectedCell_i = 0
        self.selectedCell_j = 0

        self.moveKeys = {self.keys[direction]: direction for direction in ['up', 'down', 'left', 'right']}
        self.supHoldKey = self.keys['sup_hold']
        self.supToggleKey = self.keys['sup_toggle']
        self.adjustHoldKey = self.keys['adjust_hold']
        self.adjustToggleKey = self.keys['adjust_toggle']
        self.checkKey = self.keys['check']
        self.solveKey = self.keys['solve']
        self.removeKey = self.keys['remove']
        self.deleteKey = self.keys['delete']
        self.writeKeys = {key: i for i in range(1, 10) for key in self.keys[f'val{i}']}
        self.saveGridKey = self.keys['save_grid']
        self.getGridKey = self.keys['get_grid']

        self.writeSup = False
        self.writeAdjust = False

        self.gridRect = pygame.Rect(self.gridX, self.gridY, self.n*self.unit, self.n*self.unit)

        self.sudoku = Sudoku(grid)
        self.solution = Sudoku(grid)
        self.solution.solve()

        self.grid = np.empty((self.n, self.n), dtype=SudokuCell)
        self.boxes = np.empty((self.sqrt, self.sqrt), dtype=pygame.Rect)
        for j in range(self.n):
            y = self.gridY + j*self.unit
            for i in range(self.n):
                x = self.gridX + i*self.unit
                self.grid[j][i] = SudokuCell(self.screen, (x, y), self.unit, self.sudoku.grid[j][i], (i, j))
                if not i % self.sqrt and not j % self.sqrt:
                    self.boxes[j//self.sqrt][i//self.sqrt] = pygame.Rect(x, y, self.sqrt*self.unit, self.sqrt*self.unit)

        self.buttonAutosolveColor = (150, 100, 100)
        self.autosolve = True
        self.buttonAutosolve = Button(
            self.screen,  # Surface to place button on
            self.gridRect.right + 1*self.unit,  # X-coordinate of top left corner
            self.gridY + 2*self.unit,  # Y-coordinate of top left corner
            self.buttonWidth,  # Width
            self.buttonHeight,  # Height
            text='Solve',  # Text to display
            fontSize=self.fontNormal,  # Size of font
            onClick=self.buttonAutosolveClick  # Function to call when clicked on
        )
        self.update_buttonColor(self.buttonAutosolve, self.buttonAutosolveColor)

        self.buttonCheckColor = (100, 150, 100)
        self.buttonCheck = Button(
            self.screen,  # Surface to place button on
            self.gridRect.right + 1 * self.unit,  # X-coordinate of top left corner
            self.gridY,  # Y-coordinate of top left corner
            self.buttonWidth,  # Width
            self.buttonHeight,  # Height
            text='Check',  # Text to display
            fontSize=self.fontNormal,  # Size of font
            onClick=self.buttonCheckClick  # Function to call when clicked on
        )
        self.update_buttonColor(self.buttonCheck, self.buttonCheckColor)

        self.buttonStateColorInactive = (100, 100, 150)
        self.buttonStateColorActive = (150, 150, 250)

        self.buttonSup = Button(
            self.screen,  # Surface to place button on
            self.gridX - 3 * self.unit,  # X-coordinate of top left corner
            self.gridY + 0*self.unit,  # Y-coordinate of top left corner
            self.buttonWidth,  # Width
            self.buttonHeight,  # Height
            text='Super',  # Text to display
            fontSize=self.fontNormal,  # Size of font
            onClick=self.buttonSupClick  # Function to call when clicked on
        )
        self.update_buttonColor(self.buttonSup, self.buttonStateColorInactive)

        self.buttonAdjust = Button(
            self.screen,  # Surface to place button on
            self.gridX - 3*self.unit,  # X-coordinate of top left corner
            self.gridY + 2*self.unit,  # Y-coordinate of top left corner
            self.buttonWidth,  # Width
            self.buttonHeight,  # Height
            text='Adjust',  # Text to display
            fontSize=self.fontNormal,  # Size of font
            onClick=self.buttonAdjustClick  # Function to call when clicked on
        )
        self.update_buttonColor(self.buttonAdjust, self.buttonStateColorInactive)

        self.buttonSaveColor = (150, 150, 150)
        self.buttonSave = Button(
            self.screen,  # Surface to place button on
            self.gridX - 3*self.unit,  # X-coordinate of top left corner
            self.gridRect.bottom - 1*self.unit,  # Y-coordinate of top left corner
            self.buttonWidth,  # Width
            self.buttonHeight,  # Height
            text='Save',  # Text to display
            fontSize=self.fontNormal,  # Size of font
            onClick=self.buttonSaveClick  # Function to call when clicked on
        )
        self.update_buttonColor(self.buttonSave, self.buttonSaveColor)

        self.buttonGetColor = (150, 150, 150)
        self.buttonGet = Button(
            self.screen,  # Surface to place button on
            self.gridX - 3*self.unit,  # X-coordinate of top left corner
            self.gridRect.bottom - 3*self.unit,  # Y-coordinate of top left corner
            self.buttonWidth,  # Width
            self.buttonHeight,  # Height
            text='Get',  # Text to display
            fontSize=self.fontNormal,  # Size of font
            onClick=self.buttonGetClick  # Function to call when clicked on
        )
        self.update_buttonColor(self.buttonGet, self.buttonGetColor)

    def buttonColorHover(self, buttonColor):
        color = []
        for rgb in buttonColor:
            rgb += 5
            if rgb > 255:
                rgb = 255
            color.append(rgb)
        return tuple(color)

    def buttonColorPressed(self, buttonColor):
        color = []
        for rgb in buttonColor:
            rgb += 10
            if rgb > 255:
                rgb = 255
            color.append(rgb)
        return tuple(color)

    def update_buttonColor(self, button, buttonColor):
        button.inactiveColour = buttonColor
        button.hoverColour = self.buttonColorHover(buttonColor)
        button.pressedColour = self.buttonColorPressed(buttonColor)
        print()
        print(button.inactiveColour)
        print(button.hoverColour)
        print(button.pressedColour)
        print()

    def on_click_cell(self):
        return

    def fullscreen_toggle(self):
        screen_backup = self.screen.copy()
        self.screen = pygame.display.set_mode(self.screenSize, pygame.FULLSCREEN) if not self.fullscreen else pygame.display.set_mode(self.screenSize)
        self.screen.blit(screen_backup, (0, 0))

        pygame.display.flip()
        self.fullscreen = not self.fullscreen

    def set_loops(self, running_=None, victory_=None):
        if running_ is not None:
            self.running = running_
        if victory_ is not None:
            self.victory = victory_

    def reset_loops(self, running_=False, victory_=False):
        self.set_loops(running_=running_, victory_=victory_)

    def general_event_checks(self, event):
        # only do something if the event is of type QUIT
        if event.type == pygame.QUIT:
            # change the value to False, to exit the main loop
            self.reset_loops()

        # toggle fullscreen if F11 button is pressed
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.fullscreen_toggle()

    def move_selected_cell(self, key):
        direction = self.moveKeys[key]
        if direction == 'up':
            if self.selectedCell_j > 0:
                self.selectedCell_j -= 1
        if direction == 'down':
            if self.selectedCell_j < self.n-1:
                self.selectedCell_j += 1
        if direction == 'left':
            if self.selectedCell_i > 0:
                self.selectedCell_i -= 1
        if direction == 'right':
            if self.selectedCell_i < self.n-1:
                self.selectedCell_i += 1

    def mouse_on_cell(self, pos):
        if not self.gridRect.collidepoint(pos):
            return None
        for row in self.grid:
            for cell in row:
                if cell.rect.collidepoint(pos):
                    return cell
        return None

    def draw_boxes_border(self):
        for row in self.boxes:
            for box in row:
                pygame.draw.rect(self.screen, self.boxBorderColor, box, width=2)

    def draw_boxes_background(self):
        background1 = True
        for row in self.boxes:
            for box in row:
                color = self.boxBackgroundColor1 if background1 else self.boxBackgroundColor2
                pygame.draw.rect(self.screen, color, box, width=0)
                background1 = not background1

    def draw_cells(self):
        for row in self.grid:
            for cell in row:
                cell.draw()

    def update_solution(self):
        self.solution = Sudoku(self.sudoku.grid)
        self.solution.solve()

    def update_grid(self, grid):
        self.sudoku = Sudoku(grid)
        self.solution = Sudoku(grid)
        self.solution.solve()

        self.grid = np.empty((self.n, self.n), dtype=SudokuCell)
        self.boxes = np.empty((self.sqrt, self.sqrt), dtype=pygame.Rect)
        for j in range(self.n):
            y = self.gridY + j * self.unit
            for i in range(self.n):
                x = self.gridX + i * self.unit
                self.grid[j][i] = SudokuCell(self.screen, (x, y), self.unit, self.sudoku.grid[j][i], (i, j))
                if not i % self.sqrt and not j % self.sqrt:
                    self.boxes[j // self.sqrt][i // self.sqrt] = pygame.Rect(x, y, self.sqrt * self.unit, self.sqrt * self.unit)

    def change_adjust(self):
        self.writeAdjust = not self.writeAdjust
        buttonColor = self.buttonStateColorActive if self.writeAdjust else self.buttonStateColorInactive
        self.update_buttonColor(self.buttonAdjust, buttonColor)

        if not self.writeAdjust:
            self.update_solution()

    def change_sup(self):
        self.writeSup = not self.writeSup
        buttonColor = self.buttonStateColorActive if self.writeSup else self.buttonStateColorInactive
        self.update_buttonColor(self.buttonSup, buttonColor)

    def buttonAutosolveClick(self):
        grid = self.solution if self.autosolve else self.sudoku

        for j, row in enumerate(grid.rows):
            for i, val in enumerate(row):
                cell = self.grid[j][i]
                if cell.writeable:
                    cell.change_val(val)

        self.buttonCheckClick()
        self.autosolve = not self.autosolve
        text = 'Solve' if self.autosolve else 'Unsolve'
        font = pygame.font.SysFont('Calibri bold', self.fontNormal)
        self.buttonAutosolve.text = font.render(text, True, (0, 0, 0))

    def buttonCheckClick(self):
        for j, row in enumerate(self.solution.rows):
            for i, val in enumerate(row):
                cell = self.grid[j][i]
                if cell.writeable:
                    if cell.val != val:
                        cell.wrong = True

    def buttonSupClick(self):
        self.change_sup()

    def buttonAdjustClick(self):
        self.change_adjust()

    def buttonSaveClick(self):
        self.save_grid()

    def buttonGetClick(self):
        grid = self.get_grid()
        self.update_grid(grid)

    def save_grid(self):
        with open('sudoku.txt', 'a') as file:
            grid_str = ''
            for row in self.grid:
                for cell in row:
                    grid_str += cell.string(cell.val)
            file.write(repr(grid_str) + '\n')
            print(f'Saved grid in sudoku.txt:\n\t{repr(grid_str)}')

    def get_grid(self):
        with open('sudoku.txt', 'r') as file:
            # [1:-2] -> Geen ' ' en geen \n
            grids = [grid_str[1:-2] for grid_str in file.readlines()]
            print(grids)
            grid_str = random.choice(grids)
            return grid_str

    def game_main(self):
        # main loop
        self.screen = pygame.display.set_mode(self.screenSize)

        # define a variable to control the main loop
        self.running = True

        # main loop
        while self.running:
            frame = 0

            self.screen.fill(self.backgroundColor)

            self.draw_boxes_background()
            self.draw_cells()
            self.draw_boxes_border()

            # stores the (x,y) coordinates into
            # the variable as a tuple
            mouse = pygame.mouse.get_pos()
            mouse_cell = self.mouse_on_cell(mouse)
            cell = self.grid[self.selectedCell_j][self.selectedCell_i]

            cell.draw_border(color='red', width=2)

            # event handling, gets all event from the event queue
            events = pygame.event.get()
            for event in events:
                self.general_event_checks(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if mouse_cell:
                        self.selectedCell_i = mouse_cell.i
                        self.selectedCell_j = mouse_cell.j

                # check for key presses
                if event.type == pygame.KEYDOWN:
                    if event.key in self.moveKeys:
                        self.move_selected_cell(event.key)

                    if event.key in self.writeKeys:
                        val = self.writeKeys[event.key]
                        if self.writeAdjust:
                            cell.change_val(val)
                            cell.writeable = False
                            self.sudoku.set_grid_cell((self.selectedCell_i, self.selectedCell_j), val)
                        elif self.writeSup:
                            if cell.writeable:
                                cell.add_supVal(val)
                        else:
                            if cell.writeable:
                                cell.change_val(val)
                                self.sudoku.set_cell((self.selectedCell_i, self.selectedCell_j), val)

                    if event.key in (self.removeKey, self.deleteKey):
                        if self.writeAdjust:
                            cell.delete_val()
                            cell.writeable = True
                            self.sudoku.set_grid_cell((self.selectedCell_i, self.selectedCell_j), 0)
                        elif self.writeSup:
                            if cell.writeable:
                                if event.key == self.removeKey:
                                    cell.remove_supVal()
                                if event.key == self.deleteKey:
                                    cell.delete_supVals()
                        else:
                            if cell.writeable:
                                cell.delete_val()

                    if event.key == self.supHoldKey:
                        self.change_sup()

                    if event.key == self.supToggleKey:
                        self.change_sup()

                    if event.key == self.adjustHoldKey:
                        self.change_adjust()

                    if event.key == self.adjustToggleKey:
                        self.change_adjust()

                    if event.key == self.checkKey:
                        self.buttonCheckClick()

                    if event.key == self.solveKey:
                        self.buttonAutosolveClick()

                    if event.key == self.saveGridKey:
                        self.buttonSaveClick()

                    if event.key == self.getGridKey:
                        self.buttonGetClick()

                if event.type == pygame.KEYUP:
                    if event.key == self.supHoldKey:
                        self.change_sup()

                    if event.key == self.adjustHoldKey:
                        self.change_adjust()
            #print(self.buttonSup.colour)
            pygame_widgets.update(events)
            pygame.display.update()
            self.fpsClock.tick(self.FPS)
            frame += 1


class Sudoku:
    def __init__(self, grid: Union[str, np.ndarray] = None, n=None):
        self.grid = self.get_empty_grid(n) if grid is None else self.get_grid_from_str(grid) if isinstance(grid, str) else grid
        self.rows = np.copy(self.grid)
        self.cols = np.transpose(self.rows)
        self.n = self.grid.shape[0]
        self.sqrt = int(self.n ** 0.5)
        self.boxs = self.get_boxes()

    def get_empty_grid(self, n=None):
        if n is None:
            n = 9
        grid = np.zeros((n, n), dtype=int)
        return grid

    def get_grid_from_str(self, str):
        n = int(len(str) ** 0.5)
        grid = np.zeros((n, n), dtype=int)
        for l, char in enumerate(str):
            i = l % n
            j = l // n
            if char.isdigit():
                grid[j][i] = int(char)
        return grid

    def set_grid_from_str(self, str):
        n = int(len(str) ** 0.5)
        grid = np.zeros((n, n), dtype=int)
        for l, char in enumerate(str):
            i = l % n
            j = l // n
            if char.isdigit():
                grid[j][i] = int(char)
        self.__init__(grid, self.n)

    def get_boxes(self):
        self.boxs = np.zeros((self.n, self.n), dtype=int)
        a, b = 0, 0
        for j in range(0, self.n, self.sqrt):
            for i in range(0, self.n, self.sqrt):
                for l in range(self.sqrt):
                    for k in range(self.sqrt):
                        self.boxs[b][a] = self.grid[j+l][i+k]
                        a += 1
                a = 0
                b += 1
        return self.boxs

    def get_box_idx(self, cell):
        i, j = cell
        ai, bi = divmod(i, self.sqrt)
        aj, bj = divmod(j, self.sqrt)
        l = ai + self.sqrt * aj
        k = bi + self.sqrt * bj
        return k, l

    def set_cell_1(self, cell, num):
        i, j = cell
        i -= 1
        j -= 1
        ai, bi = divmod(i, self.sqrt)
        aj, bj = divmod(j, self.sqrt)
        l = ai + self.sqrt * aj
        k = bi + self.sqrt * bj
        self.rows[j][i] = num
        self.cols[i][j] = num
        self.boxs[l][k] = num

    def set_cell(self, cell, num):
        i, j = cell
        k, l = self.get_box_idx(cell)
        self.rows[j][i] = num
        self.cols[i][j] = num
        self.boxs[l][k] = num

    def set_grid_cell(self, cell, num):
        self.set_cell(cell, num)
        i, j = cell
        self.grid[j][i] = num

    def cell_plus_1(self, cell):
        i, j = cell
        k, l = self.get_box_idx(cell)
        self.rows[j][i] += 1
        self.cols[i][j] += 1
        self.boxs[l][k] += 1

    def check_group(self, group):
        numbers = set()
        for number in group:
            if number in numbers:
                return False
            if number:
                numbers.add(number)
        return True

    def check_ordening(self, ordening):
        for group in ordening:
            if not self.check_group(group):
                return False
        return True

    def check(self):
        for ordening in (self.rows, self.cols, self.boxs):
            if not self.check_ordening(ordening):
                return False
        return True

    def check_cell(self, cell):
        i, j = cell
        k, l = self.get_box_idx(cell)
        return self.check_group(self.rows[j]) and self.check_group(self.cols[i]) and self.check_group(self.boxs[l])

    def solve(self):
        assert self.check, 'Insert valid grid.'
        c = 0
        step = +1
        while c < self.n**2:
            j, i = divmod(c, self.n)
            if not self.grid[j][i]:
                val = self.rows[j][i]
                by_sudoku = False
                while not by_sudoku and val < self.n:
                    val += 1
                    self.set_cell((i, j), val)
                    by_sudoku = self.check_cell((i, j))

                if not by_sudoku and val == self.n:
                    self.set_cell((i, j), 0)
                    step = -1
                else:
                    step = +1
            c += step
        return self.rows

    def __str__(self):
        return str(self.rows)

    def __repr__(self):
        return f'Sudoku({self.grid})'


grid_00_00 = ' 68   93  42   6  19  8  4  852 1  77  89    2 9  75 3 2 1   5 85  4 76 473 52  9'
grid_19_01 = '3  9   71   527    9        783    5  961 8         3  2     9 51   6     32   8 '
grid_20_01 = '  3   7     8 2  9 96     1   5    3  5 6  4  1 2 4 6 85    9    4    1   1     6'
grid_21_01 = '4     8   82  6       9  737 143       5            45 9      43 6 1           92'
grid_22_01 = '59     4 1 8     37     9       7 94  9 3 1   46   8    1  87    3  5      4   12'


pygame.init()
sudoku = SudokuGame()
sudoku.game_main()

# import time
# a = Sudoku()
# for grid_str in (grid_00_00, grid_19_01, grid_20_01, grid_21_01, grid_22_01):
#     a.set_grid_from_str(grid_str)
#     t0 = time.perf_counter()
#     a.solve()
#     t1 = time.perf_counter()
#     print(a)
#     print(f'Sudoku solved in {t1 - t0}s')
