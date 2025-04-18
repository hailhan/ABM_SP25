## MY CHANGES ARE IN LINES 21-52, 66-68, 82-84, 92-96, and 114-121 ##

from pathlib import Path
import numpy as np
import mesa
from agents import SugarAgent

## Using experimental cell space for this model that enforces von Neumann neighborhoods
from mesa.experimental.cell_space import OrthogonalVonNeumannGrid
## Use experimental space feature that allows us to save sugar as a property of the grid spaces
from mesa.experimental.cell_space.property_layer import PropertyLayer

class SugarScapeModel(mesa.Model):
    ## Helper function to calculate Gini coefficient, used in plot
    def calc_gini(self):
        agent_sugars = [a.sugar for a in self.agents]
        sorted_sugars = sorted(agent_sugars)
        n = len(sorted_sugars)
        x = sum(el * (n - ind) for ind, el in enumerate(sorted_sugars)) / (n * sum(sorted_sugars))
        return 1 + (1 / n) - 2 * x
    ## Helper function to count total agents, used in plot
    def agent_count(self):
        agents = [a for a in self.agents]
        return len(agents)
    ## Helper function to calc average sugar, used in plot
    def mean_sugar(self):
        agent_sugars = [a.sugar for a in self.agents]
        return np.mean(agent_sugars)
    ## Helper function to calc average metabolism, used in plot
    def mean_metabolism(self):
        agent_mets = np.array([a.metabolism for a in self.agents])
        return np.mean(agent_mets)
    ## Helper function to determine sugar regrowth rules based on cell carrying capacity
    def regrow(self):
        max_sugar = 4  # maximum sugar capacity of any cell
        sugar = self.grid.sugar.data # array of sugar levels in each cell
        planted = self.grid.planted.data # array of planted states in each cell
        # same regrowth mechanism as original when agriculture not enabled
        if not self.ag_enabled: 
            sugar = np.minimum(
            sugar + 1, self.sugar_distribution
        )
        # planting boosts soil fertility, so any planted cell gets an extra sugar
        bonus = 1
        plant_cells = planted # boolean mask to ID planted cells
        sugar[plant_cells] += bonus
        # over-farming strips soil of nutrients, so any cell that exceeds 
        # max_sugar becomes barren
        over = (sugar > max_sugar) # boolean mask to ID cells that exceed max_sugar
        sugar[over] = 0 # get rid of sugar as a penalty for over-farming
        # regrow sugar based on masking criteria
        self.grid.sugar.data = sugar 
    ## Define initiation, inherit seed property from parent class
    def __init__(
        self,
        width = 50,
        height = 50,
        initial_population=200,
        endowment_min=25,
        endowment_max=50,
        metabolism_min=1,
        metabolism_max=5,
        vision_min=1,
        vision_max=5,
        seed = None,
        ag_enabled=True, # added variable to turn ag on/off
    ):
        self.ag_enabled = ag_enabled # initialize variable
        super().__init__(seed=seed)
        ## Instantiate model parameters
        self.width = width
        self.height = height
        ## Set model to run continuously
        self.running = True
        ## Create grid
        self.grid = OrthogonalVonNeumannGrid(
            (self.width, self.height), torus=False, random=self.random
        )
        ## Define datacollector, which calculates current Gini coefficient
        self.datacollector = mesa.DataCollector(
            model_reporters = {"Gini": self.calc_gini, 
                               "Metabolism": self.mean_metabolism, # added for plot
                               "Sugar": self.mean_sugar, # added for plot
                               "NumAgents": self.agent_count # added for plot
                               }
        )
        ## Import sugar distribution from raster, define grid property
        self.sugar_distribution = np.genfromtxt(Path(__file__).parent / "sugar-map.txt")
        self.grid.add_property_layer(
            PropertyLayer.from_data("sugar", self.sugar_distribution)
        )
        ## Create property layer for planted states
        planted_map = np.zeros_like(self.sugar_distribution, dtype=bool) # all cells start at 0 (unplanted)
        self.grid.add_property_layer(
            PropertyLayer.from_data("planted", planted_map)
            )
        ## Create agents, give them random properties, and place them randomly on the map
        SugarAgent.create_agents(
            self,
            initial_population,
            self.random.choices(self.grid.all_cells.cells, k=initial_population),
            sugar=self.rng.integers(
                endowment_min, endowment_max, (initial_population,), endpoint=True
            ),
            metabolism=self.rng.integers(
                metabolism_min, metabolism_max, (initial_population,), endpoint=True
            ),
            vision=self.rng.integers(
                vision_min, vision_max, (initial_population,), endpoint=True
            ),
        )
        ## Initialize datacollector
        self.datacollector.collect(self)
    ## Define step in simulation
    def step(self):
        self.regrow() # sugar regrows at rates determined in regrow function
        self.agents.shuffle_do("move") # agents move to cell with max sugar in field of vision
        self.agents.shuffle_do("gather_and_eat") # agents eat, depleting cell's sugar to zero
        if self.ag_enabled: # running model without ag is effectively the same as running base model
            self.agents.shuffle_do("plant_sugar") # agents plant if they have surplus sugar
        self.agents.shuffle_do("see_if_die") # agents with 0 sugar die
        
        self.datacollector.collect(self) # collect data for step