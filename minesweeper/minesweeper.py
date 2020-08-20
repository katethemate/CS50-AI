import itertools
import random
import copy


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self, safes):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        safes_in_sentence = safes.intersection(self.cells)
        if self.count == len(self.cells) - len(safes_in_sentence):
            return self.cells.difference(safes_in_sentence)
        return set()

    def known_safes(self, mines):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        mines_in_sentence = mines.intersection(self.cells)
        if self.count == len(mines_in_sentence):
            return self.cells.difference(mines_in_sentence)
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)
            # delete if empty
            if not sentence.cells:
                self.knowledge.remove(sentence)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)
            # delete if empty
            if not sentence.cells:
                self.knowledge.remove(sentence)

    def infer_new_sentence(self):
        """
        Adds new sentences to the knowledge base based on the concept of subset inference.
        """
        for sentence in self.knowledge:
            knowledge_without_sentence = copy.deepcopy(self.knowledge)
            knowledge_without_sentence.remove(sentence)
            for other_sentence in knowledge_without_sentence:
                if other_sentence.cells.issubset(sentence.cells):
                    new_cells = sentence.cells.difference(other_sentence.cells)
                    new_count = sentence.count - other_sentence.count
                    new_sentence = Sentence(new_cells, new_count)
                    # Avoid duplicate sentences
                    if new_sentence not in self.knowledge:
                        self.knowledge.append(new_sentence)
                        return True
        return False

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
        """
        # mark the cell as a move that has been made
        self.moves_made.add(cell)
        # mark the cell as safe
        self.mark_safe(cell)

        # add a new sentence to the AI's knowledge base based on the value of `cell` and `count`
        new_sentence_cells = set()
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # add neighbouring cell if in bounds and not in mines nor safes
                if 0 <= i < self.height and 0 <= j < self.width and (i, j) not in self.safes and (i, j) not in self.mines:
                    new_sentence_cells.add((i, j))

        if new_sentence_cells:
            new_sentence = Sentence(new_sentence_cells, count)
            self.knowledge.append(new_sentence)

        new_mines_or_safes = True
        new_inference = True

        while new_mines_or_safes or new_inference:

            new_mines_or_safes = False

            for sentence in self.knowledge:
                for safe_cell in sentence.known_safes(self.mines):
                    new_mines_or_safes = True
                    self.mark_safe(safe_cell)

                for mine_cell in sentence.known_mines(self.safes):
                    new_mines_or_safes = True
                    self.mark_mine(mine_cell)

            new_inference = self.infer_new_sentence()

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        if len(self.safes) > len(self.moves_made):
            return random.choice(tuple(self.safes.difference(self.moves_made)))

        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        left_over_cells = []
        for i in range(self.height):
            for j in range(self.width):
                cell = (i, j)
                if cell not in self.mines and cell not in self.moves_made:
                    left_over_cells.append(cell)
        if not left_over_cells:
            return None
        return random.choice(tuple(left_over_cells))
