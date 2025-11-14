from mesa.discrete_space import CellAgent, FixedAgent

class Roomba(CellAgent):
    """
    Agent that moves randomly.
    Attributes:
        unique_id: Agent's ID
    """

    @property
    def state(self):
        """Return the current state of the Roomba."""
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    
    def __init__(self, model, cell):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell
        self.battery = 100
        self._state = "MOVING"

    def step(self):
        """Execute one step of the animal's behavior."""
        trash_cell = self.checkTrash()

        if trash_cell:
            self.state = "CLEANING"
            self.clean(trash_cell)
        else:
            self.state = "MOVING"
            # Select only cells without obstacles
            cells_without_obstacles = self.cell.neighborhood.select(
                lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
            )
            
            if len(cells_without_obstacles) > 0:
                # Prefer cells with trash
                cells_with_trash = cells_without_obstacles.select(
                    lambda cell: any(isinstance(obj, TrashAgent) and obj.with_trash for obj in cell.agents)
                )
                
                # Move to trash if available, otherwise any safe cell
                if len(cells_with_trash) > 0:
                    next_cell = cells_with_trash.select_random_cell()
                else:
                    next_cell = cells_without_obstacles.select_random_cell()
                    
                self.move(next_cell)
        
        self.battery -= 1

        # Handle death
        if self.battery < 0:
            self.remove()



    def checkObstacles(self):
        """Return the cells with obstacles."""
        return next((obj for obj in self.cell.agents if isinstance(obj, ObstacleAgent)), None)

    def checkTrash(self):
        """Return the cells with trash."""
        return next((obj for obj in self.cell.agents if isinstance(obj, TrashAgent) and obj.with_trash), None)

    def move(self, cell):
        # """Move towards a cell where there isn't an obstacle, and preferably with trash."""
        # cells_without_obstacles = self.cell.neighborhood.select(
        #     lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        # )

        # # Among safe cells, prefer those with trash
        # cells_with_trash = cells_without_obstacles.select(
        #     lambda cell: any(
        #         isinstance(obj, TrashAgent) and obj.with_trash for obj in cell.agents
        #     )
        # )
        # # Move to a cell with trash if available, otherwise move to any safe cell
        # target_cells = (
        #     cells_with_trash if len(cells_with_trash) > 0 else cells_without_obstacles
        # )
        # self.cell = target_cells.select_random_cell()
        self.cell = cell
        # self.state = "MOVING"
    
    def clean(self, trash_cell):
        """If possible, clean the trash in the current cell."""
        if trash_cell and trash_cell.with_trash:
            trash_cell.with_trash = False
            self.battery -= 1  # Energy spent cleaning
            self.state = "MOVING"



class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class TrashAgent(FixedAgent):
    """
    Trash agent. Just to add trash to the grid.
    """
    @property
    def with_trash(self):
        """Whether the cell has trash."""
        return self._with_trash

    @with_trash.setter
    def with_trash(self, value):
        self._with_trash = value

    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell
        self._with_trash = True



