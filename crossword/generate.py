import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains_of_x = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.crossword.variables:
            for word in self.domains_of_x[var].copy():
                if len(word) != var.length:
                    self.domains_of_x[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap = self.crossword.overlaps[x, y]
        revised = False
        if overlap:
            for x_word in self.domains_of_x[x]:
                if not [True if y_word[overlap[1]] == x_word[overlap[0]] else None for y_word in self.domains_of_x[y]]:
                    self.domains_of_x[x].remove(x_word)
                    revised = True

        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            arcs = []
            for var1 in self.crossword.variables:
                for var2 in self.crossword.neighbors(var1):
                    arcs.append((var1, var2))
        while arcs:
            arc = arcs.pop(0)
            if self.revise(arc[0], arc[1]):
                # if there is an empty domain the problem cannot be solved
                if not self.domains_of_x[arc[0]]:
                    return False
                ''' some neighbor y of var x that was arc-consistent with x 
                might no longer be because x's domain was reduced'''
                for var in self.crossword.neighbors(arc[0]):
                    if var == arc[1]:
                        continue
                    if (var, arc[0]) not in arcs:
                        arcs.append((var, arc[0]))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return (assignment.keys() == self.crossword.variables)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # check if all arcs are consistent (no conflicts between neighboring variables)
        overlaps = self.crossword.overlaps
        for var1, val1 in assignment.items():
            for var2, val2 in assignment.items():
                if var1 == var2:
                    continue
                if overlaps[var1, var2]:
                    overlap_indices = overlaps[var1, var2]
                    if val1[overlap_indices[0]] != val2[overlap_indices[1]]:
                        return False

        # check if all values are distinct and that very value has the correct length
        values = []
        for variable, value in assignment.items():
            if value in values or len(value) != variable.length:
                return False
            values.append(value)

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        ordered_domains = []
        for word in self.domains_of_x[var]:
            amount_eliminated = 0
            for neighbor in self.crossword.neighbors(var):
                if neighbor not in assignment:
                    overlap = self.crossword.overlaps[var, neighbor]
                    for neighbor_word in self.domains_of_x[neighbor]:
                        if neighbor_word[overlap[1]] != word[overlap[0]]:
                            amount_eliminated += 1
            ordered_domains.append((amount_eliminated, word))
        ordered_domains.sort(key=lambda tup: tup[0])
        return [domain[1] for domain in ordered_domains]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # create domain dictionary of only unassigned variables
        unassigned_vars = self.crossword.variables.difference(
            assignment.keys())
        length_of_domain = [(len(self.domains_of_x[var]), var)
                            for var in unassigned_vars]
        min_domain = min(length_of_domain, key=lambda tup: tup[0])

        # list of all vars with min_domains amount of domains
        ties = [x for x in unassigned_vars if len(self.domains_of_x[x])
                == min_domain[0]]

        # if there is a tie between unassigned variables, choose the one with a higher degree
        if len(ties) > 1:
            max_degree = 0
            for var in ties:
                degree = len(self.crossword.neighbors(var))
                if degree > max_degree:
                    max_degree = degree
                    var_to_be_assigned = var
        else:
            var_to_be_assigned = ties[0]

        return var_to_be_assigned

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            new_assignment = assignment.copy()
            new_assignment[var] = value
            arcs = [(neighbor, var)
                    for neighbor in self.crossword.neighbors(var)]
            self.ac3(arcs=arcs)
            if self.consistent(new_assignment):
                result = self.backtrack(new_assignment)
                if result:
                    return result
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
