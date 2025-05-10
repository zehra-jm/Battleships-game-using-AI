import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, StringVar
import random
from collections import deque
import math

# === CONSTANTS ===
GRID_SIZE = 10
SHIP_SIZES = [5, 4, 3, 3, 2]
SHIP_NAMES = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
SHIP_CHARS = [name[0] for name in SHIP_NAMES]
TOTAL_SHIP_PARTS = sum(SHIP_SIZES)

# Colors
WATER_COLOR = "#E3F2FD"  # Light blue for water
SHIP_COLOR = "#607D8B"   # Blue-gray for ships
HIT_COLOR = "#F44336"    # Red for hits
MISS_COLOR = "#BBDEFB"   # Lighter blue for misses
HOVER_COLOR = "#CFD8DC"  # Light gray for hover
SUNK_COLOR = "#B71C1C"   # Darker red for sunk ships

class BattleshipGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Battleship Game")
        self.root.geometry("1200x750")
        self.root.configure(bg="#ECEFF1")  # Light gray background
        
        # Game state
        self.player_grid = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_grid = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.player_btns = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_btns = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        
        self.player_hits = 0
        self.ai_hits = 0
        self.placing_ships = True
        self.current_ship_idx = 0
        self.orientation = "H"  # Default orientation
        
        # AI state
        self.ai_mode = StringVar(value="Medium")
        self.ai_targets = deque()
        self.ai_hits_queue = deque()
        self.ai_orientation = None
        self.ai_last_hit = None
        self.ai_probability_map = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_hunt_mode = True
        self.remaining_player_ships = SHIP_SIZES.copy()
        self.remaining_ai_ships = SHIP_SIZES.copy()
        
        # Track player and AI moves
        self.player_moves = []
        self.ai_moves = []
        
        # UI setup
        self.setup_ui()
        
    def setup_ui(self):
        # Top frame for controls
        top_frame = tk.Frame(self.root, bg="#ECEFF1", pady=10)
        top_frame.pack(fill=tk.X)
        
        # Game title
        title_label = tk.Label(top_frame, text="BATTLESHIP", font=("Helvetica", 24, "bold"), 
                               bg="#ECEFF1", fg="#1976D2")
        title_label.pack(pady=5)
        
        # Status label
        self.status_label = tk.Label(top_frame, text="Place your Carrier (size 5)", 
                                     font=("Helvetica", 14), bg="#ECEFF1")
        self.status_label.pack(pady=5)
        
        # Difficulty selector
        difficulty_frame = tk.Frame(top_frame, bg="#ECEFF1")
        difficulty_frame.pack(pady=5)
        
        tk.Label(difficulty_frame, text="AI Difficulty:", font=("Helvetica", 12), 
                 bg="#ECEFF1").pack(side=tk.LEFT, padx=5)
        
        difficulty_options = ["Easy", "Medium", "Hard", "Extremely Hard"]
        difficulty_menu = ttk.Combobox(difficulty_frame, textvariable=self.ai_mode, 
                                       values=difficulty_options, state="readonly", width=15)
        difficulty_menu.pack(side=tk.LEFT, padx=5)
        
        # Orientation toggle for ship placement
        self.orientation_btn = tk.Button(top_frame, text="Orientation: Horizontal", 
                                         command=self.toggle_orientation, bg="#BBDEFB",
                                         padx=10, pady=5, font=("Helvetica", 10))
        self.orientation_btn.pack(pady=5)
        
        # Auto-place ships button
        auto_place_btn = tk.Button(top_frame, text="Auto-Place Ships", 
                                  command=self.auto_place_player_ships,
                                  bg="#81D4FA", padx=10, pady=5, font=("Helvetica", 10))
        auto_place_btn.pack(pady=5)
        
        # Reset button
        reset_btn = tk.Button(top_frame, text="New Game", command=self.reset_game, 
                             bg="#90CAF9", padx=10, pady=5, font=("Helvetica", 10))
        reset_btn.pack(pady=5)
        
        # Main game area
        main_frame = tk.Frame(self.root, bg="#ECEFF1")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Player board
        player_frame = tk.Frame(main_frame, bg="#ECEFF1", padx=10, pady=10)
        player_frame.grid(row=0, column=0, padx=20)
        
        player_title = tk.Label(player_frame, text="YOUR FLEET", font=("Helvetica", 16, "bold"), 
                               bg="#ECEFF1", fg="#0D47A1")
        player_title.pack(pady=5)
        
        player_board = tk.Frame(player_frame, bg="#ECEFF1")
        player_board.pack()
        
        # AI board
        ai_frame = tk.Frame(main_frame, bg="#ECEFF1", padx=10, pady=10)
        ai_frame.grid(row=0, column=1, padx=20)
        
        ai_title = tk.Label(ai_frame, text="ENEMY WATERS", font=("Helvetica", 16, "bold"), 
                           bg="#ECEFF1", fg="#B71C1C")
        ai_title.pack(pady=5)
        
        ai_board = tk.Frame(ai_frame, bg="#ECEFF1")
        ai_board.pack()
        
        # Bottom frame for stats
        bottom_frame = tk.Frame(self.root, bg="#ECEFF1", pady=10)
        bottom_frame.pack(fill=tk.X)
        
        self.stats_label = tk.Label(bottom_frame, 
                                   text=f"Your hits: 0/{TOTAL_SHIP_PARTS} | AI hits: 0/{TOTAL_SHIP_PARTS}", 
                                   font=("Helvetica", 12), bg="#ECEFF1")
        self.stats_label.pack(pady=5)
        
        # Create the game boards
        self.create_player_board(player_board)
        self.create_ai_board(ai_board)
        
    def create_player_board(self, parent):
        # Create row labels (A, B, C, ...)
        label_frame = tk.Frame(parent, bg="#ECEFF1")
        label_frame.grid(row=0, column=0, sticky="nsew")
        
        # Empty corner cell
        tk.Label(label_frame, width=2, bg="#ECEFF1").pack()
        
        # Create column labels (1, 2, 3, ...)
        for c in range(GRID_SIZE):
            col_frame = tk.Frame(parent, bg="#ECEFF1")
            col_frame.grid(row=0, column=c+1)
            tk.Label(col_frame, text=str(c+1), width=2, bg="#ECEFF1").pack()
        
        # Create the grid with row labels
        for r in range(GRID_SIZE):
            # Row label (A, B, C, ...)
            row_label_frame = tk.Frame(parent, bg="#ECEFF1")
            row_label_frame.grid(row=r+1, column=0)
            tk.Label(row_label_frame, text=chr(65+r), width=2, bg="#ECEFF1").pack()
            
            # Grid buttons
            for c in range(GRID_SIZE):
                btn = tk.Button(parent, width=2, height=1, 
                                bg=WATER_COLOR, relief=tk.RAISED,
                                command=lambda r=r, c=c: self.on_player_board_click(r, c))
                btn.grid(row=r+1, column=c+1, padx=1, pady=1)
                
                # Add hover effect
                btn.bind("<Enter>", lambda e, btn=btn: self.on_hover(btn, True))
                btn.bind("<Leave>", lambda e, btn=btn: self.on_hover(btn, False))
                
                self.player_btns[r][c] = btn
    
    def create_ai_board(self, parent):
        # Create row labels (A, B, C, ...)
        label_frame = tk.Frame(parent, bg="#ECEFF1")
        label_frame.grid(row=0, column=0, sticky="nsew")
        
        # Empty corner cell
        tk.Label(label_frame, width=2, bg="#ECEFF1").pack()
        
        # Create column labels (1, 2, 3, ...)
        for c in range(GRID_SIZE):
            col_frame = tk.Frame(parent, bg="#ECEFF1")
            col_frame.grid(row=0, column=c+1)
            tk.Label(col_frame, text=str(c+1), width=2, bg="#ECEFF1").pack()
        
        # Create the grid with row labels
        for r in range(GRID_SIZE):
            # Row label (A, B, C, ...)
            row_label_frame = tk.Frame(parent, bg="#ECEFF1")
            row_label_frame.grid(row=r+1, column=0)
            tk.Label(row_label_frame, text=chr(65+r), width=2, bg="#ECEFF1").pack()
            
            # Grid buttons
            for c in range(GRID_SIZE):
                btn = tk.Button(parent, width=2, height=1, 
                                bg=WATER_COLOR, relief=tk.RAISED, state="disabled",
                                command=lambda r=r, c=c: self.on_ai_board_click(r, c))
                btn.grid(row=r+1, column=c+1, padx=1, pady=1)
                
                # Add hover effect
                btn.bind("<Enter>", lambda e, btn=btn: self.on_hover(btn, True))
                btn.bind("<Leave>", lambda e, btn=btn: self.on_hover(btn, False))
                
                self.ai_btns[r][c] = btn
    
    def on_hover(self, btn, entering):
        """Add hover effect to buttons"""
        if entering and btn['state'] != 'disabled' and btn['bg'] == WATER_COLOR:
            btn.config(bg=HOVER_COLOR)
        elif not entering and btn['bg'] == HOVER_COLOR:
            btn.config(bg=WATER_COLOR)

    def toggle_orientation(self):
        """Toggle ship placement orientation between horizontal and vertical"""
        if self.orientation == "H":
            self.orientation = "V"
            self.orientation_btn.config(text="Orientation: Vertical")
        else:
            self.orientation = "H"
            self.orientation_btn.config(text="Orientation: Horizontal")
    
    def on_player_board_click(self, r, c):
        """Handle clicks on the player's board"""
        if self.placing_ships:
            self.place_player_ship(r, c)
    
    def on_ai_board_click(self, r, c):
        """Handle clicks on the AI's board"""
        if not self.placing_ships and self.ai_btns[r][c]['state'] != 'disabled':
            # Record player move
            self.player_moves.append((r, c))
            
            if self.ai_grid[r][c]:
                # Hit
                ship_char = self.ai_grid[r][c]
                self.ai_btns[r][c].config(text="💥", bg=HIT_COLOR)
                self.player_hits += 1
                
                # Check if a ship is sunk
                if self.is_ship_sunk(self.ai_grid, r, c, ship_char):
                    self.mark_sunken_ship(self.ai_grid, self.ai_btns, ship_char)
                    ship_idx = next((i for i, name in enumerate(SHIP_NAMES) if name[0] == ship_char), -1)
                    if ship_idx != -1:
                        self.remaining_ai_ships.remove(SHIP_SIZES[ship_idx])
                    messagebox.showinfo("Ship Sunk!", f"You sunk the enemy's {self.get_ship_name(ship_char)}!")
            else:
                # Miss
                self.ai_btns[r][c].config(text="•", bg=MISS_COLOR)
            
            self.ai_btns[r][c].config(state="disabled")
            
            # Update stats
            self.update_stats()
            
            # Check for game end
            if self.player_hits == TOTAL_SHIP_PARTS:
                self.end_game(True)
                return
            
            # AI's turn
            self.status_label.config(text="AI's turn...")
            self.root.after(700, self.ai_turn)
    
    def place_player_ship(self, r, c):
        """Place a player ship on the board"""
        if not self.placing_ships:
            return
            
        size = SHIP_SIZES[self.current_ship_idx]
        name = SHIP_NAMES[self.current_ship_idx]
        ship_char = name[0]
        
        # Check if ship placement is valid
        if self.orientation == "H":
            if c + size > GRID_SIZE:
                messagebox.showerror("Invalid Placement", "Ship extends beyond the board horizontally!")
                return
            if any(self.player_grid[r][c+i] is not None for i in range(size)):
                messagebox.showerror("Invalid Placement", "Ship overlaps with another ship!")
                return
        else:  # Vertical
            if r + size > GRID_SIZE:
                messagebox.showerror("Invalid Placement", "Ship extends beyond the board vertically!")
                return
            if any(self.player_grid[r+i][c] is not None for i in range(size)):
                messagebox.showerror("Invalid Placement", "Ship overlaps with another ship!")
                return
        
        # Place the ship
        if self.orientation == "H":
            for i in range(size):
                self.player_grid[r][c+i] = ship_char
                self.player_btns[r][c+i].config(text="🚢", bg=SHIP_COLOR)
        else:
            for i in range(size):
                self.player_grid[r+i][c] = ship_char
                self.player_btns[r+i][c].config(text="🚢", bg=SHIP_COLOR)
        
        # Move to next ship or start game
        self.current_ship_idx += 1
        if self.current_ship_idx < len(SHIP_SIZES):
            self.status_label.config(text=f"Place your {SHIP_NAMES[self.current_ship_idx]} (size {SHIP_SIZES[self.current_ship_idx]})")
        else:
            self.start_game()
    
    def auto_place_player_ships(self):
        """Automatically place player ships"""
        if not self.placing_ships or self.current_ship_idx > 0:
            # Only allow auto-placement at the beginning
            return
            
        # Clear any existing ships
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.player_grid[r][c] = None
                self.player_btns[r][c].config(text="", bg=WATER_COLOR)
        
        # Auto-place ships
        self.place_ships_random(self.player_grid)
        
        # Update UI
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.player_grid[r][c]:
                    self.player_btns[r][c].config(text="🚢", bg=SHIP_COLOR)
        
        # Start the game
        self.start_game()
    
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
    
    def start_game(self):
        """Start the game after ship placement"""
        self.placing_ships = False
        self.status_label.config(text="Game started - Your turn!")
        self.orientation_btn.config(state="disabled")
        
        # Enable AI board for player attacks
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.ai_btns[r][c].config(state="normal")
        
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
    
    def update_probability_map(self):
        """Update AI probability map based on game state"""
        # Reset probability map
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                # Cells that have been targeted have zero probability
                if self.player_btns[r][c]['state'] == 'disabled':
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
                            if self.player_btns[r][c+i]['state'] == 'disabled' and self.player_grid[r][c+i] is None:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                if self.player_btns[r][c+i]['state'] != 'disabled':
                                    self.ai_probability_map[r][c+i] += 1
                    
                    # Check vertical placement
                    if r + ship_size <= GRID_SIZE:
                        valid = True
                        for i in range(ship_size):
                            if self.player_btns[r+i][c]['state'] == 'disabled' and self.player_grid[r+i][c] is None:
                                valid = False
                                break
                        if valid:
                            for i in range(ship_size):
                                if self.player_btns[r+i][c]['state'] != 'disabled':
                                    self.ai_probability_map[r+i][c] += 1
        
        # Enhance probabilities around known hits
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (self.player_btns[r][c]['state'] == 'disabled' and 
                    self.player_grid[r][c] is not None and 
                    not self.is_ship_sunk(self.player_grid, r, c, self.player_grid[r][c])):
                    # Increase probabilities of adjacent cells
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                            self.player_btns[nr][nc]['state'] != 'disabled'):
                            self.ai_probability_map[nr][nc] *= 3  # Weight adjacent cells higher
        
        # Add pattern-based heuristics for Extremely Hard difficulty
        if self.ai_mode.get() == "Extremely Hard":
            # Checkerboard pattern enhancement
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r + c) % 2 == 0 and self.player_btns[r][c]['state'] != 'disabled':
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
                if self.player_btns[r][c]['state'] != 'disabled':
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
                         if self.player_btns[r][c]['state'] != 'disabled']
        if valid_targets:
            return random.choice(valid_targets)
        
        return None  # This should never happen
    
    def ai_turn(self):
        """AI's turn to attack"""
        target = self.choose_ai_target()
        if not target:
            return  # No valid targets (should not happen)
        
        r, c = target
        # Record AI move
        self.ai_moves.append((r, c))
        
        # Perform attack
        hit = self.player_grid[r][c] is not None
        
        if hit:
            # Hit a ship
            ship_char = self.player_grid[r][c]
            self.player_btns[r][c].config(text="💥", bg=HIT_COLOR)
            self.ai_hits += 1
            self.ai_hunt_mode = False
            
            # Update AI targeting information
            self.ai_last_hit = (r, c)
            self.ai_hits_queue.append((r, c))
            
            # Try to determine ship orientation
            if len(self.ai_hits_queue) >= 2 and not self.ai_orientation:
                self.ai_orientation = self.find_orientation()
            
            # Check if the ship is sunk
            if self.is_ship_sunk(self.player_grid, r, c, ship_char):
                self.mark_sunken_ship(self.player_grid, self.player_btns, ship_char)
                ship_idx = next((i for i, name in enumerate(SHIP_NAMES) if name[0] == ship_char), -1)
                if ship_idx != -1:
                    ship_size = SHIP_SIZES[ship_idx]
                    if ship_size in self.remaining_player_ships:
                        self.remaining_player_ships.remove(ship_size)
                
                # Reset targeting information after sinking a ship
                self.ai_hits_queue.clear()
                self.ai_orientation = None
                self.ai_hunt_mode = True
        else:
            # Missed
            self.player_btns[r][c].config(text="•", bg=MISS_COLOR)
        
        # Disable the button to prevent further clicks
        self.player_btns[r][c].config(state="disabled")
        
        # Update game stats
        self.update_stats()
        
        # Check for game end
        if self.ai_hits == TOTAL_SHIP_PARTS:
            self.end_game(False)
            return
        
        # Update probability map for next turn
        self.update_probability_map()
        
        # Continue with player's turn
        self.status_label.config(text="Your turn!")
    
    def choose_ai_target(self):
        """Choose AI target based on difficulty"""
        mode = self.ai_mode.get()
        
        # Common function to get adjacent unattacked cells around a hit
        def get_adjacent_targets(r, c):
            adjacent = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and 
                    self.player_btns[nr][nc]['state'] != 'disabled'):
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
        if mode == "Easy":
            # Random shooting
            valid_targets = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                           if self.player_btns[r][c]['state'] != 'disabled']
            if valid_targets:
                return random.choice(valid_targets)
        
        elif mode == "Medium":
            # Simple probability-based targeting
            self.update_probability_map()
            return self.get_probability_target()
        
        elif mode == "Hard":
            # Enhanced probability-based targeting with pattern heuristics
            self.update_probability_map()
            
            # Add pattern bias (checkerboard is more efficient)
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r + c) % 2 == 0 and self.player_btns[r][c]['state'] != 'disabled':
                        self.ai_probability_map[r][c] *= 1.2
            
            return self.get_probability_target()
        
        else:  # Extremely Hard
            # Advanced targeting with memory of player's ship placements
            self.update_probability_map()
            
            # Add special strategies for extremely hard AI
            # 1. If first few moves, target the center area as ships are more likely there
            if len(self.ai_moves) < 5:
                center_targets = [(r, c) for r in range(3, 7) for c in range(3, 7)
                                if self.player_btns[r][c]['state'] != 'disabled']
                if center_targets:
                    return random.choice(center_targets)
            
            # 2. Analyze player's shooting pattern to predict ship placements
            if self.player_moves:
                player_hit_pattern = []
                for r, c in self.player_moves:
                    if self.ai_grid[r][c] is not None:
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
                                    self.player_btns[r][c]['state'] != 'disabled'):
                                    self.ai_probability_map[r][c] *= 1.1
            
            # 3. Heatmap-based probability enhancement
            max_heat = 0
            heatmap = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
            
            # Create a heatmap based on possible ship placements
            for size in self.remaining_player_ships:
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        # Horizontal placements
                        if c + size <= GRID_SIZE:
                            valid = True
                            for i in range(size):
                                if self.player_btns[r][c+i]['state'] == 'disabled' and self.player_grid[r][c+i] is None:
                                    valid = False
                                    break
                            if valid:
                                for i in range(size):
                                    if self.player_btns[r][c+i]['state'] != 'disabled':
                                        heatmap[r][c+i] += size  # Larger ships get higher weight
                                        max_heat = max(max_heat, heatmap[r][c+i])
                        
                        # Vertical placements
                        if r + size <= GRID_SIZE:
                            valid = True
                            for i in range(size):
                                if self.player_btns[r+i][c]['state'] == 'disabled' and self.player_grid[r+i][c] is None:
                                    valid = False
                                    break
                            if valid:
                                for i in range(size):
                                    if self.player_btns[r+i][c]['state'] != 'disabled':
                                        heatmap[r+i][c] += size  # Larger ships get higher weight
                                        max_heat = max(max_heat, heatmap[r+i][c])
            
            # Combine heatmap with probability map
            if max_heat > 0:
                for r in range(GRID_SIZE):
                    for c in range(GRID_SIZE):
                        if self.player_btns[r][c]['state'] != 'disabled':
                            # Normalize heat value and boost probability
                            heat_factor = 1 + (heatmap[r][c] / max_heat)
                            self.ai_probability_map[r][c] *= heat_factor
            
            # Get the highest probability target
            return self.get_probability_target()
        
        # Fallback to random targeting
        valid_targets = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) 
                       if self.player_btns[r][c]['state'] != 'disabled']
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
    
    def is_ship_sunk(self, grid, r, c, ship_char):
        """Check if a ship is completely sunk"""
        # Find all cells belonging to this ship
        ship_cells = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if grid[row][col] == ship_char:
                    ship_cells.append((row, col))
        
        # Check if player board, check if all ship cells are hit
        if grid == self.player_grid:
            return all(self.player_btns[row][col]['state'] == 'disabled' for row, col in ship_cells)
        
        # If AI board, check if all ship cells are revealed
        return all(self.ai_btns[row][col]['state'] == 'disabled' for row, col in ship_cells)
    
    def mark_sunken_ship(self, grid, btns, ship_char):
        """Mark a sunken ship with a different background"""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if grid[r][c] == ship_char:
                    btns[r][c].config(bg=SUNK_COLOR)
    
    def get_ship_name(self, ship_char):
        """Get the full ship name from its character"""
        for name in SHIP_NAMES:
            if name[0] == ship_char:
                return name
        return "Unknown"
    
    def update_stats(self):
        """Update the game statistics display"""
        self.stats_label.config(text=f"Your hits: {self.player_hits}/{TOTAL_SHIP_PARTS} | AI hits: {self.ai_hits}/{TOTAL_SHIP_PARTS}")
    
    def end_game(self, player_won):
        """End the game and show the result"""
        if player_won:
            messagebox.showinfo("Victory!", "Congratulations! You defeated the enemy fleet!")
        else:
            messagebox.showinfo("Defeat!", "Your fleet has been destroyed by the enemy!")
        
        # Reveal AI ships
        if not player_won:
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if self.ai_grid[r][c] and self.ai_btns[r][c]['state'] != 'disabled':
                        self.ai_btns[r][c].config(text="🚢", bg=SHIP_COLOR)
        
        # Disable all buttons
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.player_btns[r][c].config(state="disabled")
                self.ai_btns[r][c].config(state="disabled")
        
        self.status_label.config(text="Game Over - Press 'New Game' to play again")
    
    def reset_game(self):
        """Reset the game to start a new one"""
        # Reset game state
        self.player_grid = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_grid = [[None] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.player_hits = 0
        self.ai_hits = 0
        self.placing_ships = True
        self.current_ship_idx = 0
        
        # Reset AI state
        self.ai_targets.clear()
        self.ai_hits_queue.clear()
        self.ai_orientation = None
        self.ai_last_hit = None
        self.ai_probability_map = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ai_hunt_mode = True
        self.remaining_player_ships = SHIP_SIZES.copy()
        self.remaining_ai_ships = SHIP_SIZES.copy()
        self.player_moves = []
        self.ai_moves = []
        
        # Reset UI
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.player_btns[r][c].config(text="", bg=WATER_COLOR, state="normal")
                self.ai_btns[r][c].config(text="", bg=WATER_COLOR, state="disabled")
        
        # Enable orientation button
        self.orientation_btn.config(state="normal")
        
        # Reset status and stats
        self.status_label.config(text=f"Place your {SHIP_NAMES[0]} (size {SHIP_SIZES[0]})")
        self.update_stats()

# Run the game
if __name__ == "__main__":
    root = tk.Tk()
    game = BattleshipGame(root)
    root.mainloop()