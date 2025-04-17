import math

## Using experimental agent type with native "cell" property that saves its current position in cellular grid
from mesa.experimental.cell_space import CellAgent

## Helper function to get distance between two cells
def get_distance(cell_1, cell_2):
    x1, y1 = cell_1.coordinate
    x2, y2 = cell_2.coordinate
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx**2 + dy**2)

class SugarAgent(CellAgent):
    ## Initiate agent, inherit model property from parent class
    def __init__(self, model, cell, sugar=0, metabolism=0, vision=0):
        super().__init__(model)
        ## Set variable traits based on model parameters
        self.cell = cell
        self.sugar = sugar
        self.metabolism = metabolism
        self.vision = vision
    ## Define movement action
    def move(self):
        ## Determine currently empty cells within line of sight
        possibles = [
            cell
            for cell in self.cell.get_neighborhood(self.vision, include_center=True)
            if cell.is_empty 
        ]
        ## Determine how much sugar is in each possible movement target
        sugar_values = [
            cell.sugar
            for cell in possibles
        ]
        if sugar_values:
            ## Calculate the maximum possible sugar value in possible targets
            max_sugar = max(sugar_values)
        else:
            max_sugar = 0
        ## Get indices of cell(s) with maximum sugar potential within range
        candidates_index = [
            i for i in range(len(sugar_values)) if math.isclose(sugar_values[i], max_sugar)
        ]
        ## Indentify cell(s) with maximum possible sugar
        candidates = [
            possibles[i]
            for i in candidates_index
        ]
        if not candidates: # added
            return
        ## Find the closest cells with maximum possible sugar
        min_dist = min(get_distance(self.cell, cell) for cell in candidates)
        final_candidates = [
            cell
            for cell in candidates
            if math.isclose(get_distance(self.cell, cell), min_dist, rel_tol=1e-02)
        ]
        ## Choose one of the closest cells with maximum sugar (randomly if more than one)
        self.cell = self.random.choice(final_candidates)
    ## consume sugar in current cell, depleting it, then consume metabolism
    def gather_and_eat(self):
        self.sugar += self.cell.sugar
        self.cell.sugar = 0
        self.sugar -= self.metabolism
        #x, y = self.cell.coordinate
        #self.model.grid.eaten.data[x, y] = True
    ## plant leftover sugar
    def plant_sugar(self):
        current = self.cell.sugar # get the current amount of sugar in the cell
        capacity = 4 - current # carrying capacity of ANY cell is 4
        to_plant = min(self.sugar, capacity) # plant the minimum between agent's sugar holdings and capacity
        safety = self.sugar - self.metabolism
        if safety > 0: # protecting the poor
            to_plant = min(capacity, safety)
            self.cell.sugar += to_plant
            self.sugar -= to_plant
       # amount = 0 
        #if capacity > 0: # if cell has capacity for more sugar # ensure agent won't starve by planting self.sugar - to_plant > 0 and
            #x, y = self.cell.coordinate
            #local_fertility = self.model.grid.fertility.data[x, y]
            # soil fertility determines max amount agent can plant
            #if local_fertility == 1.0:
             #   amount = 4
            #elif local_fertility == 0.75:
             #   amount = 3
            #elif local_fertility == 0.5:
             #   amount = 2
            #elif local_fertility == 0.25:
             #   amount = 1  
            #self.cell.sugar += min(amount, self.sugar) # plant amount of sugar
            #self.sugar -= amount # remove planted sugar from agent's holdings
            #self.model.grid.planted.data[x, y] = True

    ## If an agent has zero or negative sugar, it dies and is removed from the model
    def see_if_die(self):
        if self.sugar <= 0:
            self.remove()

### IF PLANTED, I WANT TO RAISE THE MIN SUGAR
## basically, I want to test whether they always bunch around the piles of densely sugared cells
## so i should find a way to incentivize planting in non-sugared areas
## have fertility score be inversely related to the sugar level in the previous step
## mimics over-farming, forces nomadic behavior
## I anticipate the agents will end up traveling from the northeast and southwest corners to the center and back again as the fertility level fluctuates
## add variable to turn ag on and off
## Can a redistribution of resource change the dynamics of cultural development? 
# Requires: redistribution mechanism (planting), relationship between redistribution and land