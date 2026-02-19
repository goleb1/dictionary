#!/usr/bin/env python3
"""
Analyze generated puzzle sets and provide statistics.
"""

import json
import matplotlib.pyplot as plt
from collections import Counter

def load_puzzle_sets(file_path):
    """Load puzzle sets from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def analyze_puzzles(puzzle_sets):
    """Analyze puzzle sets and print statistics."""
    # Count pangrams per puzzle
    pangram_counts = [len(puzzle['pangrams']) for puzzle in puzzle_sets]
    pangram_histogram = Counter(pangram_counts)
    
    # Word counts per puzzle
    word_counts = [puzzle['total_words'] for puzzle in puzzle_sets]
    min_words = min(word_counts)
    max_words = max(word_counts)
    avg_words = sum(word_counts) / len(word_counts)
    
    # Score distribution
    scores = [puzzle['total_score'] for puzzle in puzzle_sets]
    min_score = min(scores)
    max_score = max(scores)
    avg_score = sum(scores) / len(scores)
    
    # Bingo possible count
    bingo_count = sum(1 for puzzle in puzzle_sets if puzzle['bingo_possible'])
    
    # Center letter distribution
    center_letters = Counter([puzzle['center_letter'] for puzzle in puzzle_sets])
    
    # Letter frequency overall
    all_letters = Counter()
    for puzzle in puzzle_sets:
        all_letters.update([puzzle['center_letter']])
        all_letters.update(puzzle['outside_letters'])
    
    # Print statistics
    print(f"Total puzzles analyzed: {len(puzzle_sets)}")
    print("\nPangram statistics:")
    for count, freq in sorted(pangram_histogram.items()):
        print(f"  {count} pangram(s): {freq} puzzles ({freq/len(puzzle_sets)*100:.1f}%)")
    
    print("\nWord count statistics:")
    print(f"  Minimum words: {min_words}")
    print(f"  Maximum words: {max_words}")
    print(f"  Average words: {avg_words:.2f}")
    
    print("\nScore statistics:")
    print(f"  Minimum score: {min_score}")
    print(f"  Maximum score: {max_score}")
    print(f"  Average score: {avg_score:.2f}")
    
    print(f"\nBingo possible: {bingo_count} puzzles ({bingo_count/len(puzzle_sets)*100:.1f}%)")
    
    print("\nTop 5 center letters:")
    for letter, count in center_letters.most_common(5):
        print(f"  {letter}: {count} puzzles ({count/len(puzzle_sets)*100:.1f}%)")
    
    print("\nTop 10 letters overall:")
    for letter, count in all_letters.most_common(10):
        print(f"  {letter}: {count} occurrences ({count/(len(puzzle_sets)*7)*100:.1f}%)")

def main():
    """Main function."""
    puzzle_sets = load_puzzle_sets('puzzle_sets.json')
    analyze_puzzles(puzzle_sets)

if __name__ == "__main__":
    main() 