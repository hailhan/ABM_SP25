# Not functional yet!!!
# bits and pieces work but if you try to run it altogether it will crash
import mesa
from mesa import Model
from mesa.space import MultiGrid
from agents import Citizen, Authority
import numpy as np
#from mesa.datacollection import DataCollector

class CommunityModel(Model):
    def mean_knowledge(self):
        citizen_knowledge = [c.knowledge for c in self.agents if isinstance(c, Citizen)]
        return np.mean(citizen_knowledge) #if citizen_knowledge else 0.0
    def mean_behavior(self):
        citizen_behavior = [c.behavior for c in self.agents if isinstance(c, Citizen)]
        return np.mean(citizen_behavior)
    def __init__(self, width = 50, height=50, 
                 citizen_density = 1, authority_density = 0.25, 
                 seed=None, authority=False,
                 initial_population = None):
        super().__init__(seed=seed)
        self._next_id=0 # add underscore to differentiate from mesa method
        self.width = width
        self.height = height
        self.citizen_density = citizen_density # all density features will be modifiable by user
        self.authority_density = authority_density
        self.authority = authority # default no authorities in model
        if initial_population is not None:
            total_cells = width * height
            self.citizen_density = initial_population / total_cells

        #instantiate grid
        self.grid = MultiGrid(width, height, torus=False) # multigrid so auth and cit can occupy same space

        # citizen placement
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                #if self.random.random() <= citizen_density:
                pos = (x, y)
                unique_id = self.next_id() # next_id is not functional right now- i think it is from a different version of mesa and I'm scared to mess with packages
                #is_leader = False
                #if not authority: # do something to prevent leaders from losing their knowledge
                    #is_leader = self.random.random() < leader_density
                citizen = Citizen(model=self, unique_id=unique_id)
                self.grid.place_agent(citizen, pos)

        # calculate number of authorities based on density
        if self.authority:
            num_authorities = int(self.authority_density * self.grid.width * self.grid.height)
            all_pos = [(x,y) for x in range(self.grid.width) for y in range(self.grid.height)]
            self.random.shuffle(all_pos)
            # place authorities randomly
            for pos in all_pos[:num_authorities]:
                unique_id = self.next_id()
                authority = Authority(self, unique_id=unique_id)
                self.grid.place_agent(authority, pos)
        # define data collector
        self.datacollector = mesa.DataCollector(
            # these will go up/down infinitely if no cap is set
            model_reporters = {"Mean Knowledge": self.mean_knowledge,
                               "Mean Behavior": self.mean_behavior}
        )
        # initialize data collector
        self.datacollector.collect(self)
    def next_id(self):
        self._next_id += 1
        return self._next_id
    # run a step of the model        
    def step(self):
        self.agents.shuffle_do("behave") # authorities are handled in behave function
        self.datacollector.collect(self)

# Next steps: 
# decide on a scheduler to make sure agents are paired off without overlap each turn
# Add datacollector to collect data on behavior trends
