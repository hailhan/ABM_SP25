from mesa import Agent

class Authority(Agent): # define authority class
    def __init__(self, model, unique_id):
        super().__init__(model)
        self.reliability = model.random.uniform(-1, 1)
        self.unique_id = unique_id
        low, high = model.reliability_range
        self.reliability = model.random.uniform(low, high)

    def move(self):
        # authority will randomly move to any spot in its moore neighborhood
        possible_steps = list(self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        ))
        self.model.random.shuffle(possible_steps)
        for step in possible_steps:
            if all( # authority can move to any cell that isn't already occupied by an authority
                not isinstance(a, Authority) 
                for a in self.model.grid.get_cell_list_contents(step)
            ):
                self.model.grid.move_agent(self, step)
                break

    def behave(self): # same name as citizen behave for step function
        self.move()

class Citizen(Agent): # define citizen class
    def __init__(self, model, unique_id):
        super().__init__(model)
        self.unique_id = unique_id # give each agent an id so they can be identified in memory feature
        self.susceptibility = model.random.uniform(-1, 1) # assign random float from -1 to 1 for all health-belief features
        self.severity = model.random.uniform(-1, 1) # ask david about this tomorrow
        self.benefits = model.random.uniform(-1, 1)
        self.barriers = model.random.uniform(-1, 1)
        self.knowledge = model.random.uniform(-1, 1) # all agents start with some level of prior knowledge
        self.behavior = self.knowledge > 0 # initializes based on knowledge at start
        self.memory = {} # initialize empty memory dictionary
        self.cached_neighbors = None
    
    def find_neighbors(self):
        if self.model.authority_density == 0:
            # only compute once if authorities are not enabled
            if self.cached_neighbors is None:
                neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
                self.cached_neighbors = neighbors
            neighbors = self.cached_neighbors
        else:
            # calculate neighbors each step when authorities are enabled
            neighbors = self.model.grid.get_neighbors(pos=self.pos, 
                                                  moore=True, 
                                                  include_center=False)
        # split neighbors into authorities and peers
        authorities = [n for n in neighbors if isinstance(n, Authority)]
        peers = [n for n in neighbors if isinstance(n, Citizen)]
        return authorities, peers
    
    def adjust_knowledge(self, authorities, peers):
        # handles authority variable implicitly 
        if len(authorities) > 0:
            authority = self.model.random.choice(authorities) # choose authority
            self.memory[authority.unique_id] = self.memory.get(authority.unique_id, 0) + 1 # add authority to memory
            familiarity = self.memory[authority.unique_id]
            self.knowledge += authority.reliability * familiarity
            
        # handles peer interactions
        elif peers: ## add something to encourage agents to interact more frequently with interlocutors
            interlocutor = self.model.random.choice(peers)
            # add interlocutor to memory/increase strength of relationship
            self.memory[interlocutor.unique_id] = self.memory.get(interlocutor.unique_id, 0) + 1
            familiarity = self.memory[interlocutor.unique_id]
            # determine knowledge transfer
            if interlocutor.knowledge < 0 and self.knowledge < 0:
                self.knowledge -= 0.1 * familiarity
            elif interlocutor.knowledge > 0 and self.knowledge > 0:
                self.knowledge += 0.1 * familiarity
            elif interlocutor.knowledge > 0 and self.knowledge < 0:
                self.knowledge += 0.1 * familiarity
            else:
                self.knowledge -= 0.1 * familiarity

        return self.knowledge
    
    def peer_pressure(self, peers):
        # calculate peer pressure cue to action based on neighbor behaviors
        behaved = [n for n in peers if n.behavior == True]
        not_behaved = [n for n in peers if n.behavior == False]

        if len(not_behaved) > 0: # avoid div by zero error
            return len(behaved) / len(not_behaved)
        else:
            return len(behaved) # doesn't matter that this math doesn't math since the threshold will be bigger than 1
        
    def adjust_health_belief(self, peer_pressure):
        self.benefits += 0.1 * (peer_pressure - 0.5)  # boost if > 0.5
        self.barriers -= 0.1 * (peer_pressure - 0.5)  # reduce if > 0.5
        self.benefits = max(-1, min(1, self.benefits)) # cap values
        self.barriers = max(-1, min(1, self.barriers)) # cap values
        self.susceptibility += 0.1 * self.knowledge
        self.severity += 0.1 * self.knowledge
        self.susceptibility = max(-1, min(1, self.susceptibility)) # cap values
        self.severity = max(-1, min(1, self.severity)) # cap values
        return (self.susceptibility + self.severity)/2 - (self.benefits + self.barriers)/2
    
    def behave(self):
        authorities, peers = self.find_neighbors()
        self.knowledge = self.adjust_knowledge(authorities, peers)
        peer_pressure = self.peer_pressure(peers)
        hb = self.adjust_health_belief(peer_pressure)
        # check if agent satisfies conditions for behavior
        self.behavior = hb > 0        
        

# Next steps: 
# figure out a less redundant way to calculate neighbors (only once for peers but needs updating since authorities move)
# check literature to see if there way better ways to model moderating features than with thresholds