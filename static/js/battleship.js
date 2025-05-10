// Constants
const GRID_SIZE = 10;
const SHIP_SIZES = [5, 4, 3, 3, 2];
const SHIP_NAMES = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"];

// Game state
let gameId = null;
let currentShipIndex = 0;
let shipOrientation = 'horizontal';
let placedShips = [];
let draggedShip = null;
let navyScore = 0;
let pirateScore = 0;
let airStrikeAvailable = true; // Air Strike power-up
let airStrikeMode = false; // Whether player is in air strike mode

// DOM Elements
const setupSection = document.getElementById('game-setup');
const gameplaySection = document.getElementById('game-play');
const setupBoard = document.getElementById('setup-board');
const playerBoard = document.getElementById('player-board');
const aiBoard = document.getElementById('ai-board');
const difficultySelect = document.getElementById('difficulty');
const rotateButton = document.getElementById('rotate-button');
const randomButton = document.getElementById('random-button');
const resetButton = document.getElementById('reset-button');
const startButton = document.getElementById('start-button');
const newGameButton = document.getElementById('new-game-button');
const airStrikeButton = document.getElementById('air-strike-button');
const turnIndicator = document.getElementById('turn-indicator');
const gameMessage = document.getElementById('game-message');
const gameOverModal = document.getElementById('game-over-modal');
const gameResultTitle = document.getElementById('game-result-title');
const gameResultMessage = document.getElementById('game-result-message');
const playerHitsDisplay = document.getElementById('player-hits');
const aiHitsDisplay = document.getElementById('ai-hits');
const playAgainButton = document.getElementById('play-again-button');
const navyScoreDisplay = document.getElementById('navy-score');
const pirateScoreDisplay = document.getElementById('pirate-score');

// Sound effects
const splashSound = document.getElementById('splash-sound');
const explosionSound = document.getElementById('explosion-sound');
const victorySound = document.getElementById('victory-sound');
const defeatSound = document.getElementById('defeat-sound');

// Initialize the game
function init() {
    createGrid(setupBoard);
    createGrid(playerBoard);
    createGrid(aiBoard);
    setupEventListeners();
    updateScoreboard();
}

// Create a grid of cells
function createGrid(gridElement) {
    gridElement.innerHTML = '';
    for (let row = 0; row < GRID_SIZE; row++) {
        for (let col = 0; col < GRID_SIZE; col++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.row = row;
            cell.dataset.col = col;
            gridElement.appendChild(cell);
        }
    }
}

// Setup event listeners for game controls
function setupEventListeners() {
    // Ship rotation
    rotateButton.addEventListener('click', () => {
        shipOrientation = shipOrientation === 'horizontal' ? 'vertical' : 'horizontal';
        rotateButton.textContent = `Orientation: ${shipOrientation === 'horizontal' ? 'Horizontal' : 'Vertical'}`;
        updateShipPreview();
    });
    
    // Random ship placement
    randomButton.addEventListener('click', randomPlacement);
    
    // Reset ship placement
    resetButton.addEventListener('click', resetPlacement);
    
    // Start game
    startButton.addEventListener('click', startGame);
    
    // New game
    newGameButton.addEventListener('click', () => {
        showSection(setupSection);
        resetPlacement();
    });
    
    // Play again after game over
    playAgainButton.addEventListener('click', () => {
        gameOverModal.classList.remove('active');
        showSection(setupSection);
        resetPlacement();
    });
    
    // Air Strike activation
    airStrikeButton.addEventListener('click', toggleAirStrike);
    
    // Setup drag and drop for ships
    setupDragAndDrop();
    
    // Setup click events for setup board
    setupBoard.addEventListener('click', handleSetupBoardClick);
    setupBoard.addEventListener('mouseover', handleSetupBoardHover);
    setupBoard.addEventListener('mouseout', removeShipPreview);
    
    // Setup events for AI board
    aiBoard.addEventListener('click', handleAIBoardClick);
    aiBoard.addEventListener('mouseover', handleAIBoardHover);
    aiBoard.addEventListener('mouseout', removeAirStrikeHighlight);
}

// Handle clicks on the setup board for ship placement
function handleSetupBoardClick(event) {
    if (!event.target.classList.contains('cell')) return;
    
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    
    placeShip(row, col);
}

// Handle hovering over the setup board to preview ship placement
function handleSetupBoardHover(event) {
    if (!event.target.classList.contains('cell')) return;
    
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    
    showShipPreview(row, col);
}

// Remove ship preview
function removeShipPreview() {
    const preview = document.querySelector('.ship-placement-preview');
    if (preview) preview.remove();
}

// Show a preview of where the ship will be placed
function showShipPreview(row, col) {
    removeShipPreview();
    
    // If all ships are placed, don't show preview
    if (currentShipIndex >= SHIP_SIZES.length) return;
    
    const shipSize = SHIP_SIZES[currentShipIndex];
    const cells = getShipCells(row, col, shipSize, shipOrientation);
    const valid = isValidPlacement(cells);
    
    const preview = document.createElement('div');
    preview.className = `ship-placement-preview ${shipOrientation}`;
    preview.style.position = 'absolute';
    
    if (shipOrientation === 'horizontal') {
        preview.style.top = `${event.target.offsetTop}px`;
        preview.style.left = `${event.target.offsetLeft}px`;
        preview.style.flexDirection = 'row';
    } else {
        preview.style.top = `${event.target.offsetTop}px`;
        preview.style.left = `${event.target.offsetLeft}px`;
        preview.style.flexDirection = 'column';
    }
    
    for (let i = 0; i < shipSize; i++) {
        const segment = document.createElement('div');
        segment.className = `preview-segment ${valid ? 'valid' : 'invalid'}`;
        preview.appendChild(segment);
    }
    
    setupBoard.appendChild(preview);
}

// Place a ship on the board
function placeShip(row, col) {
    if (currentShipIndex >= SHIP_SIZES.length) return;
    
    const shipSize = SHIP_SIZES[currentShipIndex];
    const shipName = SHIP_NAMES[currentShipIndex];
    const cells = getShipCells(row, col, shipSize, shipOrientation);
    
    if (!isValidPlacement(cells)) {
        gameMessage.textContent = 'Invalid placement! Ships cannot extend beyond the board or overlap.';
        gameMessage.style.color = 'var(--danger)';
        return;
    }
    
    // Record the ship placement
    placedShips.push({
        name: shipName,
        size: shipSize,
        row: row,
        col: col,
        direction: shipOrientation === 'horizontal' ? 'H' : 'V'
    });
    
    // Mark cells as occupied by ship
    for (const cell of cells) {
        const cellElement = getCellElement(setupBoard, cell.row, cell.col);
        cellElement.classList.add('ship');
        
        // Add styling for ship ends
        if (shipOrientation === 'horizontal') {
            if (cell.col === col) cellElement.classList.add('start', 'horizontal');
            if (cell.col === col + shipSize - 1) cellElement.classList.add('end', 'horizontal');
        } else {
            if (cell.row === row) cellElement.classList.add('start', 'vertical');
            if (cell.row === row + shipSize - 1) cellElement.classList.add('end', 'vertical');
        }
    }
    
    // Mark the ship as placed in the ship selection
    const shipItem = document.querySelector(`.ship-item[data-ship="${shipName.toLowerCase()}"]`);
    if (shipItem) {
        shipItem.classList.add('placed');
        shipItem.draggable = false;
    }
    
    // Move to next ship
    currentShipIndex++;
    
    // Enable start button if all ships are placed
    if (currentShipIndex >= SHIP_SIZES.length) {
        startButton.disabled = false;
        gameMessage.textContent = 'All ships placed! Click "Start Battle" to begin.';
        gameMessage.style.color = 'var(--success)';
    } else {
        gameMessage.textContent = `Place your ${SHIP_NAMES[currentShipIndex]} (size ${SHIP_SIZES[currentShipIndex]})`;
        gameMessage.style.color = 'var(--navy-primary)';
    }
}

// Get cell elements that a ship would occupy
function getShipCells(row, col, size, orientation) {
    const cells = [];
    
    if (orientation === 'horizontal') {
        for (let i = 0; i < size; i++) {
            cells.push({ row, col: col + i });
        }
    } else {
        for (let i = 0; i < size; i++) {
            cells.push({ row: row + i, col });
        }
    }
    
    return cells;
}

// Check if ship placement is valid
function isValidPlacement(cells) {
    for (const cell of cells) {
        // Check if cell is within grid bounds
        if (cell.row < 0 || cell.row >= GRID_SIZE || cell.col < 0 || cell.col >= GRID_SIZE) {
            return false;
        }
        
        // Check if cell is already occupied by another ship
        const cellElement = getCellElement(setupBoard, cell.row, cell.col);
        if (cellElement.classList.contains('ship')) {
            return false;
        }
    }
    
    return true;
}

// Get a cell element by row and column
function getCellElement(board, row, col) {
    return board.querySelector(`.cell[data-row="${row}"][data-col="${col}"]`);
}

// Reset ship placement
function resetPlacement() {
    placedShips = [];
    currentShipIndex = 0;
    
    // Reset board
    createGrid(setupBoard);
    
    // Reset ship selection
    document.querySelectorAll('.ship-item').forEach(ship => {
        ship.classList.remove('placed');
        ship.draggable = true;
    });
    
    // Reset message
    gameMessage.textContent = `Place your ${SHIP_NAMES[0]} (size ${SHIP_SIZES[0]})`;
    gameMessage.style.color = 'var(--navy-primary)';
    
    // Disable start button
    startButton.disabled = true;
}

// Random ship placement
function randomPlacement() {
    resetPlacement();
    
    for (let i = 0; i < SHIP_SIZES.length; i++) {
        let placed = false;
        
        while (!placed) {
            const row = Math.floor(Math.random() * GRID_SIZE);
            const col = Math.floor(Math.random() * GRID_SIZE);
            shipOrientation = Math.random() < 0.5 ? 'horizontal' : 'vertical';
            
            const shipSize = SHIP_SIZES[i];
            const cells = getShipCells(row, col, shipSize, shipOrientation);
            
            if (isValidPlacement(cells)) {
                // Place the ship
                placedShips.push({
                    name: SHIP_NAMES[i],
                    size: shipSize,
                    row: row,
                    col: col,
                    direction: shipOrientation === 'horizontal' ? 'H' : 'V'
                });
                
                // Mark cells as occupied by ship
                for (const cell of cells) {
                    const cellElement = getCellElement(setupBoard, cell.row, cell.col);
                    cellElement.classList.add('ship');
                    
                    // Add styling for ship ends
                    if (shipOrientation === 'horizontal') {
                        if (cell.col === col) cellElement.classList.add('start', 'horizontal');
                        if (cell.col === col + shipSize - 1) cellElement.classList.add('end', 'horizontal');
                    } else {
                        if (cell.row === row) cellElement.classList.add('start', 'vertical');
                        if (cell.row === row + shipSize - 1) cellElement.classList.add('end', 'vertical');
                    }
                }
                
                // Mark the ship as placed in the ship selection
                const shipItem = document.querySelector(`.ship-item[data-ship="${SHIP_NAMES[i].toLowerCase()}"]`);
                if (shipItem) {
                    shipItem.classList.add('placed');
                    shipItem.draggable = false;
                }
                
                placed = true;
            }
        }
    }
    
    // Update current ship index and enable start button
    currentShipIndex = SHIP_SIZES.length;
    startButton.disabled = false;
    gameMessage.textContent = 'Ships placed randomly! Click "Start Battle" to begin.';
    gameMessage.style.color = 'var(--success)';
}

// Setup drag and drop functionality for ships
function setupDragAndDrop() {
    const shipItems = document.querySelectorAll('.ship-item');
    
    shipItems.forEach(ship => {
        ship.addEventListener('dragstart', (e) => {
            if (ship.classList.contains('placed')) {
                e.preventDefault();
                return;
            }
            draggedShip = {
                name: ship.dataset.ship,
                size: parseInt(ship.dataset.size)
            };
            ship.classList.add('dragging');
        });
        
        ship.addEventListener('dragend', () => {
            ship.classList.remove('dragging');
            draggedShip = null;
        });
    });
    
    setupBoard.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    setupBoard.addEventListener('drop', (e) => {
        e.preventDefault();
        if (!draggedShip) return;
        
        const cell = e.target.closest('.cell');
        if (!cell) return;
        
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        
        // Find the index of the ship being placed
        const index = SHIP_NAMES.findIndex(name => name.toLowerCase() === draggedShip.name);
        if (index !== -1 && currentShipIndex !== index) {
            currentShipIndex = index;
        }
        
        placeShip(row, col);
    });
}

// Start a new game
function startGame() {
    if (placedShips.length !== SHIP_SIZES.length) {
        gameMessage.textContent = 'Place all ships before starting the game!';
        gameMessage.style.color = 'var(--danger)';
        return;
    }
    
    // Clear boards
    createGrid(playerBoard);
    createGrid(aiBoard);
    
    // Hide setup, show gameplay
    showSection(gameplaySection);
    
    // Start new game with selected difficulty
    const difficulty = difficultySelect.value;
    fetch('/new_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ difficulty })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            gameId = data.gameId;
            
            // Send ship placements
            return fetch('/place_ships', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ships: placedShips })
            });
        } else {
            throw new Error(data.message || 'Failed to start new game');
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateGameState(data.gameState);
            turnIndicator.textContent = 'Your Turn';
            turnIndicator.classList.remove('ai-turn');
            gameMessage.textContent = 'Game started! Click on the enemy board to fire.';
            gameMessage.style.color = 'var(--navy-primary)';
        } else {
            throw new Error(data.message || 'Failed to place ships');
        }
    })
    .catch(error => {
        console.error('Game error:', error);
        gameMessage.textContent = `Error: ${error.message}`;
        gameMessage.style.color = 'var(--danger)';
    });
}

// Handle clicks on the AI board during gameplay
function handleAIBoardClick(event) {
    if (!event.target.classList.contains('cell')) return;
    if (event.target.classList.contains('hit') || event.target.classList.contains('miss')) return;
    
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    
    // Make a shot
    fetch('/player_shoot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ row, col })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Process player shot
            const cell = getCellElement(aiBoard, data.row, data.col);
            
            if (data.hit) {
                cell.classList.add('hit');
                
                try {
                    explosionSound.play();
                } catch (error) {
                    console.log("Couldn't play explosion sound:", error);
                }
                
                if (data.shipSunk) {
                    gameMessage.textContent = `You sunk the enemy's ${data.shipName}!`;
                    gameMessage.style.color = 'var(--success)';
                    
                    // Mark all cells of the sunk ship
                    if (data.shipCells) {
                        data.shipCells.forEach(shipCell => {
                            const shipCellElement = getCellElement(aiBoard, shipCell.row, shipCell.col);
                            if (shipCellElement) {
                                shipCellElement.classList.add('sunk');
                            }
                        });
                    }
                    
                    // Update ship indicator
                    const shipIndicator = document.querySelector(`#ai-ships .mini-ship[data-ship="${data.shipName ? data.shipName.toLowerCase() : ''}"]`);
                    if (shipIndicator) {
                        shipIndicator.classList.add('sunk');
                    }
                } else {
                    gameMessage.textContent = 'Hit! Fire again!';
                    gameMessage.style.color = 'var(--success)';
                }
            } else {
                cell.classList.add('miss');
                
                try {
                    splashSound.play();
                } catch (error) {
                    console.log("Couldn't play splash sound:", error);
                }
                
                gameMessage.textContent = 'Miss! AI\'s turn.';
                gameMessage.style.color = 'var(--info)';
            }
            
            // Process AI shot if included
            if (data.aiShot && data.aiShot.status === 'success') {
                const aiShot = data.aiShot;
                const playerCell = getCellElement(playerBoard, aiShot.row, aiShot.col);
                
                setTimeout(() => {
                    if (aiShot.hit) {
                        if (playerCell) {
                            playerCell.classList.add('hit');
                        }
                        
                        try {
                            explosionSound.play();
                        } catch (error) {
                            console.log("Couldn't play explosion sound:", error);
                        }
                        
                        if (aiShot.shipSunk) {
                            gameMessage.textContent = `The enemy sunk your ${aiShot.shipName || "ship"}!`;
                            gameMessage.style.color = 'var(--danger)';
                            
                            // Mark all cells of the sunk ship
                            if (aiShot.shipCells) {
                                aiShot.shipCells.forEach(shipCell => {
                                    const shipCellElement = getCellElement(playerBoard, shipCell.row, shipCell.col);
                                    if (shipCellElement) {
                                        shipCellElement.classList.add('sunk');
                                    }
                                });
                            }
                            
                            // Update ship indicator
                            if (aiShot.shipName) {
                                const shipIndicator = document.querySelector(`#player-ships .mini-ship[data-ship="${aiShot.shipName.toLowerCase()}"]`);
                                if (shipIndicator) {
                                    shipIndicator.classList.add('sunk');
                                }
                            }
                        } else {
                            gameMessage.textContent = 'The enemy hit your ship!';
                            gameMessage.style.color = 'var(--danger)';
                        }
                    } else {
                        if (playerCell) {
                            playerCell.classList.add('miss');
                        }
                        
                        try {
                            splashSound.play();
                        } catch (error) {
                            console.log("Couldn't play splash sound:", error);
                        }
                        
                        gameMessage.textContent = 'The enemy missed! Your turn.';
                        gameMessage.style.color = 'var(--navy-primary)';
                    }
                    
                    // Update turn indicator
                    turnIndicator.textContent = 'Your Turn';
                    turnIndicator.classList.remove('ai-turn');
                }, 1000);
                
                // Set turn indicator to AI's turn temporarily
                turnIndicator.textContent = 'Enemy Turn';
                turnIndicator.classList.add('ai-turn');
            }
            
            // Update game state
            updateGameState(data.gameState);
            
            // Check for game over
            if (data.gameOver || (data.aiShot && data.aiShot.gameOver)) {
                handleGameOver(data.gameState.winner);
            }
        } else {
            gameMessage.textContent = data.message || 'Error processing shot';
            gameMessage.style.color = 'var(--danger)';
        }
    })
    .catch(error => {
        console.error('Shot error:', error);
        gameMessage.textContent = `Error: ${error.message}`;
        gameMessage.style.color = 'var(--danger)';
    });
}

// Update the game state on the frontend
function updateGameState(gameState) {
    if (!gameState) return;
    
    // Check for game over state first
    if (gameState.gameOver) {
        handleGameOver(gameState.winner);
        return;
    }
    
    // Update player board
    for (let row = 0; row < GRID_SIZE; row++) {
        for (let col = 0; col < GRID_SIZE; col++) {
            const cell = getCellElement(playerBoard, row, col);
            
            // Update ship cells
            if (gameState.playerGrid[row][col]) {
                cell.classList.add('ship');
                cell.classList.add('navy-ship');
            }
            
            // Update hit/miss markers
            if (gameState.aiShots[row][col] === true) {
                cell.classList.add('hit');
            } else if (gameState.aiShots[row][col] === false) {
                cell.classList.add('miss');
            }
        }
    }
    
    // Update AI board (hide ships but show hits/misses)
    for (let row = 0; row < GRID_SIZE; row++) {
        for (let col = 0; col < GRID_SIZE; col++) {
            const cell = getCellElement(aiBoard, row, col);
            
            if (gameState.playerShots[row][col] === true) {
                cell.classList.add('hit');
            } else if (gameState.playerShots[row][col] === false) {
                cell.classList.add('miss');
            }
        }
    }
    
    // Update hit counters
    playerHitsDisplay.textContent = gameState.playerHits;
    aiHitsDisplay.textContent = gameState.aiHits;
    
    // Update Air Strike availability
    airStrikeAvailable = gameState.airStrikeAvailable !== undefined ? gameState.airStrikeAvailable : true;
    updateAirStrikeButton();
}

// Handle game over
function handleGameOver(winner) {
    // Update scores
    if (winner === 'player') {
        navyScore++;
    } else {
        pirateScore++;
    }
    updateScoreboard();
    
    // Show game over modal
    setTimeout(() => {
        gameResultTitle.textContent = winner === 'player' ? 'Victory!' : 'Defeat!';
        gameResultMessage.textContent = winner === 'player' 
            ? 'Congratulations! You defeated the pirate fleet!' 
            : 'Your fleet has been destroyed by the pirates!';
        
        // Play sound effect
        try {
            if (winner === 'player') {
                victorySound.play();
            } else {
                defeatSound.play();
            }
        } catch (error) {
            console.log("Couldn't play game over sound:", error);
        }
        
        gameOverModal.classList.add('active');
    }, 1500);
}

// Update the scoreboard
function updateScoreboard() {
    navyScoreDisplay.textContent = navyScore;
    pirateScoreDisplay.textContent = pirateScore;
}

// Show a specific section and hide others
function showSection(section) {
    // Hide all sections
    setupSection.classList.remove('active');
    gameplaySection.classList.remove('active');
    
    // Show the requested section
    section.classList.add('active');
}

// Update ship preview when orientation changes
function updateShipPreview() {
    const previewElement = document.querySelector('.ship-placement-preview');
    if (previewElement) {
        previewElement.className = `ship-placement-preview ${shipOrientation}`;
        previewElement.style.flexDirection = shipOrientation === 'horizontal' ? 'row' : 'column';
    }
}

// Setup sound effects for the game
function setupSoundEffects() {
    // Create safe play method that won't cause infinite recursion
    function safePlay(sound) {
        if (sound && sound.originalPlay) {
            sound.originalPlay().catch(err => {
                console.log("Audio playback error:", err);
                // Fallback - do nothing, continue with the game
            });
        }
    }
    
    // Store original methods and replace with safe versions
    if (splashSound && !splashSound.originalPlay) {
        splashSound.originalPlay = splashSound.play;
        splashSound.play = function() { safePlay(this); };
    }
    
    if (explosionSound && !explosionSound.originalPlay) {
        explosionSound.originalPlay = explosionSound.play;
        explosionSound.play = function() { safePlay(this); };
    }
    
    if (victorySound && !victorySound.originalPlay) {
        victorySound.originalPlay = victorySound.play;
        victorySound.play = function() { safePlay(this); };
    }
    
    if (defeatSound && !defeatSound.originalPlay) {
        defeatSound.originalPlay = defeatSound.play;
        defeatSound.play = function() { safePlay(this); };
    }
}

// Toggle Air Strike mode
function toggleAirStrike() {
    if (!airStrikeAvailable) return;
    
    airStrikeMode = !airStrikeMode;
    updateAirStrikeButton();
    
    if (airStrikeMode) {
        gameMessage.textContent = 'Air Strike Mode: Select a row or column to attack';
        gameMessage.style.color = 'var(--pirate-primary)';
        aiBoard.classList.add('air-strike-mode');
    } else {
        gameMessage.textContent = 'Air Strike canceled. Click on a cell to fire a regular shot';
        gameMessage.style.color = 'var(--navy-primary)';
        aiBoard.classList.remove('air-strike-mode');
        removeAirStrikeHighlight();
    }
}

// Update Air Strike button appearance
function updateAirStrikeButton() {
    if (airStrikeAvailable) {
        airStrikeButton.classList.remove('disabled');
        airStrikeButton.disabled = false;
    } else {
        airStrikeButton.classList.add('disabled');
        airStrikeButton.disabled = true;
        airStrikeMode = false;
        aiBoard.classList.remove('air-strike-mode');
    }
}

// Handle AI board hover for Air Strike targeting
function handleAIBoardHover(event) {
    if (!airStrikeMode || !event.target.classList.contains('cell')) return;
    
    removeAirStrikeHighlight();
    
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    
    // Highlight the entire row or column based on which is the majority of the board
    const rowHighlight = row > GRID_SIZE / 2;
    
    if (rowHighlight) {
        // Highlight the row
        for (let c = 0; c < GRID_SIZE; c++) {
            const cell = getCellElement(aiBoard, row, c);
            if (!cell.classList.contains('hit') && !cell.classList.contains('miss')) {
                cell.classList.add('row-highlight');
            }
        }
    } else {
        // Highlight the column
        for (let r = 0; r < GRID_SIZE; r++) {
            const cell = getCellElement(aiBoard, r, col);
            if (!cell.classList.contains('hit') && !cell.classList.contains('miss')) {
                cell.classList.add('col-highlight');
            }
        }
    }
    
    // Store the air strike target
    event.target.dataset.airStrikeTarget = rowHighlight ? 'row' : 'column';
}

// Remove Air Strike highlighting
function removeAirStrikeHighlight() {
    aiBoard.querySelectorAll('.row-highlight, .col-highlight').forEach(cell => {
        cell.classList.remove('row-highlight', 'col-highlight');
        delete cell.dataset.airStrikeTarget;
    });
}

// Execute Air Strike
function executeAirStrike(row, col, targetType) {
    if (!airStrikeAvailable) return;
    
    // Determine target index (row or column number)
    const targetIndex = targetType === 'row' ? row : col;
    
    // Send Air Strike to server
    fetch('/player_air_strike', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            gameId: gameId,
            targetType: targetType,
            targetIndex: targetIndex
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateGameState(data.gameState);
            gameMessage.textContent = data.message || 'Air Strike successful!';
            gameMessage.style.color = 'var(--success)';
            
            // Air strike used - update UI
            airStrikeAvailable = false;
            airStrikeMode = false;
            updateAirStrikeButton();
            aiBoard.classList.remove('air-strike-mode');
            
            // If game is over, show game over screen
            if (data.gameState.gameOver) {
                handleGameOver(data.gameState.winner);
            }
            // If game is not over, AI will take its turn
            else {
                setTimeout(() => {
                    turnIndicator.textContent = 'AI Turn';
                    turnIndicator.classList.add('ai-turn');
                    gameMessage.textContent = 'AI is making a move...';
                    gameMessage.style.color = 'var(--pirate-primary)';
                    
                    // Fetch AI move
                    fetch('/get_game_state', {
                        method: "GET",
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            updateGameState(data.gameState);
                            turnIndicator.textContent = 'Your Turn';
                            turnIndicator.classList.remove('ai-turn');
                            gameMessage.textContent = 'Your turn to fire!';
                            gameMessage.style.color = 'var(--navy-primary)';
                        }
                    });
                }, 1500);
            }
        } else {
            gameMessage.textContent = data.message || 'Error executing Air Strike';
            gameMessage.style.color = 'var(--danger)';
        }
    })
    .catch(error => {
        console.error('Air Strike error:', error);
        gameMessage.textContent = `Error: ${error.message}`;
        gameMessage.style.color = 'var(--danger)';
    });
}

// Modify handleAIBoardClick to support Air Strike
const originalHandleAIBoardClick = handleAIBoardClick;

// Override handleAIBoardClick
handleAIBoardClick = function(event) {
    if (!event.target.classList.contains('cell')) return;
    
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    
    // Check if Air Strike mode is active
    if (airStrikeMode) {
        const targetType = event.target.dataset.airStrikeTarget || (row > GRID_SIZE / 2 ? 'row' : 'column');
        executeAirStrike(row, col, targetType);
        return;
    }
    
    // Otherwise, execute normal shot
    if (event.target.classList.contains('hit') || event.target.classList.contains('miss')) return;
    
    turnIndicator.textContent = 'Processing...';
    
    // Send player shot to server
    fetch('/player_shoot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            gameId: gameId,
            row: row,
            col: col
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Play sound effect
            try {
                if (data.hit) {
                    explosionSound.play();
                } else {
                    splashSound.play();
                }
            } catch (error) {
                console.log("Couldn't play sound:", error);
            }
            
            // Update the board
            updateGameState(data.gameState);
            
            // If game is over, show game over screen
            if (data.gameState.gameOver) {
                handleGameOver(data.gameState.winner);
            }
            // If game is not over, AI will take its turn
            else {
                setTimeout(() => {
                    turnIndicator.textContent = 'AI Turn';
                    turnIndicator.classList.add('ai-turn');
                    gameMessage.textContent = 'AI is making a move...';
                    gameMessage.style.color = 'var(--pirate-primary)';
                    
                    // Fetch AI move
                    fetch('/get_game_state', {
                        method: "GET",
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            updateGameState(data.gameState);
                            turnIndicator.textContent = 'Your Turn';
                            turnIndicator.classList.remove('ai-turn');
                            gameMessage.textContent = 'Your turn to fire!';
                            gameMessage.style.color = 'var(--navy-primary)';
                        }
                    });
                }, 1500);
            }
        } else {
            gameMessage.textContent = data.message || 'Error firing shot';
            gameMessage.style.color = 'var(--danger)';
        }
    })
    .catch(error => {
        console.error('Shot error:', error);
        gameMessage.textContent = `Error: ${error.message}`;
        gameMessage.style.color = 'var(--danger)';
    });
};

// Initialize the game when the page loads
window.addEventListener('load', () => {
    init();
    setupSoundEffects();
    showSection(setupSection);
    gameMessage.textContent = `Place your ${SHIP_NAMES[0]} (size ${SHIP_SIZES[0]})`;
});