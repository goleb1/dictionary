# Spelling Bee Puzzle Generator

A Python script that generates unique puzzle sets for a New York Times Spelling Bee game clone.

## Overview

This project generates approximately 180 unique puzzle sets, each consisting of 7 letters (1 central letter and 6 outer letters). Valid words in each puzzle must:
- Contain the central letter
- Only use letters from the set
- Be at least 4 letters long

Each puzzle has at least one pangram (word using all 7 letters) and contains between 25-200 valid words.

## Features

- Generates diverse puzzle sets with balanced letter distributions
- Ensures each puzzle has 1-6 pangrams
- Avoids letter set repetition within a 60-day period
- Randomizes puzzle order for optimal variety over time
- Calculates scores according to Spelling Bee rules
- Checks for "bingo" possibility (at least one word starting with each letter)
- Creates unique IDs for each puzzle

## Puzzle Randomization

The generator ensures that puzzles are presented in a randomized order with respect to their properties:

- Without randomization, puzzles would follow a predictable pattern from more pangrams to fewer pangrams over time
- With our randomization, there's no significant correlation between puzzle properties and time
- This provides a more engaging player experience with varied difficulty levels throughout the game's lifecycle

Correlation analysis of randomized puzzles shows:
- Words correlation: -0.0967 (essentially random)
- Score correlation: -0.1140 (essentially random)
- Pangrams correlation: -0.0201 (essentially random)

## Usage

### Requirements

Install the required packages:

```bash
pip install -r requirements.txt
```

### Generating Puzzles

Run the puzzle generator script:

```bash
python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output puzzle_sets.json
```

Parameters:
- `--input`: Input dictionary file path (default: filtered_12dictionary_40k.json)
- `--output`: Output puzzle sets file path (default: puzzle_sets.json)

### Analyzing Puzzles

To get statistics about the generated puzzles:

```bash
python analyze_puzzles.py
```

To check the randomization of puzzles over time:

```bash
python check_randomization.py
```

## Output Format

The script generates a JSON file with the following structure for each puzzle:

```json
{
  "id": "dc553376",
  "last_reviewed": "2025-02-24 12:04:11",
  "live_date": "2025-02-24",
  "center_letter": "i",
  "outside_letters": ["a", "e", "n", "o", "r", "t"],
  "pangrams": ["aeration", "anterior", "iteration", "orientate", "orientation", "reiteration"],
  "bingo_possible": true,
  "total_score": 656,
  "total_words": 99,
  "valid_words": [...]
}
```

## Scoring Rules

- 1 point for 4-letter words
- Word length for longer words
- +10 points for pangrams
- +10 points if bingo is possible

## Statistics

The generated puzzles have the following characteristics:
- 16.1% have 1 pangram, 36.7% have 2 pangrams, 25.0% have 3 pangrams
- Average of 112 words per puzzle
- Average score of 593 points per puzzle
- 85.6% of puzzles have "bingo" possibility
- Most common center letters: e (28.3%), a (27.2%), i (21.1%) 