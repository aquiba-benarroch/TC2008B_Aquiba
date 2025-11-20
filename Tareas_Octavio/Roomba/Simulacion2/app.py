from random_agents.agent import Roomba, ObstacleAgent, TrashAgent, Station, VisitedCell
from random_agents.model import RandomModel

from mesa.visualization import (
    CommandConsole,
    Slider,
    SolaraViz,
    SpaceRenderer,
    make_plot_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def random_portrayal(agent):
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, Roomba):
        portrayal.color = "blue"
        portrayal.marker = "o"
        portrayal.size = 50
    elif isinstance(agent, Station):
        portrayal.color = "red"
        portrayal.marker = "v"
        portrayal.size = 50
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "gray"
        portrayal.marker = "s"
        portrayal.size = 50
    elif isinstance(agent, TrashAgent):
        portrayal.color = "green"
        portrayal.marker = "x"
        portrayal.size = 30
    elif isinstance(agent, VisitedCell):
        portrayal.color = "orange"
        portrayal.marker = "s"
        portrayal.size = 50
        portrayal.alpha = 0.3  # Semi-transparente

    return portrayal

model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "max_steps": {
        "type": "InputText",
        "value": 3000,
        "label": "Maximum Steps",
    },
    "width": Slider("Grid width", 28, 1, 50),
    "height": Slider("Grid height", 28, 1, 50),
    "num_agents": Slider("Number of roombas", 5, 1, 50),
    "rate_obstacles": Slider("Obstacle Rate", 0.1, 0, 0.9, 0.05),
    "rate_trash": Slider("Trash Rate", 0.2, 0, 0.9, 0.05),
}

# Create the model using the initial parameters from the settings
model = RandomModel(
    seed=model_params["seed"]["value"],
    max_steps=model_params["max_steps"]["value"],
    width=model_params["width"].value,
    height=model_params["height"].value,
    num_agents=model_params["num_agents"].value,
    rate_obstacles=model_params["rate_obstacles"].value,
    rate_trash=model_params["rate_trash"].value,
)

def post_process(ax):
    ax.set_aspect("equal")

def post_process_lines(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))

lineplot_component = make_plot_component(
    {"Roombas Alive": "tab:blue", "Trash Collected [%]": "tab:green"},
    post_process=post_process_lines,
)

renderer = SpaceRenderer(
    model,
    backend="matplotlib",
)
renderer.draw_agents(random_portrayal)
renderer.post_process = post_process

page = SolaraViz(
    model,
    renderer,
    components=[lineplot_component, CommandConsole],
    model_params=model_params,
    name="Roomba Simulation",
)