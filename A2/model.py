import mesa
from mesa import Model
from mesa.space import MultiGrid
from agents import Citizen, Authority
import numpy as np

class CommunityModel(Model):
    # helper functions
    def next_id(self): # used in agent placement
        self._next_id += 1
        return self._next_id
    def mean_knowledge(self):
        citizen_knowledge = [c.knowledge for c in self.agents if isinstance(c, Citizen)]
        return np.mean(citizen_knowledge)
    def mean_behavior(self):
        citizen_behavior = [c.behavior for c in self.agents if isinstance(c, Citizen)]
        return np.mean(citizen_behavior)
    def mean_net_hb(self):
        citizens = [c for c in self.agents if isinstance(c, Citizen)]
        return np.mean([
            (c.susceptibility + c.severity) / 2 - (c.benefits + c.barriers) / 2
            for c in citizens
            ])
    
    def __init__(self, width = 50, height=50, 
                 authority_density = 0.25,
                 seed=None, authority=False,
                 ):
        super().__init__(seed=seed)
        self._next_id=0 # add underscore to differentiate from mesa method
        self.width = width
        self.height = height
        self.authority_density = authority_density
        self.authority = authority # default no authorities in model
    
        #instantiate grid
        self.grid = MultiGrid(width, height, torus=False) # multigrid so auth and cit can occupy same space

        # citizen placement
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                pos = (x, y)
                unique_id = self.next_id()
                citizen = Citizen(model=self, unique_id=unique_id)
                self.grid.place_agent(citizen, pos)

        # calculate number of authorities based on density
        if self.authority:
            num_authorities = int(self.authority_density * self.grid.width * self.grid.height)
            all_pos = [(x,y) for x in range(self.grid.width) for y in range(self.grid.height)]
            self.random.shuffle(all_pos)
            # place authorities randomly
            for pos in all_pos[:num_authorities]:
                unique_id = self.next_id() # make sure this isnt overwriting citizen IDs
                authority = Authority(self, unique_id=unique_id)
                self.grid.place_agent(authority, pos)
       
        # define data collector
        self.datacollector = mesa.DataCollector(
            # these will go up/down infinitely if no cap is set
            model_reporters = {"Mean Knowledge": self.mean_knowledge,
                               "Mean Behavior": self.mean_behavior,
                               "Net Health Belief": self.mean_net_hb}
        )
        # initialize data collector
        self.datacollector.collect(self)

    # run a step of the model        
    def step(self):
        self.agents.shuffle_do("behave") # authorities are handled in behave function
        self.datacollector.collect(self)