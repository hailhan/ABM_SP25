# Not functional yet!!!
# bits and pieces work but if you try to run it altogether it will crash
from mesa import Agent
import numpy as np

class Authority(Agent): # define authority class
    def __init__(self, model, unique_id):
        super().__init__(model)
        self.reliability = model.random.uniform(-1, 1)
        self.unique_id = unique_id
    def behave(self):
        pass

class Citizen(Agent): # define citizen class
    def __init__(self, model, unique_id, 
                 leader=False, knowledge=0, behavior=False):
        super().__init__(model)
        self.unique_id = unique_id # give each agent an id so they can be identified in memory feature
        self.susceptibility = model.random.uniform(-1, 1) # assign random float from -1 to 1 for all health-belief features
        self.severity = model.random.uniform(-1, 1)
        self.benefits = model.random.uniform(-1, 1)
        self.barriers = model.random.uniform(-1, 1)
        self.leader = leader # true if peer leaders enabled
        if self.leader == False: # non-leaders start with no knowledge
            self.knowledge = knowledge
        else: # peer leaders start with random knowledge
            self.knowledge = model.random.uniform(-1, 1)
        self.behavior = behavior # initializes as nothing
        self.interlocutors = {} # initialize empty memory dictionary

    # i will make this behave function more modular eventually
    def behave(self):
        # calculate neighbors
        neighbors = self.model.grid.get_neighbors(pos=self.pos, 
                                                  moore=True, 
                                                  include_center=False)
        # split neighbors into authorities and peers
        authorities = [n for n in neighbors if isinstance(n, Authority)]
        peers = [n for n in neighbors if isinstance(n, Citizen)]
        # handles authority variable implicitly 
        if authorities:
            authority = self.model.random.choice(authorities) # choose authority
            self.knowledge += authority.reliability * 0.1
            self.interlocutors[authority.unique_id] = self.interlocutors.get(authority.unique_id, 0) + 1 # add authority to memory
        
        # handles peer interactions
        elif peers:
            # determine knowledge transfer
            interlocutor = self.model.random.choice(peers)
            if interlocutor.knowledge < 0 and self.knowledge < 0:
                self.knowledge -= 0.1
            elif interlocutor.knowledge > 0 and self.knowledge > 0:
                self.knowledge += 0.1
            elif interlocutor.knowledge > 0 and self.knowledge < 0:
                self.knowledge += 0.1
            else:
                self.knowledge -= 0.1
            # add interlocutor to memory/increase strength of relationship
            self.interlocutors[interlocutor.unique_id] = self.interlocutors.get(interlocutor.unique_id, 0) + 1
       
        # calculate the net effect of the health belief features
        net_hb = max(self.severity, self.susceptibility) - max(self.barriers, self.benefits)

        # calculate peer pressure cue to action based on neighbor behaviors
        peers = [n for n in neighbors if isinstance(n, Citizen)] 

        behaved = [n for n in peers if n.behavior == True]
        ill_behaved = [n for n in peers if n.behavior == False]

        if len(ill_behaved) > 0: # avoid div by zero error
            peer_pressure = len(behaved) / len(ill_behaved)
        else:
            peer_pressure = len(behaved) # doesn't matter that this math doesn't math since the threshold will be bigger than 1

        # check if agent satisfies conditions for behavior
        self.behavior = self.knowledge > 0 and net_hb > 0 and peer_pressure > 1

# Next steps: 
# Break behave function into more modular parts
# figure out a less redundant way to calculate neighbors (only once for peers but needs updating since authorities move)
# flesh out peer leader functionality
# come up with a better way to handle authorities (ie outside of the function)
# check literature to see if there way better ways to model moderating features than with thresholds