from flask import Flask, render_template, request, jsonify, session
import numpy as np
import random
import json
import os
from collections import deque
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Constants
GRID_SIZE = 10
SHIP_SIZES = [5, 4, 3, 3, 2]
SHIP_NAMES = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
SHIP_CHARS = [name[0] for name in SHIP_NAMES]
TOTAL_SHIP_PARTS = sum(SHIP_SIZES)

# Game session storage
game_sessions = {}

class BattleshipGame:
    def __init__(self, difficulty="medium"):
        # Game grids (None=water, char=ship part)
        self.player_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ai_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Shot tracking grids (True=hit, False=miss, None=not shot)
        self.player_shots = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ai_shots = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Game state
        self.player_hits = 0
        self.ai_hits = 0
        self.game_over = False
        self.winner = None
        self.current_turn = "player"  # player or ai
        self.difficulty = difficulty.lower()
        
        # Power-ups
        self.air_strike_available = True  # Player can use an air strike once per game
        
        # AI state
        self.ai_targets = deque()
        self.ai_hits_queue = deque()
        self.ai_orientation = None
        self.ai_last_hit = None
        self.ai_probability_map = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ai_hunt_mode = True
        self.remaining_player_ships = SHIP_SIZES.copy()
        self.remaining_ai_ships = SHIP_SIZES.copy()
        
        # Track player and AI moves
        self.player_moves = []
        self.ai_moves = []
        
        # Place AI ships
        self.place_ships_random(self.ai_grid)
        
        # Initialize AI probability map
        self.initialize_probability_map()
        
    def initialize_probability_map(self):
        """Initialize AI probability map for targeting"""
        # Start with uniform probabilities
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.ai_probability_map[r][c] = 1
    
    def place_ships_random(self, grid):
        """Place ships randomly on the given grid"""
        for size, name in zip(SHIP_SIZES, SHIP_NAMES):
            placed = False
            while not placed:
                d = random.choice(["H", "V"])
                r, c = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
                if d == "H" and c + size <= GRID_SIZE and all(grid[r][c+i] is None for i in range(size)):
                    for i in range(size):
                        grid[r][c+i] = name[0]
                    placed = True
                elif d == "V" and r + size <= GRID_SIZE and all(grid[r+i][c] is None for i in range(size)):
                    for i in range(size):
                        grid[r+i][c] = name[0]
                    placed = True
    
    def validate_player_ship_placement(self, ships):
        """Validate player ship placements from frontend"""
        # Clear player grid
        self.player_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Check if all ships are placed
        if len(ships) != len(SHIP_SIZES):
            return False
        
        # Place each ship on the grid
        for i, ship in enumerate(ships):
            # Extract ship info
            ship_size = SHIP_SIZES[i]
            ship_char = SHIP_NAMES[i][0]
            ship_row = ship['row']
            ship_col = ship['col']
            ship_direction = ship['direction']
            
            # Validate placement
            if ship_direction == "H":
                if ship_col + ship_size > GRID_SIZE:
                    return False
                for j in range(ship_size):
                    if self.player_grid[ship_row][ship_col + j] is not None:
                        return False
                    self.player_grid[ship_row][ship_col + j] = ship_char
            else:  # V
                if ship_row + ship_size > GRID_SIZE:
                    return False
                for j in range(ship_size):
                    if self.player_grid[ship_row + j][ship_col] is not None:
                        return False
                    self.player_grid[ship_row + j][ship_col] = ship_char
        
        return True
    
    def player_shoot(self, row, col):
        """Process player's shot"""
        # Check if it's player's turn and coordinates are valid
        if self.current_turn != "player" or self.game_over:
            return {"status": "error", "message": "Not your turn or game over"}
        
        # Check if this cell was already shot
        if self.player_shots[row][col] is not None:
            return {"status": "error", "message": "You already shot here"}
        
        # Record player move
        self.player_moves.append((row, col))
        
        hit = self.ai_grid[row][col] is not None
        self.player_shots[row][col] = hit
        
        result = {"status": "success", "hit": hit, "row": row, "col": col}
        
        if hit:
            # Hit a ship
            ship_char = self.ai_grid[row][col]
            self.player_hits += 1
            
            # Check if a ship is sunk
            if self.is_ship_sunk(self.ai_grid, row, col, ship_char):
                ship_idx = next((i for i, name in enumerate(SHIP_NAMES) if name[0] == ship_char), -1)
                if ship_idx != -1:
                    if SHIP_SIZES[ship_idx] in self.remaining_ai_ships:
                        self.remaining_ai_ships.remove(SHIP_SIZES[ship_idx])
                result["shipSunk"] = True
                result["shipName"] = SHIP_NAMES[ship_idx]
                
                # Get all cells of the sunk ship
                ship_cells = []
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if self.ai_grid[r][c] == ship_char:
                            ship_cells.append({"row": r, "col": c})
                result["shipCells"] = ship_cells
        
        # Check if game is over
        if self.player_hits == TOTAL_SHIP_PARTS:
            self.game_over = True
            self.winner = "player"
            result["gameOver"] = True
            result["winner"] = "player"
            return result
        
        # Switch turn
        self.current_turn = "ai"
        return result
    
    def update_probability_map(self):
        """Update AI probability map based on game state"""
        # Reset probability map
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                # Cells that have been targeted have zero probability
                if self.ai_shots[r][c] is not None:
                    self.ai_probability_map[r][c] = 0
                else:
                    self.ai_probability_map[r][c] = 0  # Will be updated below
        
        # Calculate probabilities for each remaining ship
        for ship_size in self.remaining_player_ships:
            # Try placing each ship horizontally and vertically
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    # Check horizontal placement
                    if c + ship_size <= GRID_SIZE:
                        valid = True
                        for i in range(ship_size):
                            if self.ai_shots[r][c+i] is not None and not self.ai_shots[r][c+i]:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                if self.ai_shots[r][c+i] is None:
                                    self.ai_probability_map[r][c+i] += 1
                    
                    # Check vertical placement
                    if r + ship_size <= GRID_SIZE:
                        valid = True
                        for i in range(ship_size):
                            if self.ai_shots[r+i][c] is not None and not self.ai_shots[r+i][c]:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                if self.ai_shots[r+i][c] is None:
                                    self.ai_probability_map[r+i][c] += 1
        
        # Enhance probabilities around known hits
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (self.ai_shots[r][c] is not None and self.ai_shots[r][c] and 
                    not self.is_ship_sunk(self.player_grid, r, c, self.player_grid[r][c])):
                    # Increase probabilities of adjacent cells
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                            self.ai_shots[nr][nc] is None):
                            self.ai_probability_map[nr][nc] *= 3  # Weight adjacent cells higher
        
        # Add pattern-based heuristics for hard difficulty
        if self.difficulty == "hard":
            # Checkerboard pattern enhancement
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r + c) % 2 == 0 and self.ai_shots[r][c] is None:
                        self.ai_probability_map[r][c] += 0.5
            
            # Edge avoidance for larger ships
            if any(size >= 4 for size in self.remaining_player_ships):
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        # Avoid edges for larger ships as they're less likely to be at edges
                        if r == 0 or r == GRID_SIZE-1 or c == 0 or c == GRID_SIZE-1:
                            self.ai_probability_map[r][c] *= 0.8
    
    def get_probability_target(self):
        """Get the highest probability target"""
        max_prob = -1
        targets = []
        
        # Find highest probability cells
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.ai_shots[r][c] is None:
                    prob = self.ai_probability_map[r][c]
                    if prob > max_prob:
                        max_prob = prob
                        targets = [(r, c)]
                    elif prob == max_prob:
                        targets.append((r, c))
        
        # Choose randomly among highest probability targets
        if targets:
            return random.choice(targets)
        
        # If somehow no targets found, pick any valid cell
        valid_targets = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                         if self.ai_shots[r][c] is None]
        if valid_targets:
            return random.choice(valid_targets)
        
        return None  # This should never happen
    
    def ai_shoot(self):
        """AI makes a shot"""
        if self.current_turn != "ai" or self.game_over:
            return {"status": "error", "message": "Not AI's turn or game over"}
        
        target = self.choose_ai_target()
        if not target:
            return {"status": "error", "message": "AI couldn't find a valid target"}
        
        row, col = target
        # Record AI move
        self.ai_moves.append((row, col))
        
        # Perform attack
        hit = self.player_grid[row][col] is not None
        self.ai_shots[row][col] = hit
        
        result = {"status": "success", "hit": hit, "row": row, "col": col}
        
        if hit:
            # Hit a ship
            ship_char = self.player_grid[row][col]
            self.ai_hits += 1
            self.ai_hunt_mode = False
            
            # Update AI targeting information
            self.ai_last_hit = (row, col)
            self.ai_hits_queue.append((row, col))
            
            # Try to determine ship orientation
            if len(self.ai_hits_queue) >= 2 and not self.ai_orientation:
                self.ai_orientation = self.find_orientation()
            
            # Check if the ship is sunk
            if self.is_ship_sunk(self.player_grid, row, col, ship_char):
                ship_idx = next((i for i, name in enumerate(SHIP_NAMES) if name[0] == ship_char), -1)
                if ship_idx != -1:
                    ship_size = SHIP_SIZES[ship_idx]
                    if ship_size in self.remaining_player_ships:
                        self.remaining_player_ships.remove(ship_size)
                
                result["shipSunk"] = True
                result["shipName"] = SHIP_NAMES[ship_idx]
                
                # Get all cells of the sunk ship
                ship_cells = []
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if self.player_grid[r][c] == ship_char:
                            ship_cells.append({"row": r, "col": c})
                result["shipCells"] = ship_cells
                
                # Reset targeting information after sinking a ship
                self.ai_hits_queue.clear()
                self.ai_orientation = None
                self.ai_hunt_mode = True
        
        # Check if game is over
        if self.ai_hits == TOTAL_SHIP_PARTS:
            self.game_over = True
            self.winner = "ai"
            result["gameOver"] = True
            result["winner"] = "ai"
            return result
        
        # Update probability map for next turn
        self.update_probability_map()
        
        # Switch turn
        self.current_turn = "player"
        return result
    
    def choose_ai_target(self):
        """Choose AI target based on difficulty"""
        # Common function to get adjacent unattacked cells around a hit
        def get_adjacent_targets(r, c):
            adjacent = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                    self.ai_shots[nr][nc] is None):
                    adjacent.append((nr, nc))
            return adjacent
        
        # If we're in hunt mode and we have a last hit
        if not self.ai_hunt_mode and self.ai_last_hit:
            r, c = self.ai_last_hit
            adjacent_targets = get_adjacent_targets(r, c)
            
            # If we have a determined orientation, prioritize that direction
            if self.ai_orientation:
                direction = self.ai_orientation
                if direction == "H":
                    horizontal_targets = [(r, nc) for r, nc in adjacent_targets if r == self.ai_last_hit[0]]
                    if horizontal_targets:
                        return random.choice(horizontal_targets)
                else:  # Vertical
                    vertical_targets = [(nr, c) for nr, c in adjacent_targets if c == self.ai_last_hit[1]]
                    if vertical_targets:
                        return random.choice(vertical_targets)
            
            # If we have adjacent targets, choose one of them
            if adjacent_targets:
                return random.choice(adjacent_targets)
        
        # Different targeting strategies based on difficulty
        if self.difficulty == "easy":
            # Random shooting with simple hunting
            if random.random() < 0.3:  # 30% chance to use smart targeting even on easy
                self.update_probability_map()
                return self.get_probability_target()
            else:
                # Pure random targeting
                valid_targets = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                               if self.ai_shots[r][c] is None]
                if valid_targets:
                    return random.choice(valid_targets)
        
        elif self.difficulty == "medium":
            # Simple probability-based targeting
            self.update_probability_map()
            # Sometimes be less optimal (70% optimal)
            if random.random() < 0.3:
                valid_targets = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                               if self.ai_shots[r][c] is None]
                if valid_targets:
                    return random.choice(valid_targets)
            return self.get_probability_target()
        
        elif self.difficulty == "hard":
            # Advanced targeting with optimized probability map
            self.update_probability_map()
            
            # Add special strategies for hard AI
            # 1. If first few moves, target the center area as ships are more likely there
            if len(self.ai_moves) < 5:
                center_targets = [(r, c) for r in range(3, 7) for c in range(3, 7)
                                if self.ai_shots[r][c] is None]
                if center_targets:
                    return random.choice(center_targets)
            
            # 2. Analyze player's shooting pattern to predict ship placements
            if len(self.player_moves) > 5:
                player_hit_pattern = []
                for r, c in self.player_moves:
                    if self.player_shots[r][c] is True:  # If it was a hit
                        player_hit_pattern.append((r, c))
                
                # If player has hits, analyze their pattern for our placement
                if player_hit_pattern:
                    # This is a placeholder for more complex analysis
                    # For now, just boost probability for similar patterns on player's board
                    for source_r, source_c in player_hit_pattern:
                        for dr in range(-1, 2):
                            for dc in range(-1, 2):
                                r, c = source_r + dr, source_c + dc
                                if (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and 
                                    self.ai_shots[r][c] is None):
                                    self.ai_probability_map[r][c] *= 1.1
        
        else:  # extremely_hard
            # Ultimate AI that combines all strategies and uses advanced pattern recognition
            self.update_probability_map()
            
            # 1. Ultimate targeting of ship arrangements
            # First few moves target optimal ship positions
            if len(self.ai_moves) < 3:
                # Start with corners first (common ship placement)
                corners = [(1, 1), (1, 8), (8, 1), (8, 8)]
                valid_corners = [pos for pos in corners if self.ai_shots[pos[0]][pos[1]] is None]
                if valid_corners:
                    return random.choice(valid_corners)
            
            # 2. Next few moves try the central areas (high probability positions)
            if len(self.ai_moves) < 6:
                center_zones = [(r, c) for r in range(3, 7) for c in range(3, 7)
                             if self.ai_shots[r][c] is None]
                if center_zones:
                    # Choose the cell with the highest probability from center
                    best_score = -1
                    best_target = None
                    for r, c in center_zones:
                        if self.ai_probability_map[r][c] > best_score:
                            best_score = self.ai_probability_map[r][c]
                            best_target = (r, c)
                    if best_target:
                        return best_target
            
            # 3. Perfect ship prediction based on available spaces
            # Analyze gaps where ships could fit
            valid_ships = self.get_valid_ship_positions()
            if valid_ships:
                # Calculate best position based on multiple possible ship arrangements
                pos_scores = {}
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if self.ai_shots[r][c] is None:
                            pos_scores[(r, c)] = 0
                
                # Score positions by how many valid ship arrangements they're part of
                for ship_positions in valid_ships:
                    for pos in ship_positions:
                        if pos in pos_scores:
                            pos_scores[pos] += 1
                
                # Find the position with the highest score
                max_score = max(pos_scores.values()) if pos_scores else 0
                best_positions = [pos for pos, score in pos_scores.items() if score == max_score]
                
                if best_positions:
                    return random.choice(best_positions)
            
            # 4. If no perfect prediction, use enhanced probability map with weights
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.ai_shots[r][c] is None:
                        # Parity check (checkerboard pattern) for optimization
                        if (r + c) % 2 == 0:
                            self.ai_probability_map[r][c] *= 1.2
            
            # 5. Learn from player's patterns from previous shots
            if len(self.player_moves) > 3:
                # Analyze player's targeting patterns to predict ship placements
                player_patterns = self.analyze_player_patterns()
                for r, c, weight in player_patterns:
                    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and self.ai_shots[r][c] is None:
                        self.ai_probability_map[r][c] *= (1.0 + weight)
            
            # 3. Use heatmap for advanced targeting
            max_heat = 0
            heatmap = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
            
            # Create a heatmap based on possible ship placements
            for size in self.remaining_player_ships:
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        # Horizontal placements
                        if c + size <= GRID_SIZE:
                            valid = True
                            for i in range(size):
                                if self.ai_shots[r][c+i] is not None and not self.ai_shots[r][c+i]:
                                    valid = False
                                    break
                            if valid:
                                for i in range(size):
                                    if self.ai_shots[r][c+i] is None:
                                        heatmap[r][c+i] += size  # Larger ships get higher weight
                                        max_heat = max(max_heat, heatmap[r][c+i])
                        
                        # Vertical placements
                        if r + size <= GRID_SIZE:
                            valid = True
                            for i in range(size):
                                if self.ai_shots[r+i][c] is not None and not self.ai_shots[r+i][c]:
                                    valid = False
                                    break
                            if valid:
                                for i in range(size):
                                    if self.ai_shots[r+i][c] is None:
                                        heatmap[r+i][c] += size  # Larger ships get higher weight
                                        max_heat = max(max_heat, heatmap[r+i][c])
            
            # Combine heatmap with probability map
            if max_heat > 0:
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if self.ai_shots[r][c] is None:
                            # Normalize heat value and boost probability
                            heat_factor = 1 + (heatmap[r][c] / max_heat)
                            self.ai_probability_map[r][c] *= heat_factor
            
            # Get the highest probability target
            return self.get_probability_target()
        
        # Fallback to random targeting
        valid_targets = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                       if self.ai_shots[r][c] is None]
        if valid_targets:
            return random.choice(valid_targets)
        
        return None
    
    def find_orientation(self):
        """Find orientation of a ship based on hits"""
        if len(self.ai_hits_queue) < 2:
            return None
            
        # Check the last two hits
        hits = list(self.ai_hits_queue)
        r1, c1 = hits[-2]
        r2, c2 = hits[-1]
        
        if r1 == r2:  # Same row means horizontal
            return "H"
        elif c1 == c2:  # Same column means vertical
            return "V"
        
        return None
    
    def get_valid_ship_positions(self):
        """Calculate all valid ship positions for the remaining ships"""
        valid_ships = []
        
        # For each remaining ship, find all valid positions
        for size in self.remaining_player_ships:
            # Check horizontal placements
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE - size + 1):
                    valid = True
                    positions = []
                    for i in range(size):
                        if self.ai_shots[r][c+i] is False:  # If we know there's no ship here
                            valid = False
                            break
                        positions.append((r, c+i))
                    
                    if valid:
                        valid_ships.append(positions)
            
            # Check vertical placements
            for r in range(GRID_SIZE - size + 1):
                for c in range(GRID_SIZE):
                    valid = True
                    positions = []
                    for i in range(size):
                        if self.ai_shots[r+i][c] is False:  # If we know there's no ship here
                            valid = False
                            break
                        positions.append((r+i, c))
                    
                    if valid:
                        valid_ships.append(positions)
        
        return valid_ships
    
    def analyze_player_patterns(self):
        """Analyze player's shooting patterns to predict ship placements"""
        patterns = []
        
        # Analyze hits and misses
        hit_cells = []
        for r, c in self.player_moves:
            if self.player_shots[r][c]:  # If it was a hit
                hit_cells.append((r, c))
        
        # If not enough data, return empty list
        if len(hit_cells) < 2:
            return patterns
            
        # Find patterns in player hit cells
        horizontal_patterns = []
        vertical_patterns = []
        
        for r, c in hit_cells:
            # Check for horizontal patterns (adjacent hits)
            if (r, c+1) in hit_cells:
                horizontal_patterns.append(((r, c), (r, c+1)))
            if (r, c-1) in hit_cells:
                horizontal_patterns.append(((r, c-1), (r, c)))
                
            # Check for vertical patterns (adjacent hits)
            if (r+1, c) in hit_cells:
                vertical_patterns.append(((r, c), (r+1, c)))
            if (r-1, c) in hit_cells:
                vertical_patterns.append(((r-1, c), (r, c)))
        
        # Generate target cells based on patterns
        for (r1, c1), (r2, c2) in horizontal_patterns:
            # Check if there might be more ship cells in this line
            for dc in [-2, -1, 1, 2]:
                nc = c1 + dc
                if 0 <= nc < GRID_SIZE and self.ai_shots[r1][nc] is None:
                    weight = 0.3 if abs(dc) == 1 else 0.1  # Closer cells have higher weight
                    patterns.append((r1, nc, weight))
                    
            for dc in [-2, -1, 1, 2]:
                nc = c2 + dc
                if 0 <= nc < GRID_SIZE and self.ai_shots[r1][nc] is None:
                    weight = 0.3 if abs(dc) == 1 else 0.1
                    patterns.append((r1, nc, weight))
                    
        for (r1, c1), (r2, c2) in vertical_patterns:
            # Check if there might be more ship cells in this line
            for dr in [-2, -1, 1, 2]:
                nr = r1 + dr
                if 0 <= nr < GRID_SIZE and self.ai_shots[nr][c1] is None:
                    weight = 0.3 if abs(dr) == 1 else 0.1
                    patterns.append((nr, c1, weight))
                    
            for dr in [-2, -1, 1, 2]:
                nr = r2 + dr
                if 0 <= nr < GRID_SIZE and self.ai_shots[nr][c1] is None:
                    weight = 0.3 if abs(dr) == 1 else 0.1
                    patterns.append((nr, c1, weight))
        
        return patterns
    
    def is_ship_sunk(self, grid, r, c, ship_char):
        """Check if a ship is completely sunk"""
        # Find all cells belonging to this ship
        ship_cells = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if grid[row][col] == ship_char:
                    ship_cells.append((row, col))
        
        # Check if player grid
        if grid == self.player_grid:
            return all(self.ai_shots[row][col] for row, col in ship_cells)
        
        # If AI grid, check if all ship cells are hit
        return all(self.player_shots[row][col] for row, col in ship_cells)
    
    def player_air_strike(self, target_type, target_index):
        """Process player's air strike (attack whole row or column)"""
        # Check if it's player's turn and air strike is available
        if self.current_turn != "player" or self.game_over or not self.air_strike_available:
            return {"status": "error", "message": "Can't use air strike now"}
        
        # Validate input
        if target_type not in ["row", "column"] or not (0 <= target_index < GRID_SIZE):
            return {"status": "error", "message": "Invalid target"}
        
        # Use the air strike
        self.air_strike_available = False
        
        results = []
        hit_count = 0
        sunk_ships = []
        
        # Process each cell in the row or column
        for i in range(GRID_SIZE):
            if target_type == "row":
                row, col = target_index, i
            else:  # column
                row, col = i, target_index
            
            # Skip cells already shot
            if self.player_shots[row][col] is not None:
                continue
                
            # Record move and process shot
            self.player_moves.append((row, col))
            hit = self.ai_grid[row][col] is not None
            self.player_shots[row][col] = hit
            
            cell_result = {"row": row, "col": col, "hit": hit}
            
            if hit:
                hit_count += 1
                self.player_hits += 1
                ship_char = self.ai_grid[row][col]
                
                # Check if a ship is sunk
                if self.is_ship_sunk(self.ai_grid, row, col, ship_char):
                    ship_idx = next((i for i, name in enumerate(SHIP_NAMES) if name[0] == ship_char), -1)
                    if ship_idx != -1:
                        if SHIP_SIZES[ship_idx] in self.remaining_ai_ships:
                            self.remaining_ai_ships.remove(SHIP_SIZES[ship_idx])
                        
                        # Get all cells of the sunk ship
                        ship_cells = []
                        for r in range(GRID_SIZE):
                            for c in range(GRID_SIZE):
                                if self.ai_grid[r][c] == ship_char:
                                    ship_cells.append({"row": r, "col": c})
                        
                        sunk_ships.append({
                            "shipName": SHIP_NAMES[ship_idx],
                            "shipCells": ship_cells
                        })
            
            results.append(cell_result)
        
        response = {
            "status": "success", 
            "targetType": target_type, 
            "targetIndex": target_index,
            "results": results,
            "hitCount": hit_count,
            "sunkShips": sunk_ships,
            "airStrikeAvailable": False
        }
        
        # Check if game is over
        if self.player_hits >= TOTAL_SHIP_PARTS:
            self.game_over = True
            self.winner = "player"
            response["gameOver"] = True
            response["winner"] = "player"
            return response
        
        # Switch turn to AI
        self.current_turn = "ai"
        return response
    
    def get_game_state(self):
        """Return the current game state for the frontend"""
        return {
            "playerGrid": self.player_grid,
            "aiGrid": self.ai_grid,
            "playerShots": self.player_shots,
            "aiShots": self.ai_shots,
            "playerHits": self.player_hits,
            "aiHits": self.ai_hits,
            "gameOver": self.game_over,
            "winner": self.winner,
            "currentTurn": self.current_turn,
            "difficulty": self.difficulty,
            "remainingPlayerShips": self.remaining_player_ships,
            "remainingAiShips": self.remaining_ai_ships,
            "airStrikeAvailable": self.air_strike_available
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    try:
        data = request.json
        difficulty = data.get('difficulty', 'medium')
        
        game_id = str(uuid.uuid4())
        game = BattleshipGame(difficulty)
        game_sessions[game_id] = game
        
        session['game_id'] = game_id
        
        return jsonify({
            "status": "success",
            "gameId": game_id,
            "aiShips": game.remaining_ai_ships
        })
    except Exception as e:
        app.logger.error(f"Error in new_game: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@app.route('/place_ships', methods=['POST'])
def place_ships():
    try:
        game_id = session.get('game_id')
        if not game_id or game_id not in game_sessions:
            return jsonify({"status": "error", "message": "No active game session"})
        
        game = game_sessions[game_id]
        ships = request.json.get('ships', [])
        
        if not ships:
            return jsonify({"status": "error", "message": "No ships provided"})
        
        if not game.validate_player_ship_placement(ships):
            return jsonify({"status": "error", "message": "Invalid ship placement"})
        
        return jsonify({
            "status": "success",
            "gameState": game.get_game_state()
        })
    except Exception as e:
        app.logger.error(f"Error in place_ships: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@app.route('/player_shoot', methods=['POST'])
def player_shoot():
    try:
        game_id = session.get('game_id')
        if not game_id or game_id not in game_sessions:
            return jsonify({"status": "error", "message": "No active game session"})
        
        game = game_sessions[game_id]
        data = request.json
        row = data.get('row')
        col = data.get('col')
        
        if row is None or col is None:
            return jsonify({"status": "error", "message": "Invalid row or column"})
        
        result = game.player_shoot(row, col)
        
        # If it's now AI's turn and the game is not over, have the AI shoot
        if game.current_turn == "ai" and not game.game_over:
            ai_result = game.ai_shoot()
            result["aiShot"] = ai_result
        
        result["gameState"] = game.get_game_state()
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in player_shoot: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@app.route('/player_air_strike', methods=['POST'])
def player_air_strike():
    try:
        game_id = session.get('game_id')
        if not game_id or game_id not in game_sessions:
            return jsonify({"status": "error", "message": "No active game session"})
        
        game = game_sessions[game_id]
        data = request.json
        target_type = data.get('targetType')  # 'row' or 'column'
        target_index = data.get('targetIndex')
        
        if target_type not in ['row', 'column'] or target_index is None:
            return jsonify({"status": "error", "message": "Invalid target type or index"})
        
        result = game.player_air_strike(target_type, target_index)
        
        # If it's now AI's turn and the game is not over, have the AI shoot
        if game.current_turn == "ai" and not game.game_over:
            ai_result = game.ai_shoot()
            result["aiShot"] = ai_result
        
        result["gameState"] = game.get_game_state()
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in player_air_strike: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@app.route('/get_game_state', methods=['GET', 'POST'])
def get_game_state():
    try:
        # Support both GET and POST methods
        if request.method == 'POST':
            data = request.get_json()
            game_id = data.get('gameId') if data else session.get('game_id')
        else:  # GET
            game_id = session.get('game_id')
            
        if not game_id or game_id not in game_sessions:
            return jsonify({"status": "error", "message": "No active game session"})
        
        game = game_sessions[game_id]
        
        return jsonify({
            "status": "success",
            "gameState": game.get_game_state()
        })
    except Exception as e:
        app.logger.error(f"Error in get_game_state: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

# Clean up old game sessions
@app.before_request
def cleanup_old_sessions():
    # In a real application, you'd want to cleanup old sessions
    # But for simplicity, we'll keep them all for now
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)