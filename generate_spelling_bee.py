#!/usr/bin/env python3
"""
Spelling Bee Puzzle Generator

This script generates unique puzzle sets for a New York Times Spelling Bee game clone
according to specified requirements.

Input: Dictionary file in JSON format
Output: JSON file with puzzle sets
"""

import json
import uuid
import random
import string
import itertools
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Set, Tuple, Any

# Scoring rules
PANGRAM_BONUS = 10
BINGO_BONUS = 10
MIN_WORD_LENGTH = 4
MIN_WORDS_PER_PUZZLE = 25
MAX_WORDS_PER_PUZZLE = 200
MIN_PANGRAMS = 1
MAX_PANGRAMS = 6
DAYS_WITHOUT_REPETITION = 60
NUM_PUZZLES = 180


def load_dictionary(file_path: str) -> Dict[str, int]:
    """Load dictionary from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def save_puzzle_sets(puzzle_sets: List[Dict[str, Any]], file_path: str) -> None:
    """Save puzzle sets to JSON file."""
    with open(file_path, 'w') as f:
        json.dump(puzzle_sets, f, indent=2)


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


def generate_letter_sets(dictionary: Dict[str, int]) -> List[Tuple[str, Set[str]]]:
    """
    Generate potential letter sets by analyzing the dictionary.
    Focus on letter combinations that appear in pangrams.
    """
    # Count letter frequencies in the dictionary
    letter_counts = Counter(''.join(dictionary.keys()))
    
    # Start with common letter combinations from pangrams
    pangram_candidates = []
    for word in dictionary:
        if len(set(word)) == 7:  # Potential pangram
            pangram_candidates.append(set(word))
    
    # If we have enough potential pangrams, use them
    if len(pangram_candidates) >= NUM_PUZZLES * 2:
        random.shuffle(pangram_candidates)
        letter_sets = []
        for letter_set in pangram_candidates[:NUM_PUZZLES * 2]:
            # Choose center letter - prefer vowels or common letters
            letters = list(letter_set)
            vowels = [l for l in letters if l in 'aeiou']
            if vowels:
                center = random.choice(vowels)
            else:
                # Weight by frequency
                weights = [letter_counts[l] for l in letters]
                center = random.choices(letters, weights=weights)[0]
            letter_sets.append((center, letter_set))
        return letter_sets
    
    # Fallback: generate letter sets algorithmically
    letter_sets = []
    
    # Common vowels and consonants
    vowels = ['a', 'e', 'i', 'o', 'u']
    common_consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'l', 'm', 'n', 'p', 'r', 's', 't']
    
    # Generate sets with good mix of vowels and consonants
    for _ in range(NUM_PUZZLES * 3):  # Generate extra to filter later
        # 2-3 vowels per set
        num_vowels = random.randint(2, 3)
        set_vowels = random.sample(vowels, num_vowels)
        
        # 4-5 consonants
        num_consonants = 7 - num_vowels
        set_consonants = random.sample(common_consonants, num_consonants)
        
        letter_set = set(set_vowels + set_consonants)
        
        # Choose center letter (prefer vowels)
        if random.random() < 0.7 and set_vowels:  # 70% chance to pick vowel as center
            center = random.choice(set_vowels)
        else:
            center = random.choice(list(letter_set))
            
        letter_sets.append((center, letter_set))
    
    return letter_sets


def filter_puzzles(candidate_puzzles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter puzzles to ensure diversity and no duplications.
    Ensure letter sets aren't repeated within DAYS_WITHOUT_REPETITION.
    """
    filtered_puzzles = []
    used_letter_sets = set()
    
    # Sort by number of pangrams (descending) and then by total words (descending)
    sorted_puzzles = sorted(
        candidate_puzzles, 
        key=lambda p: (len(p['pangrams']), p['total_words']), 
        reverse=True
    )
    
    for puzzle in sorted_puzzles:
        # Create a frozen set of letters for comparison
        letter_set = frozenset([puzzle['center_letter']] + puzzle['outside_letters'])
        
        # Skip if we've used this letter set recently
        if letter_set in used_letter_sets:
            continue
            
        filtered_puzzles.append(puzzle)
        used_letter_sets.add(letter_set)
        
        # Stop once we have enough puzzles
        if len(filtered_puzzles) >= NUM_PUZZLES:
            break
            
    return filtered_puzzles


def generate_puzzles(dictionary: Dict[str, int]) -> List[Dict[str, Any]]:
    """Generate puzzle sets."""
    letter_sets = generate_letter_sets(dictionary)
    candidate_puzzles = []
    
    for center, letters in letter_sets:
        # Get valid words
        valid_words = get_valid_words(dictionary, center, letters)
        
        # Skip if not enough words
        if len(valid_words) < MIN_WORDS_PER_PUZZLE or len(valid_words) > MAX_WORDS_PER_PUZZLE:
            continue
            
        # Get pangrams
        pangrams = get_pangrams(valid_words, letters)
        
        # Skip if not enough or too many pangrams
        if len(pangrams) < MIN_PANGRAMS or len(pangrams) > MAX_PANGRAMS:
            continue
            
        # Check if bingo is possible
        outside_letters = list(letters - {center})
        has_bingo = check_bingo(valid_words, list(letters))
        
        # Calculate total score
        total_score = calculate_total_score(valid_words, letters, has_bingo)
        
        # Create puzzle set
        puzzle = {
            'id': str(uuid.uuid4())[:8],  # First 8 chars of UUID
            'last_reviewed': (datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'live_date': None,  # Will be set later
            'center_letter': center,
            'outside_letters': outside_letters,
            'pangrams': pangrams,
            'bingo_possible': has_bingo,
            'total_score': total_score,
            'total_words': len(valid_words),
            'valid_words': sorted(valid_words)
        }
        
        candidate_puzzles.append(puzzle)
    
    # Filter and limit number of puzzles
    filtered_puzzles = filter_puzzles(candidate_puzzles)
    
    # Shuffle the puzzles for variety while preserving diversity from filter_puzzles
    # This ensures no correlation between puzzle properties (pangrams, word count, etc.) and time
    # Without this, puzzles would be ordered from most pangrams/words to least
    random.shuffle(filtered_puzzles)
    
    # Set live dates
    start_date = datetime.now().date()
    for i, puzzle in enumerate(filtered_puzzles):
        puzzle['live_date'] = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
    
    return filtered_puzzles


def main():
    """Main function to run the generator."""
    parser = argparse.ArgumentParser(description='Generate Spelling Bee puzzle sets')
    parser.add_argument('--input', default='filtered_12dictionary_40k.json', 
                        help='Input dictionary file path')
    parser.add_argument('--output', default='puzzle_sets.json',
                        help='Output puzzle sets file path')
    args = parser.parse_args()
    
    # Load dictionary
    print(f"Loading dictionary from {args.input}...")
    dictionary = load_dictionary(args.input)
    
    # Generate puzzles
    print("Generating puzzle sets...")
    puzzle_sets = generate_puzzles(dictionary)
    
    # Save puzzles
    print(f"Saving {len(puzzle_sets)} puzzle sets to {args.output}...")
    save_puzzle_sets(puzzle_sets, args.output)
    
    print("Done!")
    print(f"Generated {len(puzzle_sets)} puzzle sets")
    print(f"Average words per puzzle: {sum(p['total_words'] for p in puzzle_sets) / len(puzzle_sets):.2f}")
    print(f"Average pangrams per puzzle: {sum(len(p['pangrams']) for p in puzzle_sets) / len(puzzle_sets):.2f}")
    print(f"Average score per puzzle: {sum(p['total_score'] for p in puzzle_sets) / len(puzzle_sets):.2f}")


if __name__ == "__main__":
    main() 