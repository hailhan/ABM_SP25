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
    def save_planted_matrix(self, filename="planted_matrix.txt"): # for debugging
        if hasattr(self.grid, "planted"):
            np.savetxt(filename, self.grid.planted.data, fmt="%.3f")
    def mean_sugar(self): # debug more directly than gini
        agent_sugars = [a.sugar for a in self.agents]
        return np.mean(agent_sugars)
    def mean_metabolism(self): # debug
        agent_mets = np.array([a.metabolism for a in self.agents])
        return np.mean(agent_mets)
    def regrow(self): # regrowth depends on whether the cell's carrying capacity has been exceeded
        max_sugar = 4  # assuming a maximum sugar capacity of 4 per cell
        sugar = self.grid.sugar.data # sugar is an array
        planted = self.grid.planted.data # planted is an array depending on the planted states flagged in plant function
        # automatic regrowth for any empty cell
        empty = (sugar == 0) # boolean mask to ID the cells that are empty or need regrowth.
        sugar[empty] += 1
        # planting boosts soil fertility, so anything that was planted below the sugar max in the cell gets an extra sugar
        bonus = 1
        plant_cells = planted & (sugar < max_sugar) # boolean mask to identify any cells that were planted and still have room
        sugar[plant_cells] += bonus
        # over-farming strips soil of nutrients, so any cell that exceeds 
        # its carrying capacity loses all sugar
        over = planted & (sugar > max_sugar) # boolean mask to ID cells that exceeded carrying capacity due to planting
        sugar[over] = 0 # kill off all remaining sugar as a penalty for over-farming
        # regrow sugar based on the minimum between these changes and the max capacity of the sugar in each cell
        self.grid.sugar.data = np.minimum(sugar, max_sugar)
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
        ag_enabled=True, # add variable to turn ag on/off
        #soil_memory=True,
    ):
        self.ag_enabled = ag_enabled
        #self.soil_memory = soil_memory
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
                               "Metabolism": self.mean_metabolism,
                               "Sugar": self.mean_sugar
                               }
        )
        ## Import sugar distribution from raster, define grid property
        self.sugar_distribution = np.genfromtxt(Path(__file__).parent / "sugar-map.txt")
        self.grid.add_property_layer(
            PropertyLayer.from_data("sugar", self.sugar_distribution)
        )
        planted_map = np.zeros_like(self.sugar_distribution, dtype=bool)
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
        self.agents.shuffle_do("move") # agents move to cell with max sugar in field of vision
        self.agents.shuffle_do("gather_and_eat") # agents eat, depleting cell's sugar to zero
        if self.ag_enabled:
            self.agents.shuffle_do("plant_sugar") # agents plant if it won't kill them
        self.agents.shuffle_do("see_if_die") # agents with 0 sugar die
        self.regrow() # sugar regrows at rates determined in regrow function
        #if self.soil_memory == False: # determines whether soil is permanently affected by planting
            #self.grid.planted.data[:, :] = False # reset planted state if soil is resilient
        self.datacollector.collect(self) # collect round data

#debug
model = SugarScapeModel()

#Run model for a fixed number of steps (until "convergence" or death of most agents)
for _ in range(200):  # Or however many steps you want
   model.step()

# Save fertility matrix after running
model.save_planted_matrix("planted_matrix.txt")