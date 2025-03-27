#!/usr/bin/env python3
"""
Custom Spelling Bee Puzzle Generator

This script generates a single puzzle for a New York Times Spelling Bee game clone
based on user-provided letters. It outputs JSON that can be incorporated into
existing puzzle sets.

Usage:
    python create_custom_puzzle.py -c <center_letter> -o <outside_letters> [--dict <dictionary_file>]
    
Example:
    python create_custom_puzzle.py -c a -o b,c,d,e,f,g --dict filtered_12dictionary_40k.json
"""

import json
import uuid
import argparse
from datetime import datetime
from typing import Dict, List, Set, Any
from collections import Counter

# Constants copied from generate_spelling_bee.py
PANGRAM_BONUS = 10
BINGO_BONUS = 10
MIN_WORD_LENGTH = 4

def load_dictionary(file_path: str) -> Dict[str, int]:
    """Load dictionary from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def is_valid_word(word: str, center: str, letters: Set[str]) -> bool:
    """
    Check if a word is valid for the puzzle:
    - Contains the center letter
    - Only uses allowed letters
    - At least MIN_WORD_LENGTH letters long
    """
    if len(word) < MIN_WORD_LENGTH:
        return False
    if center not in word:
        return False
    return all(c in letters for c in word)

def is_pangram(word: str, letters: Set[str]) -> bool:
    """Check if a word uses all letters in the set."""
    return set(word) == letters

def calculate_score(word: str, letters: Set[str]) -> int:
    """Calculate score for a word."""
    if len(word) == 4:
        points = 1
    else:
        points = len(word)
    
    if is_pangram(word, letters):
        points += PANGRAM_BONUS
        
    return points

def calculate_total_score(valid_words: List[str], letters: Set[str], has_bingo: bool) -> int:
    """Calculate total score for a puzzle."""
    base_score = sum(calculate_score(word, letters) for word in valid_words)
    if has_bingo:
        return base_score + BINGO_BONUS
    return base_score

def check_bingo(valid_words: List[str], letters: List[str]) -> bool:
    """Check if at least one word starts with each letter in the set."""
    starting_letters = set(word[0] for word in valid_words)
    return all(letter in starting_letters for letter in letters)

def get_valid_words(dictionary: Dict[str, int], center: str, letters: Set[str]) -> List[str]:
    """Get all valid words for a given letter set."""
    valid_words = []
    for word in dictionary:
        if is_valid_word(word, center, letters):
            valid_words.append(word)
    return valid_words

def get_pangrams(valid_words: List[str], letters: Set[str]) -> List[str]:
    """Get all pangrams from the valid words."""
    return [word for word in valid_words if is_pangram(word, letters)]

def create_custom_puzzle(dictionary: Dict[str, int], center_letter: str, 
                         outside_letters: List[str]) -> Dict[str, Any]:
    """Generate a single custom puzzle based on provided letters."""
    # Normalize input to lowercase
    center_letter = center_letter.lower()
    outside_letters = [letter.lower() for letter in outside_letters]
    
    # Create the full letter set
    all_letters = set(outside_letters + [center_letter])
    
    # Validate we have exactly 7 unique letters
    if len(all_letters) != 7:
        raise ValueError(f"Expected 7 unique letters, got {len(all_letters)}")
    
    # Get valid words for this letter set
    valid_words = get_valid_words(dictionary, center_letter, all_letters)
    
    # Get pangrams
    pangrams = get_pangrams(valid_words, all_letters)
    
    # Check if bingo is possible
    has_bingo = check_bingo(valid_words, list(all_letters))
    
    # Calculate total score
    total_score = calculate_total_score(valid_words, all_letters, has_bingo)
    
    # Create puzzle
    puzzle = {
        "id": str(uuid.uuid4())[:8],  # First 8 chars of UUID
        "last_reviewed": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "live_date": datetime.now().strftime('%Y-%m-%d'),  # Set to today
        "center_letter": center_letter,
        "outside_letters": outside_letters,
        "pangrams": pangrams,
        "bingo_possible": has_bingo,
        "total_score": total_score,
        "total_words": len(valid_words),
        "valid_words": sorted(valid_words)
    }
    
    return puzzle

def main():
    """Parse command line arguments and generate a custom puzzle."""
    parser = argparse.ArgumentParser(description='Generate a custom Spelling Bee puzzle')
    parser.add_argument('-c', '--center', required=True, help='Center letter')
    parser.add_argument('-o', '--outside', required=True, 
                      help='Outside letters (comma-separated, no spaces)')
    parser.add_argument('--dict', default='filtered_12dictionary_40k.json', 
                      help='Dictionary file path')
    parser.add_argument('--output', help='Output file path (optional, outputs to console if not specified)')
    
    args = parser.parse_args()
    
    # Validate center letter (should be a single character)
    if len(args.center) != 1:
        parser.error("Center letter must be a single character")
        
    # Parse outside letters
    outside_letters = args.outside.split(',')
    
    # Validate outside letters (should be 6 unique letters)
    if len(outside_letters) != 6:
        parser.error(f"Expected 6 outside letters, got {len(outside_letters)}")
    
    # Ensure no overlap between center and outside letters
    if args.center in outside_letters:
        parser.error("Center letter cannot be in outside letters")
    
    # Load dictionary
    print(f"Loading dictionary from {args.dict}...")
    try:
        dictionary = load_dictionary(args.dict)
    except FileNotFoundError:
        parser.error(f"Dictionary file not found: {args.dict}")
    
    # Generate custom puzzle
    print("Generating custom puzzle...")
    puzzle = create_custom_puzzle(dictionary, args.center, outside_letters)
    
    # Print puzzle statistics
    print(f"\nPuzzle generated successfully!")
    print(f"Center letter: {puzzle['center_letter']}")
    print(f"Outside letters: {', '.join(puzzle['outside_letters'])}")
    print(f"Total words: {puzzle['total_words']}")
    print(f"Total score: {puzzle['total_score']}")
    print(f"Pangrams ({len(puzzle['pangrams'])}): {', '.join(puzzle['pangrams'])}")
    print(f"Bingo possible: {'Yes' if puzzle['bingo_possible'] else 'No'}")
    
    # Output as JSON
    json_output = json.dumps(puzzle, indent=2)
    
    if args.output:
        # Save to file
        with open(args.output, 'w') as f:
            f.write(json_output)
        print(f"\nPuzzle saved to {args.output}")
    else:
        # Print to console
        print("\nJSON Output:")
        print(json_output)
        
    # Provide instructions for manual integration
    print("\nTo add this puzzle to your existing puzzle sets file:")
    print("1. Open puzzle_sets_randomized.json")
    print("2. Add this JSON object to the array")
    print("3. Make sure to add a comma after the preceding object if needed")

if __name__ == "__main__":
    main() 