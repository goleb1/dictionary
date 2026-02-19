#!/usr/bin/env python3
"""
Check the randomization of puzzle properties over time.
"""

import json
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from scipy import stats

def load_puzzle_sets(file_path):
    """Load puzzle sets from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def check_randomization(puzzle_sets):
    """Analyze puzzle randomization by checking the distribution of properties over time."""
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
    
    print("Checking for randomization of puzzles over time:")
    print(f"Correlation of words with time: {word_corr:.4f}")
    print(f"Correlation of scores with time: {score_corr:.4f}")
    print(f"Correlation of pangrams with time: {pangram_corr:.4f}")
    
    # Create plots to visualize
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))
    
    # Plot words over time
    axs[0].scatter(days, total_words, alpha=0.6)
    axs[0].set_title('Total Words per Puzzle Over Time')
    axs[0].set_xlabel('Puzzle Day')
    axs[0].set_ylabel('Word Count')
    
    # Plot scores over time
    axs[1].scatter(days, total_scores, alpha=0.6)
    axs[1].set_title('Total Score per Puzzle Over Time')
    axs[1].set_xlabel('Puzzle Day')
    axs[1].set_ylabel('Score')
    
    # Plot pangrams over time
    axs[2].scatter(days, pangram_counts, alpha=0.6)
    axs[2].set_title('Pangram Count per Puzzle Over Time')
    axs[2].set_xlabel('Puzzle Day')
    axs[2].set_ylabel('Number of Pangrams')
    
    plt.tight_layout()
    plt.savefig('puzzle_randomization.png')
    print("Visualization saved to 'puzzle_randomization.png'")

def main():
    """Main function."""
    try:
        puzzle_sets = load_puzzle_sets('puzzle_sets_randomized.json')
        check_randomization(puzzle_sets)
    except Exception as e:
        print(f"Error: {e}")
        # Fallback to the original file
        print("Trying with original puzzle_sets.json")
        puzzle_sets = load_puzzle_sets('puzzle_sets.json')
        check_randomization(puzzle_sets)

if __name__ == "__main__":
    main() 