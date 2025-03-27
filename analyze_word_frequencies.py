#!/usr/bin/env python3
"""
Analyze word frequencies in puzzle sets to optimize auto-review thresholds.
"""

import json
import pickle
import argparse
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os

def load_puzzle_sets(file_path):
    """Load puzzle sets from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_word_frequencies():
    """Load word frequencies from pickle file."""
    try:
        with open('word_frequency.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("Warning: word_frequency.pkl not found. Frequency analysis will be limited.")
        return {}

def analyze_frequencies(puzzle_sets, frequencies):
    """Analyze word frequencies across all puzzles."""
    all_words = set()
    pangrams = set()
    
    # Gather all words and pangrams
    for puzzle in puzzle_sets:
        center_letter = puzzle['center_letter']
        outside_letters = puzzle['outside_letters']
        all_letters = set(outside_letters + [center_letter])
        
        for word in puzzle['valid_words']:
            all_words.add(word)
            word_letters = set(word)
            if all_letters.issubset(word_letters):
                pangrams.add(word)
    
    # Get frequency information
    word_freqs = {}
    for word in all_words:
        word_freqs[word] = frequencies.get(word, 0)
    
    pangram_freqs = {word: freq for word, freq in word_freqs.items() if word in pangrams}
    
    # Calculate statistics
    all_freq_values = list(word_freqs.values())
    pangram_freq_values = list(pangram_freqs.values())
    
    # Create frequency buckets for analysis
    buckets = [0, 1000, 5000, 10000, 25000, 50000, 100000, 500000, 1000000, float('inf')]
    bucket_labels = [
        '0', 
        '1-1k', 
        '1k-5k', 
        '5k-10k', 
        '10k-25k', 
        '25k-50k', 
        '50k-100k', 
        '100k-500k', 
        '500k-1M', 
        '>1M'
    ]
    
    all_histogram = [0] * len(buckets)
    pangram_histogram = [0] * len(buckets)
    
    for freq in all_freq_values:
        for i in range(len(buckets)-1):
            if buckets[i] <= freq < buckets[i+1]:
                all_histogram[i] += 1
                break
    
    for freq in pangram_freq_values:
        for i in range(len(buckets)-1):
            if buckets[i] <= freq < buckets[i+1]:
                pangram_histogram[i] += 1
                break
    
    # Print statistics
    print(f"Total unique words: {len(all_words)}")
    print(f"Total pangrams: {len(pangrams)}")
    
    print("\nFrequency distribution (all words):")
    for i in range(len(buckets)-1):
        percentage = (all_histogram[i] / len(all_words)) * 100 if all_words else 0
        print(f"  {bucket_labels[i]}: {all_histogram[i]} words ({percentage:.1f}%)")
    
    print("\nFrequency distribution (pangrams):")
    for i in range(len(buckets)-1):
        percentage = (pangram_histogram[i] / len(pangrams)) * 100 if pangrams else 0
        print(f"  {bucket_labels[i]}: {pangram_histogram[i]} pangrams ({percentage:.1f}%)")
    
    # Word length analysis
    word_lengths = Counter([len(word) for word in all_words])
    
    print("\nWord length distribution:")
    for length, count in sorted(word_lengths.items()):
        percentage = (count / len(all_words)) * 100
        print(f"  {length} letters: {count} words ({percentage:.1f}%)")
    
    # Plot frequency distributions
    plt.figure(figsize=(12, 10))
    
    # Plot word frequency histogram
    plt.subplot(2, 1, 1)
    plt.bar(bucket_labels[:-1], all_histogram[:-1], alpha=0.7, label='All Words')
    plt.bar(bucket_labels[:-1], pangram_histogram[:-1], alpha=0.5, color='orange', label='Pangrams')
    plt.xlabel('Frequency')
    plt.ylabel('Number of Words')
    plt.title('Word Frequency Distribution')
    plt.legend()
    plt.xticks(rotation=45)
    
    # Plot word length histogram
    plt.subplot(2, 1, 2)
    lengths = sorted(word_lengths.keys())
    counts = [word_lengths[l] for l in lengths]
    plt.bar(lengths, counts, alpha=0.7)
    plt.xlabel('Word Length')
    plt.ylabel('Number of Words')
    plt.title('Word Length Distribution')
    
    plt.tight_layout()
    plt.savefig('word_frequency_analysis.png')
    print("\nPlot saved to 'word_frequency_analysis.png'")
    
    # Provide suggestions for auto-review thresholds
    all_sorted = sorted(all_freq_values)
    median_freq = np.median(all_sorted)
    percentile_25 = np.percentile(all_sorted, 25)
    percentile_75 = np.percentile(all_sorted, 75)
    
    print("\nSuggested auto-review thresholds:")
    print(f"  Conservative threshold (median): {median_freq:.0f}")
    print(f"  Aggressive threshold (75th percentile): {percentile_75:.0f}")
    print(f"  Very aggressive threshold (25th percentile): {percentile_25:.0f}")
    
    print("\nRecommendation:")
    print(f"  For auto-review, consider setting threshold to {percentile_75:.0f}")
    print(f"  This would auto-accept ~25% of words and mark the rest for review")

def main():
    parser = argparse.ArgumentParser(description='Analyze word frequencies in puzzle sets')
    parser.add_argument('input_file', help='Path to the puzzle sets JSON file')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Could not find puzzle sets file at {args.input_file}")
        return
    
    word_frequencies = load_word_frequencies()
    puzzle_sets = load_puzzle_sets(args.input_file)
    
    analyze_frequencies(puzzle_sets, word_frequencies)

if __name__ == "__main__":
    main() 