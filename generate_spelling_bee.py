#!/usr/bin/env python3
"""
Spelling Bee Puzzle Generator

Pangram-first approach: each puzzle is anchored to an interesting 7-unique-letter
word. The anchor word's letters define the puzzle's letter set. The center letter
is chosen to hit the target word count range.

Input: Dictionary file in JSON format
Output: JSON file with puzzle sets
"""

import json
import math
import uuid
import random
import pickle
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import argparse
from typing import Dict, List, Set, Tuple, Any, Optional

# Scoring rules
PANGRAM_BONUS = 10
BINGO_BONUS = 10
MIN_WORD_LENGTH = 4
MIN_WORDS_PER_PUZZLE = 30
MAX_WORDS_PER_PUZZLE = 60
MIN_PANGRAMS = 1
MAX_PANGRAMS = 6
DAYS_WITHOUT_REPETITION = 30
NUM_PUZZLES = 180
WORD_COUNT_TARGET = 45   # ideal midpoint for center letter selection

# Anchor word quality thresholds
MIN_ANCHOR_FREQ = 500
MAX_ANCHOR_FREQ = 500_000
MIN_ANCHOR_LENGTH = 7
VOWEL_CENTER_MAX_RATIO = 0.65
VOWEL_CENTER_MIN_RATIO = 0.35
VOWELS = set('aeiou')

# Suffixes that disqualify a word from being an anchor (derived/inflected forms)
ANCHOR_EXCLUDE_SUFFIXES = [
    'ing', 'tion', 'ation', 'ness', 'ment', 'ful', 'ive',
    'able', 'ible', 'ical', 'ize', 'ify', 'ed', 'er'
]


def load_dictionary(file_path: str) -> Dict[str, int]:
    """Load dictionary from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def load_word_frequencies(freq_file: str = 'word_frequency.pkl') -> Dict[str, int]:
    """Load word frequency data from pickle file."""
    try:
        with open(freq_file, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}


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


def calculate_morphological_diversity(valid_words: List[str]) -> float:
    """
    Ratio of unique word families to total words.
    1.0 = every word is from a unique family (best).
    Lower = many inflected variants of the same base (worse).
    """
    SUFFIXES = [
        'ings', 'ations', 'nesses', 'ments',
        'ing', 'ation', 'ness', 'ment',
        'ers', 'ied', 'ies', 'est',
        'ed', 'er', 'es', 'ly', 's'
    ]
    MIN_BASE_LENGTH = 3

    family_roots = {}
    for word in valid_words:
        base = word
        for suffix in SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= MIN_BASE_LENGTH:
                candidate = word[:-len(suffix)]
                # Normalize doubled consonants: 'running' -> 'run'
                if (len(candidate) > 2 and
                        candidate[-1] == candidate[-2] and
                        candidate[-1] not in 'aeiou'):
                    candidate = candidate[:-1]
                base = candidate
                break
        family_roots[word] = base

    families = defaultdict(set)
    for word, base in family_roots.items():
        families[base].add(word)

    return len(families) / len(valid_words) if valid_words else 0.0


def freq_score(freq: int) -> float:
    """
    Score a word's frequency on a 0-1 scale peaking around 5,000 occurrences.
    Penalizes words that are too obscure or too trivially common.
    """
    if freq <= 0:
        return 0.0
    log_f = math.log10(freq)
    peak = 3.7    # log10(5000) — recognizable but not trivially common
    width = 1.5
    return max(0.0, 1.0 - ((log_f - peak) / width) ** 2)


def anchor_length_score(word: str) -> float:
    """Score a word's length for use as an anchor. 8-letter words are ideal."""
    l = len(word)
    if l <= 7:   return 0.60
    if l == 8:   return 1.00
    if l == 9:   return 0.95
    if l == 10:  return 0.85
    if l == 11:  return 0.70
    return 0.50


def is_anchor_derived(word: str) -> bool:
    """Return True if the word ends in a derivational suffix (disqualifies as anchor)."""
    MIN_BASE_LENGTH = 4
    for suffix in ANCHOR_EXCLUDE_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_BASE_LENGTH:
            return True
    return False


def find_anchor_candidates(
    dictionary: Dict[str, int],
    word_freq: Dict[str, int]
) -> List[Tuple[str, float]]:
    """
    Find all words suitable to anchor a puzzle, sorted by quality score.

    An anchor word must:
    - Have exactly 7 unique letters (is a potential pangram)
    - Contain no 'S' (prevents plurals as outside letters)
    - Be long enough to be interesting (>= MIN_ANCHOR_LENGTH)
    - Have a frequency in the recognizable-but-satisfying range
    - Not be a derivational form (no -ing, -ed, -tion, etc.)
    """
    candidates = []
    for word in dictionary:
        if len(word) < MIN_ANCHOR_LENGTH:
            continue
        if len(set(word)) != 7:
            continue
        if 's' in word:
            continue
        if is_anchor_derived(word):
            continue
        freq = word_freq.get(word, 0)
        if freq < MIN_ANCHOR_FREQ or freq > MAX_ANCHOR_FREQ:
            continue
        score = freq_score(freq) * 0.5 + anchor_length_score(word) * 0.5
        candidates.append((word, score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates


def select_center_letter(
    dictionary: Dict[str, int],
    letters: Set[str],
    force_center: Optional[str] = None
) -> Optional[Tuple[str, List[str]]]:
    """
    Choose the best center letter for a letter set targeting WORD_COUNT_TARGET words.

    If force_center is given (e.g. 's'), only that letter is tried.
    Prefers vowel centers, then consonant centers.
    Returns (center, valid_words) or None if no letter produces a valid word count.
    """
    vowel_options = []
    consonant_options = []

    candidates = [force_center] if force_center else list(letters)

    for center in candidates:
        words = get_valid_words(dictionary, center, letters)
        count = len(words)
        if MIN_WORDS_PER_PUZZLE <= count <= MAX_WORDS_PER_PUZZLE:
            bucket = vowel_options if center in VOWELS else consonant_options
            bucket.append((center, count, words))

    for bucket in (vowel_options, consonant_options):
        if bucket:
            center, _, words = min(bucket, key=lambda x: abs(x[1] - WORD_COUNT_TARGET))
            return center, words

    return None


def generate_puzzles(dictionary: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Generate puzzle sets using a pangram-first approach.

    Each puzzle is anchored to an interesting 7-unique-letter word. That word's
    letters define the puzzle. The center is chosen to hit the target word count.
    S is excluded as an outside letter — letter sets containing S only proceed
    when S is used as the center letter.
    """
    word_freq = load_word_frequencies()
    anchor_candidates = find_anchor_candidates(dictionary, word_freq)
    print(f"Found {len(anchor_candidates)} anchor candidates")

    all_puzzles = []
    seen_letter_sets: Set[frozenset] = set()
    vowel_count = 0

    for anchor_word, anchor_score in anchor_candidates:
        letters = set(anchor_word)
        lset = frozenset(letters)

        if lset in seen_letter_sets:
            continue
        seen_letter_sets.add(lset)

        # S is excluded as an outside letter. If the anchor has no S, try all
        # center letters freely. Anchors with S are already excluded by
        # find_anchor_candidates(), so this block handles S-center puzzles
        # sourced from a separate pool if needed — currently not used.
        result = select_center_letter(dictionary, letters)
        if result is None:
            continue

        center, valid_words = result

        # Quality gates
        pangrams = get_pangrams(valid_words, letters)
        if len(pangrams) < MIN_PANGRAMS or len(pangrams) > MAX_PANGRAMS:
            continue

        diversity = calculate_morphological_diversity(valid_words)
        if diversity < 0.70:
            continue

        long_words = sum(1 for w in valid_words if len(w) >= 6)
        if long_words / len(valid_words) < 0.20:
            continue

        # Vowel/consonant balance gate (applied after warmup)
        is_vowel_center = center in VOWELS
        tentative_ratio = (vowel_count + is_vowel_center) / (len(all_puzzles) + 1)
        if len(all_puzzles) > 20:
            if is_vowel_center and tentative_ratio > VOWEL_CENTER_MAX_RATIO:
                continue
            if not is_vowel_center and tentative_ratio < VOWEL_CENTER_MIN_RATIO:
                continue

        if is_vowel_center:
            vowel_count += 1

        # Composite puzzle quality score (used for final ranking/logging)
        word_count_score = 1.0 - abs(len(valid_words) - WORD_COUNT_TARGET) / WORD_COUNT_TARGET
        puzzle_score = anchor_score * 0.4 + diversity * 0.3 + word_count_score * 0.3

        outside_letters = list(letters - {center})
        has_bingo = check_bingo(valid_words, list(letters))
        total_score = calculate_total_score(valid_words, letters, has_bingo)

        all_puzzles.append({
            'id': str(uuid.uuid4())[:8],
            'last_reviewed': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'live_date': None,
            'center_letter': center,
            'outside_letters': outside_letters,
            'anchor_word': anchor_word,
            'pangrams': pangrams,
            'bingo_possible': has_bingo,
            'total_score': total_score,
            'total_words': len(valid_words),
            'valid_words': sorted(valid_words),
            '_puzzle_score': puzzle_score,
        })

        if len(all_puzzles) >= NUM_PUZZLES:
            break

    # Log center letter distribution
    center_counts = Counter(p['center_letter'] for p in all_puzzles)
    print("Center letter distribution:")
    for letter, count in sorted(center_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {letter}: {count} puzzles ({count/len(all_puzzles)*100:.1f}%)")

    # Clean up internal scoring keys
    for puzzle in all_puzzles:
        puzzle.pop('_puzzle_score', None)

    # Shuffle to remove correlation between puzzle quality and live date
    random.shuffle(all_puzzles)

    # Set live dates
    start_date = datetime.now().date()
    for i, puzzle in enumerate(all_puzzles):
        puzzle['live_date'] = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')

    return all_puzzles


def main():
    """Main function to run the generator."""
    parser = argparse.ArgumentParser(description='Generate Spelling Bee puzzle sets')
    parser.add_argument('--input', default='filtered_12dictionary_40k.json',
                        help='Input dictionary file path')
    parser.add_argument('--output', default='puzzle_sets.json',
                        help='Output puzzle sets file path')
    parser.add_argument('--freq', default='word_frequency.pkl',
                        help='Word frequency pickle file path')
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
    print(f"Average long words (6+): {sum(sum(1 for w in p['valid_words'] if len(w) >= 6) for p in puzzle_sets) / len(puzzle_sets):.2f}")

    s_outside = sum(1 for p in puzzle_sets if 's' in p['outside_letters'])
    s_center = sum(1 for p in puzzle_sets if p['center_letter'] == 's')
    diversities = [calculate_morphological_diversity(p['valid_words']) for p in puzzle_sets]
    avg_diversity = sum(diversities) / len(diversities)
    print(f"S as center letter: {s_center} ({s_center/len(puzzle_sets)*100:.1f}%)")
    print(f"S as outside letter: {s_outside} ({s_outside/len(puzzle_sets)*100:.1f}%)")
    print(f"Average morphological diversity: {avg_diversity:.3f}")
    print(f"Puzzles below 0.75 diversity: {sum(1 for d in diversities if d < 0.75)}")


if __name__ == "__main__":
    main()
