from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from mesa.datacollection import DataCollector

from .agent import Roomba, ObstacleAgent, TrashAgent, Station

class RandomModel(Model):
    """
    Creates a new model with random agents.
    Args:
        num_agents: Number of agents in the simulation
        height, width: The size of the grid to model
    """
    def _init_(self, num_agents=1, num_obstacles=1, rate_trash=0.2, max_steps=1000, width=8, height=8, seed=42):

        super()._init_(seed=seed)

        # Initialize model parameters
        self.num_agents = num_agents
        self.num_obstacles = num_obstacles
        self.num_trash = int(rate_trash * (width - 2) * (height - 2))
        self.max_steps = max_steps
        self.seed = seed
        self.width = width
        self.height = height

        # Initialize grid
        self.grid = OrthogonalMooreGrid([width, height], torus=False)

        # Setup data collection
        model_reporters = {
            "Trash Collected %": lambda m: (m.num_trash - len(m.agents_by_type[TrashAgent])) / m.num_trash * 100,
            "Battery %": lambda m: next(agent.battery for agent in m.agents_by_type[Roomba])
        }
        self.datacollector = DataCollector(model_reporters)

        # Identify the coordinates of the border of the grid
        border = [(x,y)
                  for y in range(height)
                  for x in range(width)
                  if y in [0, height-1] or x in [0, width - 1]]

        # Create the border cells
        for _, cell in enumerate(self.grid):
            if cell.coordinate == (1,1):
                # Place roomba and station at (1,1)
                Roomba(self, cell=cell)
                Station(self, cell=cell)
            if cell.coordinate in border:
                ObstacleAgent(self, cell=cell)

        ObstacleAgent.create_agents(
            self,
            self.num_obstacles,
            cell=self.random.choices(self.grid.empties.cells, k=self.num_obstacles)
        )

        TrashAgent.create_agents(
            self,
            self.num_trash,
            cell=self.random.choices(self.grid.empties.cells, k=self.num_trash)
        )

        # Collect initial data
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        '''Advance the model by one step.'''
        self.agents.shuffle_do("step")
        
        # Collect data
        self.datacollector.collect(self)

        # Stop the model if all trash is collected
        # Convert max_steps to int because its detected as string from the input
        if len(self.agents_by_type[TrashAgent]) == 0 or self.steps >= int(self.max_steps):
            self.running = False