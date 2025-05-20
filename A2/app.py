import solara
from agents import Citizen, Authority
from model import CommunityModel
from mesa.visualization import (  
    SolaraViz,
    make_plot_component
)
from mesa.visualization.components.matplotlib_components import make_mpl_space_component

def agent_portrayal(agent):
    # combined functions to pass into community_space
    if isinstance(agent, Citizen):
        return {
            'marker': 'o',
            'color': 'blue' if agent.behavior == True else 'red',
            'size': 20
        }
    elif isinstance(agent, Authority):
        return {
            'marker': 's',
            'color': 'white',
            'size': 10
        }
    else:
        return {
            'marker': 'x',
            'color': 'gray',
            'size': 5
        }

community_space = make_mpl_space_component(
    agent_portrayal=agent_portrayal, # single function instead of list of functions
    post_process=None,
    draw_grid=False,
)

# define model reporter plots
KnowledgePlot = make_plot_component("Mean Knowledge")
BehaviorPlot = make_plot_component("Mean Behavior")

model_params = {
    "seed": {
        "type": "InputText",
        "value": 0,
        "label": "Random Seed"
    },
    "width": 50,
    "height": 50,
    "authority": {
        "type":"Checkbox",
        "value": False,
        "label": "Enable Authorities"
    }
}

##Instantiate model
#model = CommunityModel()

## Define all aspects of page
page = SolaraViz(
    CommunityModel(),
    components=[
        community_space,
        KnowledgePlot,
        BehaviorPlot
    ],
    model_params=model_params,
    name="Community",
    play_interval=150,
)
## Return page
page