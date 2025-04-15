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
    def mean_fertility(self):
        return np.mean(self.grid.fertility.data) # overall initial fertility is 1 because every square starts at equal fertility level
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
        ag_enabled=True, 
    ):
        self.ag_enabled = ag_enabled
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
                               "MeanFertility": self.mean_fertility,
                               }
        )
        ## Import sugar distribution from raster, define grid property
        self.sugar_distribution = np.genfromtxt(Path(__file__).parent / "sugar-map.txt")
        self.grid.add_property_layer(
            PropertyLayer.from_data("sugar", self.sugar_distribution)
        )
        fertility_map = np.ones((self.width, self.height))
        self.grid.add_property_layer(
            PropertyLayer.from_data("fertility", fertility_map)
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
    ## Define step: Sugar grows back at constant rate of 1, all agents move, then all agents consume, then all see if they die. Then model calculated Gini coefficient.
    def step(self):
        self.agents.shuffle_do("move")
        self.agents.shuffle_do("gather_and_eat")
        if self.ag_enabled:
            self.agents.shuffle_do("plant_sugar") # plant sugar after eating and before dying
        # calculate sugar regrow rate based on amount of sugar in cell after eating/planting
        current_sugar = self.grid.sugar.data
        global_max_sugar = np.max(self.sugar_distribution)
        self.grid.fertility.data = 1 - (current_sugar / global_max_sugar) # cell fertility is inversely related to current sugar capacity
        growth = self.grid.fertility.data
        self.grid.sugar.data += np.minimum(
            self.grid.sugar.data + growth, self.sugar_distribution
            ) # regrowth rate depends on fertility of cell; np.minimum(self.grid.sugar.data + growth, self.sugar_distribution)
        self.agents.shuffle_do("see_if_die")
        self.datacollector.collect(self)