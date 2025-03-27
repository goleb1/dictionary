#!/usr/bin/env python3
"""
Batch process words across all puzzles to speed up review.
This script can pre-mark common words as valid and rare/obscure words as invalid.
"""

import json
import pickle
import argparse
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple

def load_word_cache(word_cache_file: str) -> Tuple[Set[str], Set[str]]:
    """Load valid and rejected words from word_cache.json."""
    valid_words = set()
    obscure_words = set()
    
    if os.path.exists(word_cache_file):
        try:
            with open(word_cache_file, 'r') as f:
                cache = json.load(f)
                valid_words = set(cache.get('valid', []))
                obscure_words = set(cache.get('rejected', []))
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: Could not load word cache from {word_cache_file}")
    
    return valid_words, obscure_words

def save_word_cache(word_cache_file: str, valid_words: Set[str], obscure_words: Set[str]) -> None:
    """Save valid and rejected words to word_cache.json."""
    cache = {
        'valid': sorted(list(valid_words)),
        'rejected': sorted(list(obscure_words))
    }
    
    # Create a backup of the existing cache file
    if os.path.exists(word_cache_file):
        backup_file = f'word_cache_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        try:
            with open(word_cache_file, 'r') as src:
                with open(backup_file, 'w') as dst:
                    dst.write(src.read())
            print(f"Created backup of word cache at {backup_file}")
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
    
    # Save updated cache
    with open(word_cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
    print(f"Word cache saved to {word_cache_file}")

def load_word_frequencies() -> Dict[str, int]:
    """Load word frequencies from pickle file."""
    try:
        with open('word_frequency.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("Warning: word_frequency.pkl not found. Using empty frequency dictionary.")
        return {}

def load_puzzle_sets(file_path: str) -> List[Dict]:
    """Load puzzle sets from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def collect_all_words(puzzle_sets: List[Dict]) -> Set[str]:
    """Collect all unique words from all puzzles."""
    all_words = set()
    for puzzle in puzzle_sets:
        all_words.update(puzzle.get('valid_words', []))
    return all_words

def batch_process(puzzle_sets_file: str, word_cache_file: str, 
                  freq_threshold: int, min_length: int,
                  action: str, dry_run: bool = False) -> None:
    """
    Batch process words in all puzzles.
    
    Args:
        puzzle_sets_file: Path to puzzle sets JSON file
        word_cache_file: Path to word cache JSON file
        freq_threshold: Frequency threshold for processing
        min_length: Minimum word length to consider for processing
        action: 'auto' (mark common as valid, rare as obscure), 
                'valid' (mark words above threshold as valid), or 
                'obscure' (mark words below threshold as obscure)
        dry_run: If True, only preview changes without saving
    """
    # Load data
    valid_words, obscure_words = load_word_cache(word_cache_file)
    word_frequencies = load_word_frequencies()
    puzzle_sets = load_puzzle_sets(puzzle_sets_file)
    
    # Collect all unique words
    all_words = collect_all_words(puzzle_sets)
    print(f"Found {len(all_words)} unique words across all puzzles")
    
    # Count words already marked
    already_valid = sum(1 for word in all_words if word in valid_words)
    already_obscure = sum(1 for word in all_words if word in obscure_words)
    unmarked = len(all_words) - already_valid - already_obscure
    
    print(f"Status before processing:")
    print(f"  Already marked as valid: {already_valid} words")
    print(f"  Already marked as obscure: {already_obscure} words")
    print(f"  Unmarked: {unmarked} words")
    
    # Process words based on action
    new_valid = set()
    new_obscure = set()
    
    if action in ['auto', 'valid']:
        # Mark common words as valid
        for word in all_words:
            if (word not in valid_words and 
                word not in obscure_words and
                word in word_frequencies and 
                word_frequencies[word] >= freq_threshold):
                new_valid.add(word)
    
    if action in ['auto', 'obscure']:
        # Mark rare words as obscure
        for word in all_words:
            if (word not in valid_words and 
                word not in obscure_words and
                ((word in word_frequencies and word_frequencies[word] < freq_threshold and len(word) < min_length) or
                 (word not in word_frequencies and len(word) < min_length))):
                new_obscure.add(word)
    
    print(f"\nChanges to be made:")
    print(f"  Words to mark as valid: {len(new_valid)}")
    print(f"  Words to mark as obscure: {len(new_obscure)}")
    
    # Sample of words to be marked
    if new_valid:
        sample = list(new_valid)[:50] if len(new_valid) > 10 else list(new_valid)
        print(f"\nSample of words to mark as valid: {', '.join(sample)}")
    
    if new_obscure:
        sample = list(new_obscure)[:50] if len(new_obscure) > 10 else list(new_obscure)
        print(f"\nSample of words to mark as obscure: {', '.join(sample)}")
    
    # Apply changes if not dry run
    if not dry_run:
        valid_words.update(new_valid)
        obscure_words.update(new_obscure)
        save_word_cache(word_cache_file, valid_words, obscure_words)
        print(f"\nChanges applied to word cache.")
    else:
        print(f"\nDry run - no changes applied. Run without --dry-run to apply changes.")

def main():
    parser = argparse.ArgumentParser(description='Batch process words in all puzzles')
    parser.add_argument('--puzzle-sets', default='puzzle_sets.json',
                        help='Path to puzzle sets JSON file')
    parser.add_argument('--word-cache', default='word_cache.json',
                        help='Path to word cache JSON file')
    parser.add_argument('--freq-threshold', type=int, default=50000,
                        help='Frequency threshold for processing')
    parser.add_argument('--min-length', type=int, default=8,
                        help='Minimum word length to consider rare words as valid')
    parser.add_argument('--action', choices=['auto', 'valid', 'obscure'], default='auto',
                        help='Processing action: auto (both), valid (only mark valid), or obscure (only mark obscure)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without saving')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.puzzle_sets):
        print(f"Error: Could not find puzzle sets file at {args.puzzle_sets}")
        return
    
    batch_process(args.puzzle_sets, args.word_cache, 
                 args.freq_threshold, args.min_length,
                 args.action, args.dry_run)

if __name__ == "__main__":
    main() 