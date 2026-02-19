#!/usr/bin/env python3
"""
Compare the properties of randomized vs non-randomized puzzle files.
"""

import json
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from scipy import stats
import os

def load_puzzle_sets(file_path):
    """Load puzzle sets from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def check_randomization(puzzle_sets, title_suffix=""):
    """Analyze puzzle distribution by checking the properties over time."""
    # Sort puzzles by live date
    puzzle_sets.sort(key=lambda p: p['live_date'])
    
    # Extract properties over time
    days = list(range(len(puzzle_sets)))
    total_words = [p['total_words'] for p in puzzle_sets]
    total_scores = [p['total_score'] for p in puzzle_sets]
    pangram_counts = [len(p['pangrams']) for p in puzzle_sets]
    
    # Check for trends or patterns (correlation with day)
    word_corr = stats.pearsonr(days, total_words)[0]
    score_corr = stats.pearsonr(days, total_scores)[0]
    pangram_corr = stats.pearsonr(days, pangram_counts)[0]
    
    print(f"Checking for trends in puzzle set {title_suffix}:")
    print(f"Correlation of words with time: {word_corr:.4f}")
    print(f"Correlation of scores with time: {score_corr:.4f}")
    print(f"Correlation of pangrams with time: {pangram_corr:.4f}")
    
    # Create plots to visualize
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))
    
    # Plot words over time
    axs[0].scatter(days, total_words, alpha=0.6)
    axs[0].set_title(f'Total Words per Puzzle Over Time {title_suffix}')
    axs[0].set_xlabel('Puzzle Day')
    axs[0].set_ylabel('Word Count')
    
    # Plot scores over time
    axs[1].scatter(days, total_scores, alpha=0.6)
    axs[1].set_title(f'Total Score per Puzzle Over Time {title_suffix}')
    axs[1].set_xlabel('Puzzle Day')
    axs[1].set_ylabel('Score')
    
    # Plot pangrams over time
    axs[2].scatter(days, pangram_counts, alpha=0.6)
    axs[2].set_title(f'Pangram Count per Puzzle Over Time {title_suffix}')
    axs[2].set_xlabel('Puzzle Day')
    axs[2].set_ylabel('Number of Pangrams')
    
    plt.tight_layout()
    plt.savefig(f'puzzle_{title_suffix.replace(" ", "_").lower()}.png')
    print(f"Visualization saved to 'puzzle_{title_suffix.replace(' ', '_').lower()}.png'")

def main():
    """Main function."""
    # Generate new unrandomized puzzles for comparison if needed
    if not os.path.exists('puzzle_sets.json'):
        print("Original puzzle file not found. Generating a new one for comparison...")
        import generate_spelling_bee  # Import the module to run it
        import sys
        sys.argv = ['generate_spelling_bee.py', '--output', 'puzzle_sets.json']
        
        # Temporarily modify the randomization in the module
        original_shuffle = generate_spelling_bee.random.shuffle
        generate_spelling_bee.random.shuffle = lambda x: None  # Do nothing instead of shuffling
        generate_spelling_bee.main()
        generate_spelling_bee.random.shuffle = original_shuffle  # Restore original shuffle
    
    # Now check both files
    if os.path.exists('puzzle_sets.json'):
        original_puzzles = load_puzzle_sets('puzzle_sets.json')
        check_randomization(original_puzzles, "(Original)")
    
    if os.path.exists('puzzle_sets_randomized.json'):
        randomized_puzzles = load_puzzle_sets('puzzle_sets_randomized.json')
        check_randomization(randomized_puzzles, "(Randomized)")
    
    print("\nComparison complete. Check the visualization files to see the differences.")

if __name__ == "__main__":
    main() 