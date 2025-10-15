#!/usr/bin/env python3
"""
Ultra Tetris HDR 1.0 - Exact Game Boy Tetris Recreation
Complete with main menu, statistics, all levels to kill screen,
and authentic Game Boy timing and mechanics.
"""

import pygame
import numpy as np
import random
import time
import json
import os

# ---------------------------------------------------------------------
# GAME CONFIG - Authentic Game Boy Settings
# ---------------------------------------------------------------------

# --- Core Tetris Grid (Game Boy exact) ---
BLOCK = 24
COLS, ROWS = 10, 20
GRID_WIDTH, GRID_HEIGHT = COLS * BLOCK, ROWS * BLOCK

# --- UI Panel ---
SIDE_WIDTH = 200
WIDTH, HEIGHT = GRID_WIDTH + SIDE_WIDTH, GRID_HEIGHT

# --- Game Boy Timing (60 FPS with frame-perfect drops) ---
FPS = 60
# Original NES/GB gravity table (frames between drops at 60fps)
SPEED_TABLE = {
    0:48, 1:43, 2:38, 3:33, 4:28, 5:23, 6:18, 7:13, 8:8, 9:6,
    10:5, 11:5, 12:5, 13:4, 14:4, 15:4, 16:3, 17:3, 18:3, 19:2,
    20:2, 21:2, 22:2, 23:2, 24:2, 25:2, 26:2, 27:2, 28:2, 29:1
}

# --- Entry Delay (frames before piece can be moved after spawn) ---
ENTRY_DELAY = 10  # Game Boy specific

# --- DAS (Delayed Auto Shift) Settings ---
DAS_DELAY = 16  # Initial delay before auto-repeat (frames)
DAS_RATE = 6    # Auto-repeat rate (frames between moves)

# --- Game Boy Color Palette ---
GB_DARK   = (15, 56, 15)
GB_MID    = (48, 98, 48)
GB_LIGHT  = (139, 172, 15)
GB_WHITE  = (155, 188, 15)
GB_BLACK  = (0, 0, 0)

# Piece colors for statistics display
PIECE_COLORS = {
    0: (0, 240, 240),   # I - Cyan
    1: (160, 0, 240),   # T - Purple
    2: (0, 240, 0),     # S - Green
    3: (240, 0, 0),     # Z - Red
    4: (240, 240, 0),   # O - Yellow
    5: (240, 160, 0),   # L - Orange
    6: (0, 0, 240)      # J - Blue
}

# --- Tetromino Shapes (Game Boy rotation system) ---
SHAPES = [
    np.array([[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]]),  # I
    np.array([[0,1,0],[1,1,1],[0,0,0]]),                   # T
    np.array([[0,1,1],[1,1,0],[0,0,0]]),                   # S
    np.array([[1,1,0],[0,1,1],[0,0,0]]),                   # Z
    np.array([[1,1],[1,1]]),                                # O
    np.array([[0,0,1],[1,1,1],[0,0,0]]),                   # L
    np.array([[1,0,0],[1,1,1],[0,0,0]])                    # J
]

# --- Game Modes ---
GAME_MODES = {
    'A_TYPE': 0,
    'B_TYPE': 1
}

# ---------------------------------------------------------------------
# AUDIO - Authentic Game Boy Korobeiniki
# ---------------------------------------------------------------------
def init_audio():
    """Initialize pygame mixer for audio playback."""
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        return True
    except:
        return False

def generate_korobeiniki():
    """Generate authentic Game Boy Korobeiniki (Type-A music)."""
    try:
        sample_rate = 22050
        # Game Boy tempo: ~144 BPM for authentic speed
        bpm = 144
        beat_duration = 60 / bpm
        
        # Note frequencies (Game Boy sound chip frequencies)
        notes = {
            'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00,
            'B3': 246.94, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63,
            'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
            'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
            'REST': 0
        }
        
        # Full Korobeiniki melody (Type-A theme)
        melody_notes = [
            ('E5', 0.5), ('B4', 0.25), ('C5', 0.25), ('D5', 0.5), ('C5', 0.25), ('B4', 0.25),
            ('A4', 0.5), ('A4', 0.25), ('C5', 0.25), ('E5', 0.5), ('D5', 0.25), ('C5', 0.25),
            ('B4', 0.75), ('C5', 0.25), ('D5', 0.5), ('E5', 0.5),
            ('C5', 0.5), ('A4', 0.5), ('A4', 0.5), ('REST', 0.5),
            
            ('REST', 0.25), ('D5', 0.375), ('F5', 0.25), ('A5', 0.5), ('G5', 0.25), ('F5', 0.25),
            ('E5', 0.75), ('C5', 0.25), ('E5', 0.5), ('D5', 0.25), ('C5', 0.25),
            ('B4', 0.5), ('B4', 0.25), ('C5', 0.25), ('D5', 0.5), ('E5', 0.5),
            ('C5', 0.5), ('A4', 0.5), ('A4', 0.5), ('REST', 0.5)
        ]
        
        # Bass line for fuller sound
        bass_notes = [
            ('E3', 1), ('E3', 1), ('A3', 1), ('A3', 1),
            ('G3', 1), ('G3', 1), ('C4', 0.5), ('G3', 0.5), ('C4', 1),
            ('D4', 1), ('D4', 1), ('A3', 1), ('F3', 1),
            ('C4', 1), ('C4', 1), ('C4', 0.5), ('G3', 0.5), ('C4', 1)
        ]
        
        # Generate melody waveform
        melody_wave = np.array([], dtype=np.float32)
        for note, duration in melody_notes:
            freq = notes.get(note, 0)
            num_samples = int(sample_rate * beat_duration * duration)
            t = np.linspace(0, duration * beat_duration, num_samples, endpoint=False)
            
            if freq > 0:
                # 12.5% duty cycle pulse wave (Game Boy sound)
                wave = np.where(np.sin(2 * np.pi * freq * t) % (2 * np.pi) < np.pi / 4, 1, -1)
                # Add slight envelope
                envelope = np.exp(-t * 0.5)
                wave = wave * envelope * 0.3
            else:
                wave = np.zeros(num_samples)
            
            melody_wave = np.append(melody_wave, wave)
        
        # Generate bass waveform
        bass_wave = np.array([], dtype=np.float32)
        bass_pos = 0
        for i in range(len(melody_wave)):
            if bass_pos >= len(bass_notes):
                bass_pos = 0
            
            note, duration = bass_notes[bass_pos]
            freq = notes.get(note, 0)
            
            if freq > 0:
                t = i / sample_rate
                # Triangle wave for bass (Game Boy wave channel)
                bass_sample = (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * freq * t)) * 0.15
            else:
                bass_sample = 0
            
            bass_wave = np.append(bass_wave, bass_sample)
            
            if i % int(sample_rate * beat_duration * duration) == 0 and i > 0:
                bass_pos += 1
        
        # Ensure bass and melody are same length
        min_len = min(len(melody_wave), len(bass_wave))
        melody_wave = melody_wave[:min_len]
        bass_wave = bass_wave[:min_len]
        
        # Combine melody and bass
        combined = melody_wave + bass_wave
        
        # Normalize and convert to int16
        combined = np.clip(combined, -1, 1)
        combined = (combined * 32767 * 0.5).astype(np.int16)
        
        # Create stereo sound
        stereo = np.zeros((len(combined), 2), dtype=np.int16)
        stereo[:, 0] = combined
        stereo[:, 1] = combined
        
        return pygame.sndarray.make_sound(stereo)
    except Exception as e:
        print(f"Could not generate audio: {e}")
        return None

def generate_sound_effects():
    """Generate Game Boy-style sound effects."""
    effects = {}
    sample_rate = 22050
    
    # Line clear sound
    duration = 0.2
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq_sweep = np.linspace(800, 1200, len(t))
    wave = np.sin(2 * np.pi * freq_sweep * t) * np.exp(-t * 3)
    wave = (wave * 32767 * 0.4).astype(np.int16)
    stereo = np.column_stack((wave, wave))
    effects['clear'] = pygame.sndarray.make_sound(stereo)
    
    # Tetris (4-line clear) sound
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq_sweep = np.linspace(400, 1600, len(t))
    wave = np.sin(2 * np.pi * freq_sweep * t) * np.exp(-t * 2)
    wave = (wave * 32767 * 0.5).astype(np.int16)
    stereo = np.column_stack((wave, wave))
    effects['tetris'] = pygame.sndarray.make_sound(stereo)
    
    # Drop sound
    duration = 0.05
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * 200 * t) * np.exp(-t * 20)
    wave = (wave * 32767 * 0.3).astype(np.int16)
    stereo = np.column_stack((wave, wave))
    effects['drop'] = pygame.sndarray.make_sound(stereo)
    
    # Rotate sound
    duration = 0.03
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * 600 * t)
    wave = (wave * 32767 * 0.2).astype(np.int16)
    stereo = np.column_stack((wave, wave))
    effects['rotate'] = pygame.sndarray.make_sound(stereo)
    
    # Game over sound
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    freq_sweep = np.linspace(400, 100, len(t))
    wave = np.sin(2 * np.pi * freq_sweep * t) * np.exp(-t * 0.5)
    wave = (wave * 32767 * 0.4).astype(np.int16)
    stereo = np.column_stack((wave, wave))
    effects['gameover'] = pygame.sndarray.make_sound(stereo)
    
    return effects

# ---------------------------------------------------------------------
# GAME STATE & HIGH SCORES
# ---------------------------------------------------------------------
class GameState:
    """Manages overall game state and persistence."""
    def __init__(self):
        self.high_scores = {'A_TYPE': [0] * 10, 'B_TYPE': [0] * 10}
        self.load_high_scores()
    
    def load_high_scores(self):
        """Load high scores from file."""
        try:
            if os.path.exists('ultra_tetris_scores.json'):
                with open('ultra_tetris_scores.json', 'r') as f:
                    self.high_scores = json.load(f)
        except:
            pass
    
    def save_high_scores(self):
        """Save high scores to file."""
        try:
            with open('ultra_tetris_scores.json', 'w') as f:
                json.dump(self.high_scores, f)
        except:
            pass
    
    def add_score(self, score, mode='A_TYPE'):
        """Add a score to high scores if it qualifies."""
        scores = self.high_scores[mode]
        scores.append(score)
        scores.sort(reverse=True)
        self.high_scores[mode] = scores[:10]
        self.save_high_scores()

# ---------------------------------------------------------------------
# TETRIS PIECE CLASS
# ---------------------------------------------------------------------
class Piece:
    """Represents a Tetromino with Game Boy rotation."""
    def __init__(self, shape_id):
        self.shape_id = shape_id
        self.shape = SHAPES[shape_id].copy()
        self.x = COLS // 2 - self.shape.shape[1] // 2
        self.y = 0
        self.entry_timer = ENTRY_DELAY
        
    def get_rotated(self):
        """Get rotated shape (Game Boy rotation rules)."""
        if self.shape_id == 4:  # O piece doesn't rotate
            return self.shape
        return np.rot90(self.shape, -1)  # Clockwise rotation

# ---------------------------------------------------------------------
# CORE GAME LOGIC
# ---------------------------------------------------------------------
def check_collision(board, shape, offset_x, offset_y):
    """Check if piece collides with board or boundaries."""
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                new_x = offset_x + x
                new_y = offset_y + y
                if new_x < 0 or new_x >= COLS or new_y >= ROWS:
                    return True
                if new_y >= 0 and board[new_y][new_x]:
                    return True
    return False

def merge_piece(board, piece):
    """Lock piece into the board."""
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                board_y = piece.y + y
                board_x = piece.x + x
                if board_y >= 0:
                    board[board_y][board_x] = piece.shape_id + 1

def clear_rows(board):
    """Clear completed rows with Game Boy mechanics."""
    rows_to_clear = []
    for y in range(ROWS):
        if all(board[y]):
            rows_to_clear.append(y)
    
    # Animate line clear (Game Boy style)
    if rows_to_clear:
        # Flash the lines briefly
        for row in rows_to_clear:
            for x in range(COLS):
                board[row][x] = -1  # Mark for animation
    
    # Remove cleared lines
    for row in rows_to_clear:
        del board[row]
        board.insert(0, [0] * COLS)
    
    return len(rows_to_clear)

def get_level_speed(level):
    """Get drop speed for current level."""
    if level > 29:
        return 1  # Kill screen speed
    return SPEED_TABLE.get(level, 48)

def calculate_score(lines, level):
    """Calculate score using original Nintendo scoring."""
    base_points = {0: 0, 1: 40, 2: 100, 3: 300, 4: 1200}
    return base_points.get(lines, 0) * (level + 1)

# ---------------------------------------------------------------------
# DRAWING FUNCTIONS
# ---------------------------------------------------------------------
def draw_background(screen):
    """Draw Game Boy-style background."""
    screen.fill(GB_LIGHT)
    # Add subtle pattern
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(screen, GB_MID, (0, y), (WIDTH, y))

def draw_grid(screen):
    """Draw the Tetris playfield grid."""
    # Draw border
    pygame.draw.rect(screen, GB_DARK, (0, 0, GRID_WIDTH, GRID_HEIGHT), 2)
    
    # Draw grid lines (subtle)
    for x in range(BLOCK, GRID_WIDTH, BLOCK):
        pygame.draw.line(screen, GB_MID, (x, 0), (x, GRID_HEIGHT))
    for y in range(BLOCK, GRID_HEIGHT, BLOCK):
        pygame.draw.line(screen, GB_MID, (0, y), (GRID_WIDTH, y))

def draw_board(screen, board):
    """Draw the locked pieces on the board."""
    for y in range(ROWS):
        for x in range(COLS):
            if board[y][x] > 0:
                px, py = x * BLOCK, y * BLOCK
                
                # Flash effect for clearing lines
                if board[y][x] == -1:
                    color = GB_WHITE
                else:
                    color = GB_DARK
                
                # Draw block with Game Boy style
                pygame.draw.rect(screen, color, (px, py, BLOCK, BLOCK))
                pygame.draw.rect(screen, GB_WHITE, (px + 2, py + 2, BLOCK - 4, BLOCK - 4))
                pygame.draw.rect(screen, color, (px + 4, py + 4, BLOCK - 8, BLOCK - 8))

def draw_piece(screen, piece, ghost_y=None):
    """Draw the active piece and optional ghost."""
    # Draw ghost piece
    if ghost_y is not None:
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    px = (piece.x + x) * BLOCK
                    py = (ghost_y + y) * BLOCK
                    pygame.draw.rect(screen, GB_MID, (px + 8, py + 8, BLOCK - 16, BLOCK - 16))
    
    # Draw actual piece
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                px = (piece.x + x) * BLOCK
                py = (piece.y + y) * BLOCK
                pygame.draw.rect(screen, GB_DARK, (px, py, BLOCK, BLOCK))
                pygame.draw.rect(screen, GB_WHITE, (px + 2, py + 2, BLOCK - 4, BLOCK - 4))
                pygame.draw.rect(screen, GB_DARK, (px + 4, py + 4, BLOCK - 8, BLOCK - 8))

def draw_ui(screen, font, score, lines, level, next_piece, statistics):
    """Draw the complete UI panel with statistics."""
    # Background for UI
    pygame.draw.rect(screen, GB_DARK, (GRID_WIDTH, 0, SIDE_WIDTH, HEIGHT))
    
    # Title
    title_font = pygame.font.Font(None, 20)
    title = title_font.render("ULTRA TETRIS", True, GB_WHITE)
    screen.blit(title, (GRID_WIDTH + 50, 10))
    title2 = title_font.render("HDR 1.0", True, GB_WHITE)
    screen.blit(title2, (GRID_WIDTH + 70, 30))
    
    # Score
    score_label = font.render("SCORE", True, GB_LIGHT)
    screen.blit(score_label, (GRID_WIDTH + 10, 60))
    score_text = font.render(f"{score:06d}", True, GB_WHITE)
    screen.blit(score_text, (GRID_WIDTH + 10, 80))
    
    # Lines
    lines_label = font.render("LINES", True, GB_LIGHT)
    screen.blit(lines_label, (GRID_WIDTH + 10, 110))
    lines_text = font.render(f"{lines:03d}", True, GB_WHITE)
    screen.blit(lines_text, (GRID_WIDTH + 10, 130))
    
    # Level
    level_label = font.render("LEVEL", True, GB_LIGHT)
    screen.blit(level_label, (GRID_WIDTH + 10, 160))
    level_text = font.render(f"{level:02d}", True, GB_WHITE)
    screen.blit(level_text, (GRID_WIDTH + 10, 180))
    
    # Next piece
    next_label = font.render("NEXT", True, GB_LIGHT)
    screen.blit(next_label, (GRID_WIDTH + 10, 220))
    
    next_box_x = GRID_WIDTH + 10
    next_box_y = 240
    pygame.draw.rect(screen, GB_LIGHT, (next_box_x, next_box_y, 80, 60), 1)
    
    # Draw next piece centered in box
    shape = next_piece.shape
    offset_x = next_box_x + (80 - shape.shape[1] * 16) // 2
    offset_y = next_box_y + (60 - shape.shape[0] * 16) // 2
    
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                px = offset_x + x * 16
                py = offset_y + y * 16
                pygame.draw.rect(screen, GB_DARK, (px, py, 16, 16))
                pygame.draw.rect(screen, GB_WHITE, (px + 1, py + 1, 14, 14))
                pygame.draw.rect(screen, GB_DARK, (px + 2, py + 2, 12, 12))
    
    # Statistics
    stats_label = font.render("STATISTICS", True, GB_LIGHT)
    screen.blit(stats_label, (GRID_WIDTH + 10, 320))
    
    stat_y = 340
    small_font = pygame.font.Font(None, 16)
    piece_names = ['I', 'T', 'S', 'Z', 'O', 'L', 'J']
    for i, count in enumerate(statistics):
        # Draw mini piece
        shape = SHAPES[i]
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    px = GRID_WIDTH + 15 + x * 6
                    py = stat_y + y * 6
                    pygame.draw.rect(screen, GB_DARK, (px, py, 6, 6))
        
        # Draw count
        count_text = small_font.render(f"{count:03d}", True, GB_WHITE)
        screen.blit(count_text, (GRID_WIDTH + 50, stat_y))
        stat_y += 20

def draw_main_menu(screen, font):
    """Draw the main menu screen."""
    screen.fill(GB_LIGHT)
    
    # Draw decorative border
    pygame.draw.rect(screen, GB_DARK, (20, 20, WIDTH - 40, HEIGHT - 40), 3)
    
    # Title
    title_font = pygame.font.Font(None, 48)
    title1 = title_font.render("ULTRA TETRIS", True, GB_DARK)
    title_rect1 = title1.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(title1, title_rect1)
    
    title2 = title_font.render("HDR 1.0", True, GB_DARK)
    title_rect2 = title2.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 50))
    screen.blit(title2, title_rect2)
    
    # Game Boy style decoration
    subtitle = font.render("Game Boy Edition", True, GB_MID)
    subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(subtitle, subtitle_rect)
    
    # Instructions
    instruction_font = pygame.font.Font(None, 24)
    
    # Blinking "Press Q to Start"
    if int(time.time() * 2) % 2:
        start_text = instruction_font.render("Press Q to Start", True, GB_DARK)
        start_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        screen.blit(start_text, start_rect)
    
    # Controls
    controls = [
        "← → : Move",
        "↑ : Rotate",
        "↓ : Soft Drop",
        "Space : Hard Drop",
        "P : Pause"
    ]
    
    y_pos = HEIGHT // 2 + 100
    control_font = pygame.font.Font(None, 18)
    for control in controls:
        text = control_font.render(control, True, GB_MID)
        text_rect = text.get_rect(center=(WIDTH // 2, y_pos))
        screen.blit(text, text_rect)
        y_pos += 20

def draw_game_over(screen, font, score, high_scores):
    """Draw game over screen with high scores."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((15, 56, 15, 200))
    screen.blit(overlay, (0, 0))
    
    # Game Over text
    title_font = pygame.font.Font(None, 36)
    game_over_text = title_font.render("GAME OVER", True, GB_WHITE)
    text_rect = game_over_text.get_rect(center=(WIDTH // 2, 80))
    screen.blit(game_over_text, text_rect)
    
    # Final score
    score_text = font.render(f"Final Score: {score:06d}", True, GB_WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, 130))
    screen.blit(score_text, score_rect)
    
    # High scores
    high_label = font.render("HIGH SCORES", True, GB_LIGHT)
    high_rect = high_label.get_rect(center=(WIDTH // 2, 180))
    screen.blit(high_label, high_rect)
    
    small_font = pygame.font.Font(None, 18)
    y_pos = 210
    for i, hs in enumerate(high_scores[:5]):
        if hs > 0:
            hs_text = small_font.render(f"{i+1}. {hs:06d}", True, GB_WHITE)
            hs_rect = hs_text.get_rect(center=(WIDTH // 2, y_pos))
            screen.blit(hs_text, hs_rect)
            y_pos += 20
    
    # Instructions
    restart_text = font.render("Press R to Restart", True, GB_WHITE)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, 350))
    screen.blit(restart_text, restart_rect)
    
    menu_text = font.render("Press Q for Main Menu", True, GB_WHITE)
    menu_rect = menu_text.get_rect(center=(WIDTH // 2, 380))
    screen.blit(menu_text, menu_rect)

def draw_pause(screen, font):
    """Draw pause screen."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((15, 56, 15, 150))
    screen.blit(overlay, (0, 0))
    
    pause_text = font.render("PAUSED", True, GB_WHITE)
    text_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(pause_text, text_rect)
    
    continue_text = pygame.font.Font(None, 18).render("Press P to Continue", True, GB_WHITE)
    cont_rect = continue_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
    screen.blit(continue_text, cont_rect)

# ---------------------------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------------------------
def run_game(screen, clock, game_state, starting_level=0):
    """Run the main Tetris game."""
    font = pygame.font.Font(None, 24)
    
    # Initialize sound
    music = generate_korobeiniki()
    sound_effects = generate_sound_effects()
    if music:
        music.play(-1)
    
    # Game variables
    board = [[0] * COLS for _ in range(ROWS)]
    current_piece = Piece(random.randint(0, 6))
    next_piece = Piece(random.randint(0, 6))
    
    score = 0
    lines = 0
    level = starting_level
    statistics = [0] * 7  # Piece statistics
    
    # Timing variables
    drop_timer = 0
    lock_delay = 0
    max_lock_delay = 30  # Half second at 60 FPS
    
    # DAS variables
    das_left = 0
    das_right = 0
    
    # Game state
    running = True
    game_over = False
    paused = False
    
    # Animation timers
    line_clear_timer = 0
    line_clear_delay = 20  # Frames to show cleared lines
    
    while running:
        dt = clock.tick(FPS)
        
        # Handle events
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                    if paused:
                        pygame.mixer.pause()
                    else:
                        pygame.mixer.unpause()
                
                if game_over:
                    if event.key == pygame.K_r:
                        return 'restart'
                    elif event.key == pygame.K_q:
                        return 'menu'
                
                if not game_over and not paused:
                    # Rotation
                    if event.key == pygame.K_UP:
                        rotated = current_piece.get_rotated()
                        if not check_collision(board, rotated, current_piece.x, current_piece.y):
                            current_piece.shape = rotated
                            if sound_effects:
                                sound_effects['rotate'].play()
                            lock_delay = 0  # Reset lock delay on successful rotation
                        # Wall kicks (Game Boy style)
                        elif not check_collision(board, rotated, current_piece.x - 1, current_piece.y):
                            current_piece.shape = rotated
                            current_piece.x -= 1
                            if sound_effects:
                                sound_effects['rotate'].play()
                            lock_delay = 0
                        elif not check_collision(board, rotated, current_piece.x + 1, current_piece.y):
                            current_piece.shape = rotated
                            current_piece.x += 1
                            if sound_effects:
                                sound_effects['rotate'].play()
                            lock_delay = 0
                    
                    # Hard drop
                    if event.key == pygame.K_SPACE:
                        drop_distance = 0
                        while not check_collision(board, current_piece.shape, current_piece.x, current_piece.y + 1):
                            current_piece.y += 1
                            drop_distance += 1
                        score += drop_distance * 2  # Hard drop scoring
                        lock_delay = max_lock_delay  # Force immediate lock
                        if sound_effects:
                            sound_effects['drop'].play()
        
        if not game_over and not paused:
            # Handle entry delay
            if current_piece.entry_timer > 0:
                current_piece.entry_timer -= 1
                continue
            
            # Handle line clear animation
            if line_clear_timer > 0:
                line_clear_timer -= 1
                if line_clear_timer == 0:
                    # Clear the marked lines
                    for y in range(ROWS):
                        for x in range(COLS):
                            if board[y][x] == -1:
                                board[y][x] = 0
                    
                    # Remove cleared rows
                    board[:] = [row for row in board if any(cell != -1 for cell in row)]
                    while len(board) < ROWS:
                        board.insert(0, [0] * COLS)
                continue
            
            # DAS (Delayed Auto Shift) handling
            if keys[pygame.K_LEFT]:
                if das_left == 0:
                    # Initial move
                    if not check_collision(board, current_piece.shape, current_piece.x - 1, current_piece.y):
                        current_piece.x -= 1
                        lock_delay = 0
                das_left += 1
                if das_left >= DAS_DELAY:
                    if (das_left - DAS_DELAY) % DAS_RATE == 0:
                        if not check_collision(board, current_piece.shape, current_piece.x - 1, current_piece.y):
                            current_piece.x -= 1
                            lock_delay = 0
            else:
                das_left = 0
            
            if keys[pygame.K_RIGHT]:
                if das_right == 0:
                    # Initial move
                    if not check_collision(board, current_piece.shape, current_piece.x + 1, current_piece.y):
                        current_piece.x += 1
                        lock_delay = 0
                das_right += 1
                if das_right >= DAS_DELAY:
                    if (das_right - DAS_DELAY) % DAS_RATE == 0:
                        if not check_collision(board, current_piece.shape, current_piece.x + 1, current_piece.y):
                            current_piece.x += 1
                            lock_delay = 0
            else:
                das_right = 0
            
            # Soft drop
            soft_dropping = keys[pygame.K_DOWN]
            
            # Gravity
            drop_speed = get_level_speed(level)
            if soft_dropping:
                drop_speed = max(1, drop_speed // 2)  # Soft drop is twice as fast
            
            drop_timer += 1
            if drop_timer >= drop_speed:
                drop_timer = 0
                if not check_collision(board, current_piece.shape, current_piece.x, current_piece.y + 1):
                    current_piece.y += 1
                    if soft_dropping:
                        score += 1  # Soft drop scoring
                    lock_delay = 0
                else:
                    # Piece hit bottom, start lock delay
                    lock_delay += 1
            
            # Check if piece should lock
            if check_collision(board, current_piece.shape, current_piece.x, current_piece.y + 1):
                lock_delay += 1
                if lock_delay >= max_lock_delay:
                    # Lock the piece
                    merge_piece(board, current_piece)
                    statistics[current_piece.shape_id] += 1
                    
                    # Check for line clears
                    cleared_lines = clear_rows(board)
                    if cleared_lines > 0:
                        lines += cleared_lines
                        score += calculate_score(cleared_lines, level)
                        level = min(29, lines // 10 + starting_level)  # Cap at level 29
                        
                        # Play sound effect
                        if sound_effects:
                            if cleared_lines == 4:
                                sound_effects['tetris'].play()
                            else:
                                sound_effects['clear'].play()
                        
                        # Start line clear animation
                        line_clear_timer = line_clear_delay
                    
                    # Spawn new piece
                    current_piece = next_piece
                    next_piece = Piece(random.randint(0, 6))
                    drop_timer = 0
                    lock_delay = 0
                    das_left = 0
                    das_right = 0
                    
                    # Check for game over
                    if check_collision(board, current_piece.shape, current_piece.x, current_piece.y):
                        game_over = True
                        game_state.add_score(score, 'A_TYPE')
                        if sound_effects:
                            sound_effects['gameover'].play()
                        pygame.mixer.stop()
        
        # Calculate ghost piece position
        ghost_y = current_piece.y
        while not check_collision(board, current_piece.shape, current_piece.x, ghost_y + 1):
            ghost_y += 1
        
        # Draw everything
        draw_background(screen)
        draw_grid(screen)
        draw_board(screen, board)
        
        if not game_over:
            draw_piece(screen, current_piece, ghost_y)
        
        draw_ui(screen, font, score, lines, level, next_piece, statistics)
        
        if paused and not game_over:
            draw_pause(screen, font)
        
        if game_over:
            draw_game_over(screen, font, score, game_state.high_scores['A_TYPE'])
        
        pygame.display.flip()
    
    return 'quit'

def main():
    """Main game entry point."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ultra Tetris HDR 1.0 - Game Boy Edition")
    clock = pygame.time.Clock()
    
    # Set icon (optional)
    icon_surface = pygame.Surface((32, 32))
    icon_surface.fill(GB_LIGHT)
    pygame.draw.rect(icon_surface, GB_DARK, (8, 8, 16, 16))
    pygame.display.set_icon(icon_surface)
    
    # Initialize audio
    init_audio()
    
    # Load game state
    game_state = GameState()
    
    # Main menu loop
    font = pygame.font.Font(None, 24)
    in_menu = True
    
    while in_menu:
        # Draw main menu
        draw_main_menu(screen, font)
        pygame.display.flip()
        
        # Handle menu input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                in_menu = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    # Start game
                    result = run_game(screen, clock, game_state, starting_level=0)
                    
                    if result == 'quit':
                        in_menu = False
                    elif result == 'restart':
                        continue
                    elif result == 'menu':
                        continue
        
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
