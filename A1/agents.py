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
        #if not possibles: # had to add to handle cases where agents cannot move
            #return
        ## Determine how much sugar is in each possible movement target
        sugar_values = [
            cell.sugar
            for cell in possibles
        ]
        ## Calculate the maximum possible sugar value in possible targets
        max_sugar = max(sugar_values)
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
    ## plant leftover sugar
    def plant_sugar(self):
        current = self.cell.sugar
        #if not (self.sugar > 0 and current < 4): 
            #return # ensure agent has sugar to plant and cell has capacity to hold sugar
        capacity = 4 - current # move the sugar cap for all cells to 4
        to_plant = min(self.sugar, capacity)
        if self.sugar - to_plant > 0 and capacity > 0:
            x, y = self.cell.coordinate
            local_fertility = self.model.grid.fertility.data[x, y]
            if local_fertility == 1.0:
                amount = min(to_plant, 4)
            elif local_fertility == 0.75:
                amount = min(to_plant, 3)
            elif local_fertility == 0.5:
                amount = min(to_plant, 2)
            elif local_fertility == 0.25:
                amount = min(to_plant, 1)
            else:
                amount = 0
            self.cell.sugar += amount
            self.sugar -= amount
         # plant the minimum between the difference (-self.metabolism)
            #of the agent's sugar holdings and their metabolism and the max capacity of a cell (- self.metabolism to avoid total extinction)
            #coord = self.cell.coordinate # access actual coordinate of cell
    ## If an agent has zero or negative sugar, it dies and is removed from the model
    def see_if_die(self):
        if self.sugar <= 0:
            self.remove()

## basically, I want to test whether they always bunch around the piles of densely sugared cells
## so i should find a way to incentivize planting in non-sugared areas
## have fertility score be inversely related to the sugar level in the previous step
## mimics over-farming, forces nomadic behavior
## I anticipate the agents will end up traveling from the northeast and southwest corners to the center and back again as the fertility level fluctuates
## add variable to turn ag on and off
## Can a redistribution of resource change the dynamics of cultural development? 
# Requires: redistribution mechanism (planting), relationship between redistribution and land