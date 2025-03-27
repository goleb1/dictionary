import json
from datetime import datetime, timedelta

def is_pangram(word, center_letter, outside_letters):
    # Convert word to set of unique letters
    word_letters = set(word.lower())
    # Check if the word contains the center letter and all outside letters
    required_letters = set(outside_letters + [center_letter])
    return required_letters.issubset(word_letters)

# Read the original JSON file
with open('puzzle_sets_filtered.json', 'r') as f:
    puzzle_sets = json.load(f)

# Process each puzzle set and filter out ones without pangrams
filtered_puzzles = []
current_date = datetime.now()

for puzzle_set in puzzle_sets:
    # Find pangrams in valid words
    pangrams_list = [
        word for word in puzzle_set['valid_words']
        if is_pangram(word, puzzle_set['center_letter'], puzzle_set['outside_letters'])
    ]
    
    # Only keep puzzles that have at least one pangram
    if pangrams_list:
        # Create new puzzle set with reordered fields
        new_puzzle_set = {
            "id": puzzle_set["id"],
            "live_date": current_date.strftime("%Y-%m-%d"),
            "center_letter": puzzle_set["center_letter"],
            "outside_letters": puzzle_set["outside_letters"],
            "pangrams": pangrams_list,
            "bingo_possible": puzzle_set["bingo_possible"],
            "total_score": puzzle_set["total_score"],
            "total_words": puzzle_set["total_words"],
            "valid_words": puzzle_set["valid_words"]
        }
        filtered_puzzles.append(new_puzzle_set)
        # Increment date for next puzzle
        current_date += timedelta(days=1)

# Write the modified JSON back to file
with open('puzzle_sets_filtered.json', 'w') as f:
    json.dump(filtered_puzzles, f, indent=2) 