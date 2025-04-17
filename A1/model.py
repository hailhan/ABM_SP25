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
    def mean_sugar(self): # debug
        agent_sugars = np.array([a.sugar for a in self.agents])
        return np.mean(agent_sugars)
    def mean_fertility(self): # debugging
        return np.mean(self.grid.fertility.data) # overall initial fertility is 1 because every square starts at equal fertility level
    def regrow(self):
        # Assuming a maximum sugar capacity of 4 per cell
        max_sugar = 4
        planted = self.grid.planted.data
        # Identify the cells that are empty or need regrowth.
        mask = (self.grid.sugar.data == 0) #& (~planted)
        # Get the fertility values for those cells.
        fertility = self.grid.fertility.data[mask]
        # Create an array for the integer regrowth amount, based on fertility ranges.
        regrowth_amount = np.zeros_like(fertility, dtype=int)
        # Use fertility to determine integer regrowth.
        regrowth_amount[(fertility == 1.0)] = 4
        regrowth_amount[(fertility == 0.75)] = 3
        regrowth_amount[(fertility == 0.5)] = 2
        regrowth_amount[(fertility == 0.25)] = 1
        # Add the integer regrowth amounts to the cells, ensuring the cap of 4 is not exceeded.
        new_sugar = self.grid.sugar.data[mask] + regrowth_amount
        self.grid.sugar.data[mask] = np.minimum(new_sugar, max_sugar)
    def update_fertility(self): # update fertility levels at each step
        # calculate updated fertility as the inverse of each cell's sugar divided by carrying capacity cap
        self.grid.fertility.data = 1 - (self.grid.sugar.data/4)
    def save_fertility_matrix(self, filename="fertility_matrix.txt"): # for debugging
        if hasattr(self.grid, "fertility"):
            np.savetxt(filename, self.grid.fertility.data, fmt="%.3f")
        else:
            print("Fertility layer not found in the grid.")
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
        first_step=True,
    ):
        self.ag_enabled = ag_enabled
        self.first_step = first_step
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
                               "SugarHoldings": self.mean_sugar
                               }
        )
        ## Import sugar distribution from raster, define grid property
        self.sugar_distribution = np.genfromtxt(Path(__file__).parent / "sugar-map.txt")
        self.grid.add_property_layer(
            PropertyLayer.from_data("sugar", self.sugar_distribution)
        )
        fertility_map = 1 - (self.sugar_distribution / np.max(self.sugar_distribution))
        #fertility_map = np.zeros_like(self.sugar_distribution)
        self.grid.add_property_layer(
            PropertyLayer.from_data("fertility", fertility_map),
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
    ## Define step: Sugar grows back at constant rate of 1, all agents move, then all agents consume, then all see if they die. Then model calculated Gini coefficient.
    def step(self):
        if not self.first_step:
            self.regrow()
        #self.grid.sugar.data = np.minimum(
            #self.grid.sugar.data + 1, self.sugar_distribution
        #)
        
        self.agents.shuffle_do("move")
        self.agents.shuffle_do("gather_and_eat") # they eat, depleting the cell's capacity to zero
        if self.ag_enabled:
            self.agents.shuffle_do("plant_sugar") # agents plant, amounts according to the cell's fertility at the beginning of the round
        self.agents.shuffle_do("see_if_die")
        self.grid.planted.data[:, :] = False # reset planted state
        self.update_fertility() # new soil fertility stands regardless of ag
        self.datacollector.collect(self) 
        self.first_step=False

#debug
model = SugarScapeModel()

#Run model for a fixed number of steps (until "convergence" or death of most agents)
for _ in range(200):  # Or however many steps you want
   model.step()

# Save fertility matrix after running
model.save_fertility_matrix("fertility_matrix.txt")