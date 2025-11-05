# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self):
        """Compute the next state based on the custom rules."""
        # Asignar nombres a las celdas vecinas basadas en sus coordenadas relativas
        # Consideramos solo los vecinos de arriba: top-left, top-center, top-right
        izquierda_pos = (self.pos[0] - 1) % 50, (self.pos[1] + 1) % 50 # arriba-izquierda
        arriba_pos = self.pos[0], (self.pos[1] + 1) % 50        # arriba
        derecha_pos = (self.pos[0] + 1) % 50, (self.pos[1] + 1) % 50     # arriba-derecha

        izquierda = 0
        arriba = 0
        derecha = 0

        for neighbor in self.neighbors:
            if neighbor.pos == izquierda_pos:
                izquierda = neighbor.is_alive
            elif neighbor.pos == arriba_pos:
                arriba = neighbor.is_alive
            elif neighbor.pos == derecha_pos:
                derecha = neighbor.is_alive
        # print(izquierda, arriba, derecha)

        self._next_state = self.state
        
        # SOLUCION 1: 
        #Reglas
        if not self.is_alive:
             # 111 -> 0
            if izquierda and arriba and derecha:
                self._next_state = self.DEAD
            # 110 -> 1
            elif izquierda and arriba and not derecha:
                self._next_state = self.ALIVE
            # 101 -> 0
            elif izquierda and not arriba and derecha:
                self._next_state = self.DEAD
            # 100 -> 1
            elif izquierda and not arriba and not derecha:
                self._next_state = self.ALIVE
            # 011 -> 1
            elif not izquierda and arriba and derecha:
                self._next_state = self.ALIVE
            # 010 -> 0
            elif not izquierda and arriba and not derecha:
                self._next_state = self.DEAD
            # 001 -> 1
            elif not izquierda and not arriba and derecha:
                self._next_state = self.ALIVE
            # 000 -> 0
            elif not izquierda and not arriba and not derecha:
                self._next_state = self.DEAD
        
        
    
    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state
