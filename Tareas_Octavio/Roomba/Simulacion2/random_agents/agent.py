# Artificial intelligence was used to generate some of the code comments.

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
        self.cell = cell  # Current cell of the Roomba
        self.stationCells = [self.cell.coordinate]  # List of known stations (starts with its origin station)
        self.state = "idle"  # Current state of the Roomba (idle, ready, moving, cleaning, returning, recharging, waiting, communicating)
        self.battery = 100  # Battery level (0-100)
        self.visited_cells = {self.cell.coordinate}  # Set of coordinates of visited cells
        self.trash_known_cells = set()  # Set of cells with known trash but not yet cleaned
        self.pathToStation = []  # Calculated path to the nearest station
        self.distance_to_station = 0  # Calculated distance to the nearest station
        self.hasExchangedInfo = False  # Flag to control if info was recently exchanged
        self.exchange_timer = 0  # Timer to avoid multiple consecutive exchanges
        self.steps = 0  # Step counter
        self.hasToRecharge = False  # Flag indicating if it needs to recharge
    
    def checkBattery(self):
        """Checks battery level and decides next action."""
        # Recalculate distance to nearest station
        self.distanceToStation()

        # Safety margin to avoid running out of battery on the way
        step_margin = 20
        total_distance = self.distance_to_station + step_margin

        # If battery is less than or equal to distance + margin, must return to recharge
        if self.battery <= total_distance:
            self.hasToRecharge = True
            self.state = "returning"
        else:
            # If it has enough battery, it's ready to work
            self.state = "ready"
    
    def checkStation(self):
        """Checks if the station is still occupied."""
        # Look for a station in neighboring cells
        station_cell = next(
            (cell for cell in self.cell.neighborhood
            if any(isinstance(obj, Station) for obj in cell.agents)), None
        )
        if station_cell:
            occupied = self.stationOccupied(station_cell)
            if not occupied:
                # If not occupied, can move and start recharging
                self.state = "recharging"
                self.move(station_cell)
            else:
                # If occupied, must wait
                self.state = "waiting"

    def checkTrash(self):
        """Checks if there is trash in the current cell."""
        # Look for a trash agent in the current cell
        trash_cell = next(
            (obj for obj in self.cell.agents if isinstance(obj, TrashAgent)), None
        )

        # If returning to the station and finds trash, save it for cleaning later
        if (self.state == "returning") and trash_cell:
            self.trash_known_cells.add(self.cell.coordinate)
            return
        
        # If found trash, change to cleaning state
        if trash_cell:
            self.state = "cleaning"
        else:
            # If no trash, proceed to check obstacles
            self.state = "checkObstacles"
        return trash_cell
    
    def checkObstacles(self):
        """Chooses next cell prioritizing unvisited and obstacle-free cells."""
        # Select valid neighboring cells (without obstacles)
        valid_neighbors = self.cell.neighborhood.select(
            lambda cell: not any(isinstance(obj, ObstacleAgent) for obj in cell.agents)
        )

        # Among valid neighbors, prioritize those with trash
        trash_cells = valid_neighbors.select(
            lambda cell: any(isinstance(obj, TrashAgent) for obj in cell.agents)
        )

        # Get unvisited cells
        unvisited_cells = valid_neighbors.select(
            lambda cell: cell.coordinate not in self.visited_cells
        )

        # Selection priority: trash > unvisited > any valid
        if trash_cells:
            # Priority 1: If there's trash in neighbors, go there
            next_cell = trash_cells.select_random_cell()
        elif unvisited_cells:
            # Priority 2: If there are unvisited cells, explore them
            next_cell = unvisited_cells.select_random_cell()
        else:
            # Priority 3: If all neighbors are visited, use pathfinding
            # First check if there's known trash stored
            if self.trash_known_cells:
                path = self.pathToNearestTrash()
            else:
                # If no known trash, find the nearest unvisited cell
                path = self.pathToNearestUnvisited()
            
            if len(path) > 0:
                # Follow the first step of the calculated path
                next_coord = path[0]
                next_cell = self.model.grid[next_coord]
            else:
                # If all cells have been visited, choose any valid neighbor
                next_cell = valid_neighbors.select_random_cell()
        
        self.state = "moving"
        return next_cell

    def checkRoomba(self, roomba_cell):
        """Checks if there are other Roombas in neighboring cells to exchange information."""
        # Get cells with other Roombas
        roomba_cells = roomba_cell.neighborhood.select(
            lambda cell: any(isinstance(obj, Roomba) 
            and obj != self for obj in cell.agents)
        )

        # Get the first Roomba agent found in those cells
        roomba_agent = next(
            (obj for cell in roomba_cells for obj in cell.agents
            if isinstance(obj, Roomba) and obj != self), None
        )

        # If found another Roomba and hasn't exchanged info recently, communicate
        if roomba_agent and not self.hasExchangedInfo:
            self.state = "communicating"
        else:
            # If no Roomba or already exchanged info, proceed to check trash
            self.state = "checkTrash"
        return roomba_agent

    def move(self, cell):
        """Moves the Roomba to the specified cell."""

        # If the cell is a station and it's occupied, wait
        if cell.coordinate in self.stationCells and self.hasToRecharge and self.stationOccupied(cell):
            self.state = "waiting"
            return

        # Move to the new cell
        self.cell = cell

        # Mark cell as visited in the Roomba's memory
        self.visited_cells.add(cell.coordinate)
        
        # Mark cell as visited in the model's grid for visualization
        # This will allow VisitedCell markers to be created in orange color
        self.model.visited_grid.add(cell.coordinate)
        self.steps += 1
        
        # Check if arrived at a station
        if self.cell.coordinate in self.stationCells and self.hasToRecharge:
            occupied = self.stationOccupied(self.cell)
            if not occupied:
                # If station is free, start recharging
                self.state = "recharging"
                self.pathToStation = []  # Clear path when arrived
            else:
                # If occupied, wait
                self.state = "waiting"
        else:
            # If not a station or doesn't need to recharge, return to idle
            self.state = "idle"
    
    def clean(self, trash_cell):
        """Cleans the trash in the current cell."""
        # Mark cell as clean and remove the trash agent
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
        """Selects the next cell to move towards the station."""

        # If there's no calculated path, calculate it
        if not self.pathToStation:
            self.calculateReturn()

            if not self.pathToStation:
                # If still no path, don't move
                return None
        
        # Follow the path step by step
        if self.pathToStation:
            next_coord = self.pathToStation.pop(0)  # Get the first coordinate and remove it from the list
            next_cell = self.model.grid[next_coord]
            self.state = "moving"
            return next_cell
        else:
            # If there's no path, remain idle
            self.state = "idle"
            return None

    def calculateReturn(self):
        """
        Calculates distance to all free known stations and the path to the nearest one.
        """
        start = self.cell.coordinate

        # Filter available stations (not occupied)
        available_stations = [
            coord for coord in self.stationCells
            if not self.stationOccupied(self.model.grid[coord])
        ]

        # If all stations are occupied, wait
        if not available_stations:
            self.state = "waiting"
            self.pathToStation = []
            return

        # Select the nearest station using Chebyshev distance
        nearest_station = self.distanceToStation(available_stations)

        if nearest_station is None:
            self.state = "waiting"
            self.pathToStation = []
            return

        # Calculate the path using A* to the nearest station
        path = self.a_star(start, nearest_station)
        
        if path:
            self.pathToStation = path
        else:
            # If path cannot be calculated, wait
            self.state = "waiting"
            self.pathToStation = []
    
    def recharge(self):
        """Recharges the Roomba's battery."""
        # Increase battery by 5 units per step
        self.battery += 5
        if self.battery >= 100:
            # When battery reaches 100, stop recharging
            self.battery = 100
            self.hasToRecharge = False
            self.state = "idle"
    
    def pathToNearestUnvisited(self):
        """
        Find the nearest unvisited cell to the roomba

        Similar to A*, but we stop when we find the first unvisited cell.
        Then the path to that cell is calculated using A*.
        """
        grid = self.model.grid
        start = self.cell.coordinate

        visited = set(start)
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

    def pathToNearestTrash(self):
        """From known trash cells, finds the nearest one and returns the path."""
        # Take the last added trash cell (the nearest one)
        trash_cell = self.trash_known_cells.pop()
        # Calculate and return the path using A*
        return self.a_star(self.cell.coordinate, trash_cell)

    def distanceToStation(self, stations=None):
        """Using ChebyShev, calculate smallest distance to known stations and return the nearest station cell."""

        # If no stations provided, use all known stations
        if stations is None:
            stations = self.stationCells
        
        if not stations:
            self.distance_to_station = float('inf')
            return None

        min_distance = float('inf')
        nearest_station = None
        current_x, current_y = self.cell.coordinate

        # Find the nearest known station
        for coord in stations:
            base_x, base_y = coord
            distance = max(abs(current_x - base_x), abs(current_y - base_y))
            if distance < min_distance:
                min_distance = distance
                nearest_station = coord

        self.distance_to_station = min_distance
        return nearest_station

    def exchangeInfo(self, other_roomba):
        """Updates the set of visited cells and known stations with those from the other Roomba."""
        # Exchange visited cells information
        for cell in other_roomba.visited_cells:
            if cell not in self.visited_cells:
                self.visited_cells.add(cell)
        
        # Exchange known stations information
        for station_coord in other_roomba.stationCells:
            if station_coord not in self.stationCells:
                self.stationCells.append(station_coord)
        
        # Set timer to avoid multiple exchanges in a short time
        self.hasExchangedInfo = True
        self.exchange_timer = 10  # Steps before allowing new exchanges
        self.state = "idle"
    
    def stationOccupied(self, station_cell):
        """Checks if a station cell is occupied by another recharging Roomba."""
        # Returns True if there's another Roomba (not this one) in recharging state in the cell
        occupied = any(
            isinstance(agent, Roomba) and agent is not self and agent.state == "recharging"
            for agent in station_cell.agents
        )
        return occupied

    def step(self):
        """
        Executes one step of the Roomba's behavior based on the state machine.
        
        Possible states:
        - idle: Initial state, checks battery
        - waiting: Waiting for the station to become available
        - returning: Returning to station to recharge
        - recharging: Recharging battery at the station
        - ready: Ready to work (sufficient battery)
        - communicating: Exchanging information with another Roomba
        - cleaning: Cleaning trash
        - moving: Moving to another cell
        """

        # Initial state checks
        if self.state == "idle":
            # If idle, check battery level
            self.checkBattery()
        elif self.state == "waiting":
            # If waiting, check if the station is now free
            self.checkStation()
        
        # After initial checks, execute based on current state
        if self.state == "returning":
            # If returning to the station
            self.checkTrash()  # Check for trash along the way
            next_cell = self.getNextReturnMove()  # Get next step towards the station
            if next_cell and self.state == "moving":
                self.move(next_cell)
        elif self.state == "recharging":
            # If recharging, increase battery
            self.recharge()
        elif self.state == "ready":
            # If ready to work
            roomba_agent = self.checkRoomba(self.cell)  # Check if there are other Roombas nearby
            if self.state == "communicating":
                # If found another Roomba, exchange information
                self.exchangeInfo(roomba_agent)
            elif self.state == "checkTrash":
                # If no Roomba or already exchanged info, look for trash
                trash_cell = self.checkTrash()
                if self.state == "cleaning":
                    # If there's trash, clean it
                    self.clean(trash_cell)
                elif self.state == "checkObstacles":
                    # If no trash, find the next cell to explore
                    next_cell = self.checkObstacles()
                    if self.state == "moving":
                        self.move(next_cell)
        
        # Handle information exchange timer
        if self.exchange_timer > 0:
            self.exchange_timer -= 1
            if self.exchange_timer == 0:
                # When timer reaches 0, can exchange information again
                self.hasExchangedInfo = False
        
        # Always decrease battery by 1 at the end of the step, except when recharging or waiting
        if self.state not in ["recharging", "waiting"]:
            self.battery -= 1
        
        # If battery reaches 0, the Roomba is removed (runs out of energy)
        if self.battery <= 0:
            self.remove()

class TrashAgent(FixedAgent):
    @property
    def with_trash(self):
        """Whether the cell has trash."""
        return self._with_trash
    
    @with_trash.setter
    def with_trash(self, value: bool) -> None:
        """Set trash presence state."""
        self._with_trash = value

    def __init__(self, model, cell):
        """Create a new trash object

        Args:
            model: Model instance
            cell: Cell to which this trash object belongs
        """
        super().__init__(model)
        self.cell=cell
        self._with_trash = True

class Station(FixedAgent):
    """
    Station agent. Just to add charging stations to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass

class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, model, cell):
        super().__init__(model)
        self.cell=cell

    def step(self):
        pass


class VisitedCell(FixedAgent):
    """
    Visual marker for cells that have been visited by a Roomba.
    This agent is purely for visualization purposes.
    """
    def __init__(self, model, cell):
        """Create a visual marker for a visited cell.
        
        Args:
            model: Model instance
            cell: Cell that has been visited
        """
        super().__init__(model)
        self.cell = cell

    def step(self):
        """Visited cells don't perform any actions."""
        pass