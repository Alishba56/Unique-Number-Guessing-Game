import streamlit as st
import random
import time
import math
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Unique Number Guessing Game",
    page_icon="🎲",
    layout="wide"
)

# Initialize session state variables
if 'game_initialized' not in st.session_state:
    st.session_state.game_initialized = False
    st.session_state.target_number = 0
    st.session_state.attempts = 0
    st.session_state.max_attempts = 10
    st.session_state.min_range = 1
    st.session_state.max_range = 100
    st.session_state.hints_used = 0
    st.session_state.available_hints = 3
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.best_streak = 0
    st.session_state.game_over = False
    st.session_state.win = False
    st.session_state.guess_history = []
    st.session_state.start_time = time.time()
    st.session_state.game_mode = "normal"
    st.session_state.difficulty = "medium"
    st.session_state.proximity = 0
    st.session_state.last_proximity = 0
    st.session_state.time_limit = 60
    st.session_state.game_initialized = True

# Function to initialize a new game
def initialize_game():
    difficulty_ranges = {
        "easy": (1, 50, 15, 3),
        "medium": (1, 100, 10, 2),
        "hard": (1, 200, 8, 1),
        "expert": (1, 500, 6, 0)
    }
    
    min_range, max_range, max_attempts, available_hints = difficulty_ranges[st.session_state.difficulty]
    
    st.session_state.min_range = min_range
    st.session_state.max_range = max_range
    st.session_state.max_attempts = max_attempts
    st.session_state.available_hints = available_hints
    
    if st.session_state.game_mode == "normal":
        st.session_state.target_number = random.randint(min_range, max_range)
    elif st.session_state.game_mode == "evil":
        # Evil mode: number changes slightly within a range after each guess
        st.session_state.target_number = random.randint(min_range, max_range)
        st.session_state.evil_range = max(5, int((max_range - min_range) * 0.05))
    elif st.session_state.game_mode == "binary":
        # Binary mode: number is represented in binary
        st.session_state.target_number = random.randint(min_range, max_range)
    
    st.session_state.attempts = 0
    st.session_state.hints_used = 0
    st.session_state.game_over = False
    st.session_state.win = False
    st.session_state.guess_history = []
    st.session_state.start_time = time.time()
    st.session_state.proximity = 0
    st.session_state.last_proximity = 0

# Function to calculate proximity (0-100) where 100 is exact match
def calculate_proximity(guess, target, min_range, max_range):
    max_distance = max_range - min_range
    distance = abs(guess - target)
    proximity = 100 - (distance / max_distance * 100)
    return max(0, min(100, proximity))

# Function to get temperature description based on proximity
def get_temperature(proximity):
    if proximity >= 95:
        return "🔥 BURNING HOT!", "red"
    elif proximity >= 85:
        return "🔥 Very Hot!", "#FF4500"
    elif proximity >= 70:
        return "🔥 Hot", "#FF8C00"
    elif proximity >= 50:
        return "🌡️ Warm", "#FFA500"
    elif proximity >= 30:
        return "❄️ Cool", "#1E90FF"
    elif proximity >= 15:
        return "❄️ Cold", "#00BFFF"
    else:
        return "🧊 FREEZING!", "#0000FF"

# Function to calculate score based on attempts, hints, and difficulty
def calculate_score(attempts, hints_used, difficulty, time_taken, max_attempts):
    difficulty_multiplier = {"easy": 1, "medium": 2, "hard": 3, "expert": 5}
    base_score = 1000
    attempts_penalty = (attempts / max_attempts) * 500
    hints_penalty = hints_used * 100
    time_penalty = min(200, time_taken / 2)
    
    score = base_score - attempts_penalty - hints_penalty - time_penalty
    score *= difficulty_multiplier[difficulty]
    
    return max(0, int(score))

# Function to provide a hint
def get_hint():
    if st.session_state.available_hints <= st.session_state.hints_used:
        return "No more hints available!"
    
    st.session_state.hints_used += 1
    
    hint_types = [
        f"The number is {'even' if st.session_state.target_number % 2 == 0 else 'odd'}.",
        f"The number is {'divisible by 5' if st.session_state.target_number % 5 == 0 else 'not divisible by 5'}.",
        f"The number is {'greater than ' + str(st.session_state.min_range + (st.session_state.max_range - st.session_state.min_range) // 2) if st.session_state.target_number > (st.session_state.min_range + (st.session_state.max_range - st.session_state.min_range) // 2) else 'less than ' + str(st.session_state.min_range + (st.session_state.max_range - st.session_state.min_range) // 2)}.",
        f"The sum of the digits is {sum(int(digit) for digit in str(st.session_state.target_number))}.",
        f"The first digit is {str(st.session_state.target_number)[0]}.",
        f"The last digit is {str(st.session_state.target_number)[-1]}."
    ]
    
    # Choose a hint that hasn't been given before
    used_hints = [h for h in st.session_state.guess_history if h.startswith("Hint:")]
    available_hints = [h for h in hint_types if f"Hint: {h}" not in used_hints]
    
    if available_hints:
        hint = random.choice(available_hints)
    else:
        # If all hint types have been used, give a narrower range
        lower = st.session_state.target_number - random.randint(1, 10)
        upper = st.session_state.target_number + random.randint(1, 10)
        lower = max(st.session_state.min_range, lower)
        upper = min(st.session_state.max_range, upper)
        hint = f"The number is between {lower} and {upper}."
    
    st.session_state.guess_history.append(f"Hint: {hint}")
    return hint

# Function to process a guess
def process_guess(guess):
    if st.session_state.game_over:
        return
    
    st.session_state.attempts += 1
    
    # In evil mode, the target number shifts slightly after each guess
    if st.session_state.game_mode == "evil" and st.session_state.attempts > 1:
        shift = random.randint(-st.session_state.evil_range, st.session_state.evil_range)
        st.session_state.target_number += shift
        # Ensure it stays within range
        st.session_state.target_number = max(st.session_state.min_range, min(st.session_state.max_range, st.session_state.target_number))
    
    # Calculate proximity for hot/cold indicator
    st.session_state.last_proximity = st.session_state.proximity
    st.session_state.proximity = calculate_proximity(guess, st.session_state.target_number, st.session_state.min_range, st.session_state.max_range)
    
    # Check if guess is correct
    if guess == st.session_state.target_number:
        st.session_state.win = True
        st.session_state.game_over = True
        st.session_state.streak += 1
        st.session_state.best_streak = max(st.session_state.streak, st.session_state.best_streak)
        
        # Calculate score
        time_taken = time.time() - st.session_state.start_time
        st.session_state.score += calculate_score(st.session_state.attempts, st.session_state.hints_used, st.session_state.difficulty, time_taken, st.session_state.max_attempts)
        
        result = f"🎉 Correct! You found the number in {st.session_state.attempts} attempts!"
    else:
        # Check if out of attempts
        if st.session_state.attempts >= st.session_state.max_attempts:
            st.session_state.game_over = True
            st.session_state.streak = 0
            result = f"❌ Game Over! You've used all {st.session_state.max_attempts} attempts. The number was {st.session_state.target_number}."
        else:
            # Provide feedback
            if guess < st.session_state.target_number:
                result = f"📈 Higher than {guess}! "
            else:
                result = f"📉 Lower than {guess}! "
            
            # Add temperature indicator
            temp_text, _ = get_temperature(st.session_state.proximity)
            result += temp_text
            
            # Add trend indicator
            if st.session_state.attempts > 1:
                if st.session_state.proximity > st.session_state.last_proximity:
                    result += " (Getting warmer! 🔥)"
                elif st.session_state.proximity < st.session_state.last_proximity:
                    result += " (Getting colder! ❄️)"
    
    # Check if time limit exceeded
    if st.session_state.game_mode == "timed" and time.time() - st.session_state.start_time > st.session_state.time_limit:
        st.session_state.game_over = True
        st.session_state.streak = 0
        result = f"⏱️ Time's up! The number was {st.session_state.target_number}."
    
    st.session_state.guess_history.append(f"Guess {st.session_state.attempts}: {guess} - {result}")
    return result

# Main title with custom styling
st.markdown("""
<style>
    .game-title {
        text-align: center;
        color: #FF5733;
        font-size: 3em;
        margin-bottom: 0.5em;
        text-shadow: 2px 2px 4px #cccccc;
    }
    .game-subtitle {
        text-align: center;
        color: #333333;
        font-size: 1.5em;
        margin-bottom: 1.5em;
    }
    .stButton button {
        width: 100%;
    }
    .hint-button {
        background-color: #FFD700;
    }
    .guess-history {
        height: 200px;
        overflow-y: auto;
        border: 1px solid #cccccc;
        padding: 10px;
        border-radius: 5px;
    }
    .temperature-meter {
        height: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .stats-box {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="game-title">🎲 MIND READER</div>', unsafe_allow_html=True)
st.markdown('<div class="game-subtitle">A Unique Number Guessing Experience</div>', unsafe_allow_html=True)

# Game settings in sidebar
with st.sidebar:
    st.header("Game Settings")
    
    new_difficulty = st.selectbox("Difficulty", 
                                 ["easy", "medium", "hard", "expert"],
                                 index=["easy", "medium", "hard", "expert"].index(st.session_state.difficulty))
    
    new_game_mode = st.selectbox("Game Mode", 
                                ["normal", "evil", "binary", "timed"],
                                index=["normal", "evil", "binary", "timed"].index(st.session_state.game_mode),
                                help="Normal: Standard game\nEvil: Target number shifts slightly after each guess\nBinary: Number shown in binary\nTimed: Race against the clock")
    
    if new_game_mode == "timed":
        new_time_limit = st.slider("Time Limit (seconds)", 30, 120, st.session_state.time_limit)
        if new_time_limit != st.session_state.time_limit:
            st.session_state.time_limit = new_time_limit
    
    # Start new game if settings change
    if new_difficulty != st.session_state.difficulty or new_game_mode != st.session_state.game_mode:
        st.session_state.difficulty = new_difficulty
        st.session_state.game_mode = new_game_mode
        initialize_game()
    
    if st.button("Start New Game"):
        initialize_game()
    
    # Display stats
    st.header("Stats")
    st.markdown(f"""
    <div class="stats-box">
        <p><b>Score:</b> {st.session_state.score}</p>
        <p><b>Current Streak:</b> {st.session_state.streak}</p>
        <p><b>Best Streak:</b> {st.session_state.best_streak}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Game instructions
    with st.expander("How to Play"):
        st.markdown("""
        1. Guess a number within the given range
        2. Get feedback on whether your guess is too high or too low
        3. The "temperature" indicator shows how close you are
        4. Use hints if you're stuck (costs points)
        5. Try to guess the number in as few attempts as possible
        
        **Game Modes:**
        - **Normal**: Standard number guessing
        - **Evil**: The target number shifts slightly after each guess
        - **Binary**: The number is shown in binary format
        - **Timed**: Race against the clock to find the number
        
        **Scoring:**
        - Base score: 1000 points
        - Penalties for attempts, hints used, and time taken
        - Difficulty multiplier: Easy (1x), Medium (2x), Hard (3x), Expert (5x)
        """)

# Main game area
col1, col2 = st.columns([2, 1])

with col1:
    # Game info
    st.subheader("Game Info")
    
    # Display range and mode-specific info
    range_text = f"Find a number between {st.session_state.min_range} and {st.session_state.max_range}"
    if st.session_state.game_mode == "binary":
        binary_target = bin(st.session_state.target_number)[2:]
        range_text += f" (Binary: {binary_target})" if st.session_state.game_over else " (shown in binary)"
    st.info(range_text)
    
    # Display attempts remaining
    attempts_left = st.session_state.max_attempts - st.session_state.attempts
    st.warning(f"Attempts remaining: {attempts_left}/{st.session_state.max_attempts}")
    
    # Display timer for timed mode
    if st.session_state.game_mode == "timed" and not st.session_state.game_over:
        elapsed_time = time.time() - st.session_state.start_time
        time_left = max(0, st.session_state.time_limit - elapsed_time)
        time_percent = (time_left / st.session_state.time_limit) * 100
        
        st.progress(time_percent / 100)
        st.write(f"⏱️ Time remaining: {int(time_left)} seconds")
    
    # Input for guess
    guess_col1, guess_col2 = st.columns([3, 1])
    
    with guess_col1:
        user_guess = st.number_input("Enter your guess:", 
                                     min_value=st.session_state.min_range, 
                                     max_value=st.session_state.max_range,
                                     step=1,
                                     disabled=st.session_state.game_over)
    
    with guess_col2:
        if st.button("Guess!", disabled=st.session_state.game_over):
            process_guess(user_guess)
    
    # Temperature indicator (only show after first guess)
    if st.session_state.attempts > 0 and not st.session_state.win:
        st.subheader("Temperature Gauge")
        temp_text, temp_color = get_temperature(st.session_state.proximity)
        
        # Create a progress bar for temperature
        st.progress(st.session_state.proximity / 100)
        
        # Display temperature text with color
        st.markdown(f"<div style='text-align: center; color: {temp_color}; font-size: 1.5em;'>{temp_text}</div>", unsafe_allow_html=True)
    
    # Hint button
    if not st.session_state.game_over and st.session_state.hints_used < st.session_state.available_hints:
        if st.button(f"Use Hint ({st.session_state.available_hints - st.session_state.hints_used} remaining)"):
            hint = get_hint()
            st.info(hint)
    elif not st.session_state.game_over and st.session_state.available_hints > 0:
        st.write("No more hints available!")

with col2:
    # Guess history
    st.subheader("Guess History")
    
    history_placeholder = st.empty()
    
    with history_placeholder.container():
        for entry in reversed(st.session_state.guess_history):
            if entry.startswith("Hint:"):
                st.info(entry)
            elif "Correct!" in entry:
                st.success(entry)
            elif "Game Over!" in entry or "Time's up!" in entry:
                st.error(entry)
            else:
                st.write(entry)
    
    # Game over message
    if st.session_state.game_over:
        if st.session_state.win:
            st.balloons()
            st.success(f"🏆 You won! The number was {st.session_state.target_number}.")
            time_taken = time.time() - st.session_state.start_time
            st.write(f"Time taken: {time_taken:.1f} seconds")
            st.write(f"Score earned: +{calculate_score(st.session_state.attempts, st.session_state.hints_used, st.session_state.difficulty, time_taken, st.session_state.max_attempts)}")
        else:
            st.error(f"Game over! The number was {st.session_state.target_number}.")
        
        if st.button("Play Again"):
            initialize_game()

# Initialize game if not already done
if not st.session_state.game_initialized:
    initialize_game()

# Auto-refresh for timed mode
if st.session_state.game_mode == "timed" and not st.session_state.game_over:
    st.experimental_rerun()
