from mesa.discrete_space import CellAgent, FixedAgent
from collections import deque
import heapq

class Roomba(CellAgent):
    """
    Agent that moves randomly.
    Attributes:
        unique_id: Agent's ID
    """
    def __init__(self, model, cell):
        """
        Creates a new random agent.
        Args:
            model: Model reference for the agent
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell
        self.stationCell = self.cell
        self.state = "idle"
        self.battery = 100
        self.visited_cells = set([self.cell.coordinate])
        self.pathToStation = []
        self.distance_to_station = 0
        self.steps = 0
    
    def checkBattery(self):
        """Check battery level and decide next action."""
        # Calculate current distance to station (Manhattan distance)
        # Get the coordinates of the station
        base_x, base_y = self.stationCell.coordinate
        # Get the current coordinates of the Roomba
        current_x, current_y = self.cell.coordinate
        # Calculate Manhattan distance: sum of absolute differences in x and y
        distance_to_station = abs(current_x - base_x) + abs(current_y - base_y)
        
        # Margin for avoiding running out of battery
        # Add extra steps to ensure the Roomba can reach the station safely
        step_margin = 3
        total_distance = distance_to_station + step_margin

        # If battery is too low to safely return, start returning to station
        if self.battery <= total_distance:
            self.state = "returning"
        else:
            # Otherwise, continue working normally
            self.state = "ready"

    def checkTrash(self):
        """Check for trash in the current cell"""
        trash_cell = next(
            (obj for obj in self.cell.agents if isinstance(obj, TrashAgent)), None
        )
        if trash_cell:
            self.state = "cleaning"
        else:
            self.state = "checkObstacles"
        return trash_cell
    
    def checkObstacles(self):
        """Choose next cell prioritizing non-visited and obstacle-free cells."""
        # Select valid neighboring cells
        valid_neighbors = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        )

        # Among valid neighbors, prefer those with trash
        trash_cells = valid_neighbors.select(
            lambda cell: any(isinstance(obj, TrashAgent) for obj in cell.agents)
        )

        # Get unvisited cells
        unvisited_cells = valid_neighbors.select(
            lambda cell: cell.coordinate not in self.visited_cells
        )

        # Priority: cells with trash > unvisited cells > any valid cell
        if len(trash_cells) > 0:
            next_cell = trash_cells.select_random_cell()
        elif len(unvisited_cells) > 0:
            next_cell = unvisited_cells.select_random_cell()
        else:
            # If all cells have been visited, choose any valid neighbor
            next_cell = valid_neighbors.select_random_cell()
        
        self.state = "moving"
        return next_cell

    def move(self, cell):
        """Move the Roomba to the specified cell."""
        self.cell = cell
        
        # Mark cell as visited
        self.visited_cells.add(cell.coordinate)
        self.steps += 1
        self.state = "idle"
    
    def clean(self, trash_cell):
        """If possible, clean the trash in the current cell."""
        if trash_cell and trash_cell.with_trash:
            trash_cell.with_trash = False
            trash_cell.remove()
            self.state = "idle"
    
    def a_star(self, start, goal):
        """
        A* pathfinding algorithm adapted for the grid in the model

        This algorithm was adapted from the advanced algorithm class
        with Lizbeth Peralta.
        """

        # Calculate Manhattan distance
        # We have to estimate heuristic using this distance
        # since it is not given from the model
        # Ref: https://www.geeksforgeeks.org/dsa/a-search-algorithm/
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Initialize variables
        grid = self.model.grid
        stack = [] # Stack of nodes to explore
        c_list = {}  # g values
        visited = set()  # visited nodes

        # Father vector to reconstruct path
        fathers = {}

        # Initialize stack with start node
        # Heap already sorts by smallest f value
        heapq.heappush(stack, (0, start))
        c_list[start] = 0

        # While the stack is not empty
        # Explore neighbors with lowest f value
        while len(stack) > 0:
            
            # Get node with lowest f value
            # This returns f, coordinate
            # but we only need coordinate, so we use _
            _, current = heapq.heappop(stack)

            # If the node hasnt been visited, process it
            if current not in visited:

                # Mark as visited
                visited.add(current)

                # If we reached the goal, finish
                if (current == goal):
                    break

                # Explore neighbors
                # Get valid neighbors (not obstacles)                
                valid_neighbors = grid[current].neighborhood.select(
                    lambda cell: not any(isinstance(a, ObstacleAgent) for a in cell.agents)
                )
                
                # For each valid neighbor, calculate costs and update structures
                for neighbor_cell in valid_neighbors:
                    neighbor = neighbor_cell.coordinate
                    actual_c = c_list[current] + 1 # Cost between nodes is 1

                    # If the new cost is lower, calculate f and add to stack
                    if (actual_c < c_list.get(neighbor, float('inf'))):
                        c_list[neighbor] = actual_c
                        fathers[neighbor] = current
                        f_value = actual_c + heuristic(neighbor, goal)

                        # Add to stack
                        heapq.heappush(stack, (f_value, neighbor))

        # Reconstruct path
        if goal in fathers:
            path = []
            current = goal
            while current != start:
                path.append(current)
                current = fathers[current]
            path.reverse()
            return path
        
        # If no path found, return empty list
        return []

    def getNextReturnMove(self):
        """Select next cell to move towards the station."""

        # If there is no calculated path, calculate it
        if not self.pathToStation:
            self.calculateReturn()
        
        # Follow the path step by step
        if self.pathToStation:
            next_coord = self.pathToStation.pop(0) # Get first coordinate and remove it
            next_cell = self.model.grid[next_coord]
            self.state = "moving"
            return next_cell
        else:
            # If there is no path, stay idle
            self.state = "idle"
            return None

    def calculateReturn(self):
        """Calculate path and distance to station."""
        start = self.cell.coordinate
        goal = self.stationCell.coordinate
        path = self.a_star(start, goal)
        self.pathToStation = path
        self.distance_to_station = len(path)
    
    def recharge(self):
        """Recharge the Roomba's battery."""
        self.battery += 5
        if self.battery >= 100:
            self.battery = 100
            self.state = "idle"
    
    def pathToNearestUnvisited(self):
        """
        Find the nearest unvisited cell to the roomba

        Similar to A*, but we stop when we find the first unvisited cell.
        Then the path to that cell is calculated using A*.
        """
        grid = self.model.grid
        start = self.cell.coordinate

        visited = set([start])
        # Instead of heap with A*, we use queue
        # To get first item inserted
        queue = deque([start])

        # While there are cells to explore
        while len(queue) > 0:
            # Get the next cell to explore
            current = queue.popleft()
            cell = grid[current]

            # If the cell is unvisited and reachable, calculate path
            if cell.coordinate not in self.visited_cells and not any(isinstance(a, ObstacleAgent) for a in cell.agents):
                return self.a_star(start, cell.coordinate)

            # Otherwise, get neeighbors and explore them
            valid_neighbors = cell.neighborhood.select(
                lambda cell: not any(isinstance(a, ObstacleAgent) for a in cell.agents)
            )

            # For each neighbor, add to queue if unvisited
            for neighbor_cell in valid_neighbors:
                neighbor = neighbor_cell.coordinate
                if (neighbor) not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)

        # If no unvisited cell found, return empty path
        return []

    def step(self):
        """
        Execute one step of the Roomba's behavior based on the state machine.
        """
        # Check if Roomba at station and need charging
        if self.cell.coordinate == self.stationCell.coordinate and self.battery < 100:
            self.state = "recharging"
            self.recharge()
            return
        
        if self.state == "idle":
            self.checkBattery()
        
        if self.state == "returning":
            next_cell = self.getNextReturnMove()
            if next_cell and self.state == "moving":
                self.move(next_cell)
        elif self.state == "recharging":
            self.recharge()
        elif self.state == "ready":
            trash_cell = self.checkTrash()
            if self.state == "cleaning":
                self.clean(trash_cell)
            elif self.state == "checkObstacles":
                next_cell = self.checkObstacles()
                if next_cell and self.state == "moving":
                    self.move(next_cell)
        
        # Always decrease battery by 1 at the end of the step, except when recharging
        if self.state != "recharging":
            self.battery -= 1
        
        # If battery reaches 0, remove the agent
        if self.battery <= 0:
            self.remove()


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
        """Set trash presence state."""
        self._with_trash = value

    def __init__(self, model, cell):
        """Create a new trash object

        Args:
            model: Model instance
            cell: Cell to which this trash object belongs
        """
        super().__init__(model)
        self.cell = cell
        self._with_trash = True

    def step(self):
        pass


class Station(FixedAgent):
    """
    Station agent. Just to add charging stations to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass


class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass

