import json
from datetime import datetime, timedelta

# Read the JSON file
with open('puzzle_sets_randomized.json', 'r') as f:
    puzzles = json.load(f)

# Set the starting date
start_date = datetime(2025, 2, 26)

# Update each puzzle's live_date
for i, puzzle in enumerate(puzzles):
    new_date = start_date + timedelta(days=i)
    puzzle['live_date'] = new_date.strftime('%Y-%m-%d')

# Write back to the file
with open('puzzle_sets_randomized.json', 'w') as f:
    json.dump(puzzles, f, indent=2) 