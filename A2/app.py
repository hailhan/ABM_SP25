import solara
from agents import Citizen, Authority
from model import CommunityModel
from mesa.visualization.components.matplotlib_components import make_mpl_space_component
from mesa.visualization import (  
    SolaraViz,
    make_plot_component,
    Slider
    )

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
            'size': 5
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
NetHBPlot = make_plot_component("Net Health Belief")

model_params = {
    "seed": {
        "type": "InputText",
        "value": 0,
        "label": "Random Seed"
    },
    "width": 50,
    "height": 50,
    "authority_density": Slider("Authority Density", value=0, min=0, max=1, step=0.05)
    }


## Define all aspects of page
page = SolaraViz(
    CommunityModel(), # instantiate model
    components=[ # include components to visualize
        community_space,
        KnowledgePlot,
        BehaviorPlot,
        NetHBPlot
    ],
    model_params=model_params,
    name="Community",
    play_interval=150,
)
## Return page
page