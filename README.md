# Battleship: Navy vs Pirates

A sophisticated web-based Battleship game with advanced AI opponents, multiple difficulty levels, and special attack features.

## Overview

This Battleship game pits the player (Navy) against an AI opponent (Pirates) in a classic naval warfare game. The project features an advanced AI with four difficulty levels, including an extremely challenging mode that uses sophisticated targeting algorithms.

## Features

- **Multiple Difficulty Levels**:

  - **Easy**: Basic targeting with occasional random shots
  - **Medium**: Improved probability-based targeting
  - **Hard**: Advanced targeting with optimized probability maps
  - **Extremely Hard**: Ultimate AI with corner targeting, center-zone analysis, and player pattern recognition

- **Advanced AI Algorithms**:

  - Probability density maps for intelligent targeting
  - Pattern recognition to identify player ship placements
  - Hunt and target mode to focus on partially damaged ships
  - Adaptive learning from player's tactics

- **Special Power-up: Air Strike**:

  - One-time ability to attack an entire row or column
  - Strategic timing can turn the tide of battle
  - Visual highlighting of targeting area

- **Themed Interface**:

  - Ocean-themed background with wave animations
  - Navy vs Pirates visual styling
  - Responsive design for various screen sizes

- **Audio Effects**:

  - Sound effects for hits, misses, victory, and defeat
  - Enhances player immersion

- **Game Statistics**:
  - Track hits, misses, and success rates
  - Win/loss counter to track your performance

## How to Play

1. **Setup Phase**:

   - Use the "Random Placement" button for quick setup, or
   - Manually place your ships on the grid
   - Click "Rotate Ship" to change orientation
   - Click "Start Battle" when your fleet is positioned

2. **Battle Phase**:

   - Click on the enemy grid to fire at that position
   - Blue splash indicates a miss, red explosion indicates a hit
   - Sink all enemy ships to win
   - Use your Air Strike strategically for maximum impact

3. **Air Strike Power-up**:
   - Click the "Air Strike" button to activate
   - Select a row or column to attack entirely
   - This can only be used once per game

## Technical Details

### Frontend

- Built with vanilla JavaScript, HTML5, and CSS3
- Responsive grid system with visual effects
- Interactive UI with real-time feedback

### Backend

- Flask web server handling game logic
- Session management for game state
- RESTful API endpoints for game actions

### AI Implementation

- NumPy for probability calculations
- Advanced pattern recognition algorithms
- Difficulty-based targeting strategies
- Adaptive behavior based on game progress

## Running the Game

1. Make sure you have Python installed
2. Install required dependencies:
   ```
   pip install flask numpy
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Navigate to `http://localhost:5000` in your web browser
