import json
import random
import string
import uuid
import argparse
from typing import List, Dict, Set, Tuple
from collections import Counter
import math
import statistics
from datetime import datetime
import os

# Common English letter frequencies (source: Cornell Language Lab)
LETTER_FREQUENCIES = {
    'e': 12.02, 't': 9.10, 'a': 8.12, 'o': 7.68, 'i': 7.31, 'n': 6.95, 's': 6.28,
    'r': 6.02, 'h': 5.92, 'd': 4.32, 'l': 3.98, 'u': 2.88, 'c': 2.71, 'm': 2.61,
    'f': 2.30, 'y': 2.11, 'w': 2.09, 'g': 2.03, 'p': 1.82, 'b': 1.49, 'v': 1.11,
    'k': 0.69, 'x': 0.17, 'q': 0.11, 'j': 0.10, 'z': 0.07
}

# Vowels and common consonants for better word formation
VOWELS = set('aeiou')
COMMON_CONSONANTS = set('rstlndhc')

# Target ranges for optimal puzzle characteristics
IDEAL_WORD_COUNT_RANGE = (30, 80)  # More focused range for engaging puzzles
IDEAL_PANGRAM_COUNT_RANGE = (1, 3)  # Ideal number of pangrams
MIN_FOUR_LETTER_WORDS = 5  # Minimum number of 4-letter words for easier start
MAX_WORD_LENGTH = 16  # Maximum word length for reasonable playability

def load_dictionary(dictionary_path: str) -> Dict[str, int]:
    """Load dictionary and filter out rejected words from word cache."""
    # Load word cache first
    word_cache = {}
    if os.path.exists('word_cache.json'):
        try:
            with open('word_cache.json', 'r') as f:
                word_cache = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Could not load word cache")
    
    rejected_words = set(word_cache.get('rejected', []))
    
    # Load and filter dictionary
    with open(dictionary_path, 'r') as f:
        dictionary = json.load(f)
        # Remove rejected words from dictionary
        return {word: freq for word, freq in dictionary.items() 
                if word not in rejected_words}

def is_valid_word(word: str, center: str, letters: Set[str], min_length: int = 4) -> bool:
    """Check if word is valid for the puzzle and not in rejected list."""
    if len(word) < min_length or len(word) > MAX_WORD_LENGTH:
        return False
    if center not in word:
        return False
    allowed_letters = letters | {center}
    return all(c in allowed_letters for c in word)

def score_word_familiarity(word: str) -> float:
    """Enhanced scoring system for word familiarity."""
    # Penalize very long words more gradually
    length_penalty = max(0, (len(word) - 8) * 0.1)
    
    # Calculate letter frequency score
    letter_freq_score = sum(LETTER_FREQUENCIES[c] for c in word) / len(word)
    
    # Bonus for words with common prefixes/suffixes
    common_prefixes = {'re', 'un', 'in', 'dis'}
    common_suffixes = {'ing', 'ed', 'er', 'est'}
    prefix_bonus = 0.2 if any(word.startswith(p) for p in common_prefixes) else 0
    suffix_bonus = 0.2 if any(word.endswith(s) for s in common_suffixes) else 0
    
    return letter_freq_score - length_penalty + prefix_bonus + suffix_bonus

def score_word(word: str, is_pangram: bool = False) -> int:
    """Enhanced scoring system for better gameplay progression."""
    length = len(word)
    if length == 4:
        return 1
    elif length == 5:
        return 5
    else:
        # Bonus points for longer words
        length_bonus = length + math.floor(length / 3)  # Extra points every 3 letters
        pangram_bonus = 15 if is_pangram else 0  # Increased pangram bonus
        return length_bonus + pangram_bonus

def has_bingo(words: List[str], letters: Set[str]) -> bool:
    starting_letters = {word[0] for word in words}
    return all(letter in starting_letters for letter in letters)

def find_valid_words(dictionary: Dict[str, int], center: str, letters: Set[str]) -> List[str]:
    valid = []
    for word in dictionary:
        if is_valid_word(word, center, letters):
            valid.append(word)
    return valid

def is_pangram(word: str, center: str, letters: Set[str]) -> bool:
    return all(letter in word for letter in (letters | {center}))

def evaluate_puzzle_quality(valid_words: List[str], pangrams: List[str], center: str, letters: Set[str]) -> float:
    """Enhanced puzzle quality evaluation with more factors."""
    if not valid_words:
        return 0.0
    
    # Word count score - relaxed ideal range
    word_count = len(valid_words)
    if 15 <= word_count <= IDEAL_WORD_COUNT_RANGE[1]:  # Reduced minimum from IDEAL_WORD_COUNT_RANGE[0]
        word_count_score = 1.0
    else:
        word_count_score = max(0.4, 1.0 - abs(word_count - sum(IDEAL_WORD_COUNT_RANGE)/2) / 100)
    
    # Word length distribution score
    length_counts = Counter(len(word) for word in valid_words)
    length_variety = len(length_counts) / 8  # Normalize by expected variety
    
    # Four-letter word score (ensure enough easy starting words)
    four_letter_ratio = length_counts.get(4, 0) / word_count
    four_letter_score = min(1.0, four_letter_ratio * 4)  # Reduced from *5 to *4, making it easier to achieve
    
    # Pangram quality - restored original scoring but simplified
    pangram_count = len(pangrams)
    if pangram_count >= 1:
        pangram_score = 1.0
    else:
        pangram_score = 0.0  # No pangrams means zero score for this component
    
    # Letter distribution score - more lenient
    letter_usage = Counter(''.join(valid_words))
    usage_balance = statistics.stdev(letter_usage.values()) / statistics.mean(letter_usage.values())
    distribution_score = 1.0 / (1.0 + usage_balance)  # Lower variance is better
    
    # Combine scores with adjusted weights - restored pangram importance
    quality_score = (
        word_count_score * 0.30 +
        length_variety * 0.20 +
        four_letter_score * 0.20 +
        pangram_score * 0.20 +  # Restored higher weight for pangrams
        distribution_score * 0.10
    )
    
    return quality_score

def select_letters() -> Tuple[str, List[str]]:
    """Enhanced letter selection for better puzzle formation.
    Returns a tuple of (center_letter, outside_letters) where:
    - All letters are unique
    - Total of exactly 7 letters
    - 2-3 vowels included
    - Some common consonants included
    - Favors combinations likely to form 1-3 pangrams
    """
    # Common letter combinations that tend to work well in puzzles
    COMMON_PAIRS = ['th', 'st', 'ch', 'sh', 'tr', 'pl', 'cl']
    COMMON_ENDINGS = ['ing', 'er', 'ed', 'es']
    
    # Try multiple attempts to find good letter combinations
    for _ in range(10):
        remaining = set(string.ascii_lowercase)
        outside_letters = []
        
        # First, select 2-3 vowels with preference for common ones
        available_vowels = sorted(list(VOWELS & remaining), 
                                key=lambda x: LETTER_FREQUENCIES[x], 
                                reverse=True)
        num_vowels = random.randint(2, 3)
        selected_vowels = available_vowels[:num_vowels]
        
        outside_letters.extend(selected_vowels)
        remaining -= set(selected_vowels)
        
        # Try to include one common pair for word formation
        selected_pair = random.choice(COMMON_PAIRS)
        pair_letters = set(selected_pair) - set(outside_letters)
        if len(pair_letters) > 0 and len(outside_letters) + len(pair_letters) <= 6:
            new_letters = list(pair_letters)[:6-len(outside_letters)]
            outside_letters.extend(new_letters)
            remaining -= set(new_letters)
        
        # Try to include letters from a common ending if space allows
        if len(outside_letters) < 5:  # Leave room for at least one more letter
            selected_ending = random.choice(COMMON_ENDINGS)
            ending_letters = set(selected_ending) - set(outside_letters)
            if ending_letters and len(outside_letters) + len(ending_letters) <= 6:
                new_letters = list(ending_letters)[:6-len(outside_letters)]
                outside_letters.extend(new_letters)
                remaining -= set(new_letters)
        
        # Fill remaining slots with common consonants and frequent letters
        while len(outside_letters) < 6:
            # Prioritize common consonants if available
            available = remaining & COMMON_CONSONANTS
            if not available:
                # Fall back to most frequent remaining letters
                available = remaining
            
            if not available:
                break
                
            best_letter = max(available, key=lambda x: LETTER_FREQUENCIES[x])
            outside_letters.append(best_letter)
            remaining.remove(best_letter)
        
        # If we don't have 6 letters yet, something went wrong
        if len(outside_letters) != 6:
            continue
            
        # For center letter, prefer common consonants that work well as centers
        center_candidates = remaining & (COMMON_CONSONANTS | VOWELS)
        if not center_candidates:
            center_candidates = remaining
        if not center_candidates:
            continue
            
        center = max(center_candidates, key=lambda x: LETTER_FREQUENCIES[x])
        
        # Verify we have exactly 7 unique letters
        all_letters = set(outside_letters) | {center}
        if len(all_letters) == 7:
            return center, sorted(outside_letters)
    
    # If we couldn't find a good combination after multiple attempts,
    # fall back to simple random selection of unique letters
    remaining = set(string.ascii_lowercase)
    all_letters = set(random.sample(list(remaining), 7))
    center = random.choice(list(all_letters))
    outside_letters = sorted(list(all_letters - {center}))
    return center, outside_letters

def generate_puzzle(dictionary: Dict[str, int], max_words: int = 400, min_quality: float = 0.5) -> Dict:
    """Generate a puzzle with characteristics good for Spelling Bee gameplay:
    - 2-6 pangrams
    - Natural word count (typically 20-150 words)
    - Good mix of easy and challenging words
    - All letters should be useful
    """
    attempts = 0
    best_puzzle = None
    best_quality = 0.0
    max_attempts = 30
    
    while attempts < max_attempts:
        attempts += 1
        if attempts % 10 == 0 and attempts < max_attempts:
            print(".", end='', flush=True)
            
        # Select letters using frequency analysis
        center, outside_letters = select_letters()
        letters_set = set(outside_letters)
        
        # Find valid words
        valid_words = find_valid_words(dictionary, center, letters_set)
        
        # Quick validation for word count - aim for good gameplay range
        word_count = len(valid_words)
        if word_count < 20:  # Too few words isn't fun
            continue
        if word_count > 150:  # Cap at 150 words for manual review
            continue
            
        # Check pangrams - allow 2-6 pangrams for variety
        pangrams = [word for word in valid_words if is_pangram(word, center, letters_set)]
        if not (2 <= len(pangrams) <= 6):  # Wider range for manual curation
            continue
            
        # Ensure we have enough starter words (4-5 letters)
        short_words = [w for w in valid_words if len(w) <= 5]
        if len(short_words) < 5:  # Need some easier words
            continue
            
        # Check letter utility - each letter should be used in multiple words
        letter_usage = Counter(''.join(valid_words))
        min_letter_usage = min(letter_usage[l] for l in (letters_set | {center}))
        if min_letter_usage < 3:  # Each letter should be useful in at least 3 words
            continue
            
        # Evaluate puzzle quality
        quality = evaluate_puzzle_quality(valid_words, pangrams, center, letters_set)
        
        # Update best puzzle if this is better
        if quality > best_quality:
            best_quality = quality
            
            # Calculate scores
            total_score = 0
            for word in valid_words:
                is_pangram_word = word in pangrams
                total_score += score_word(word, is_pangram_word)
            
            # Add bonus for bingo
            bingo_possible = has_bingo(valid_words, letters_set | {center})
            if bingo_possible:
                total_score += 10

            best_puzzle = {
                "id": str(uuid.uuid4())[:8],
                "center_letter": center,
                "outside_letters": outside_letters,
                "pangrams": pangrams,
                "bingo_possible": bingo_possible,
                "total_score": total_score,
                "total_words": len(valid_words),
                "valid_words": sorted(valid_words)
            }
            
            # Accept good enough puzzles with moderate quality threshold
            if quality >= min_quality * 0.8:
                return best_puzzle
    
    # If we found any puzzle, return it
    if best_puzzle is not None:
        return best_puzzle
        
    raise ValueError("Could not generate a valid puzzle after maximum attempts")

def main():
    parser = argparse.ArgumentParser(description='Generate word puzzles from a dictionary file')
    parser.add_argument('dictionary_path', help='Path to the dictionary JSON file')
    parser.add_argument('--num-puzzles', type=int, default=180, help='Number of puzzles to generate (default: 180)')
    parser.add_argument('--max-words', type=int, default=400, help='Maximum number of words allowed in a puzzle (default: 400)')
    parser.add_argument('--min-quality', type=float, default=0.65, help='Minimum quality score for puzzles (default: 0.65)')
    parser.add_argument('--output', type=str, help='Output file path base name (default: puzzle_sets)')
    args = parser.parse_args()
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = args.output if args.output else "puzzle_sets"
    output_file = f"{output_base}_{timestamp}.json"
    
    print(f"Loading dictionary from {args.dictionary_path}...")
    
    try:
        dictionary = load_dictionary(args.dictionary_path)
        print(f"Loaded {len(dictionary)} words from dictionary")
    except FileNotFoundError:
        print(f"Error: Could not find dictionary file at {args.dictionary_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: The file at {args.dictionary_path} is not a valid JSON file")
        return
    
    print(f"\nGenerating {args.num_puzzles} puzzles...")
    puzzles = []
    previous_letters = []  # Track last N puzzles' letters
    max_history = 5  # Reduced from 10 to 5 to allow more letter combinations
    max_similarity = 4  # Allow up to 4 letters in common
    
    for i in range(args.num_puzzles):
        if i > 0 and i % 10 == 0:
            print(f"\nProgress: {i}/{args.num_puzzles}")
        else:
            print(".", end='', flush=True)
            
        attempts = 0
        puzzle_generated = False
        
        while attempts < 10 and not puzzle_generated:  # Limit similarity check attempts
            try:
                puzzle = generate_puzzle(dictionary, args.max_words, args.min_quality)
                current_letters = set(puzzle['outside_letters']) | {puzzle['center_letter']}
                
                # Check similarity with recent puzzles
                is_too_similar = False
                for prev_letters in previous_letters:
                    if len(current_letters & prev_letters) > max_similarity:
                        is_too_similar = True
                        break
                
                if not is_too_similar or attempts >= 5:  # Accept similar puzzles after 5 attempts
                    puzzles.append(puzzle)
                    previous_letters.append(current_letters)
                    if len(previous_letters) > max_history:
                        previous_letters.pop(0)
                    puzzle_generated = True
                
            except ValueError:
                pass  # Continue trying if puzzle generation fails
            
            attempts += 1
        
        if not puzzle_generated:
            print("x", end='', flush=True)  # Mark failed attempts with x
            # Try one last time without similarity check
            puzzle = generate_puzzle(dictionary, args.max_words, args.min_quality)
            puzzles.append(puzzle)
            current_letters = set(puzzle['outside_letters']) | {puzzle['center_letter']}
            previous_letters.append(current_letters)
            if len(previous_letters) > max_history:
                previous_letters.pop(0)
    
    print("\n\nPuzzle Generation Complete!")
    print(f"Saving {len(puzzles)} puzzles to {output_file}")
    
    # Save puzzles to file
    with open(output_file, 'w') as f:
        json.dump(puzzles, f, indent=2)
    
    # Print statistics
    total_words = sum(p['total_words'] for p in puzzles)
    avg_words = total_words / len(puzzles)
    avg_score = sum(p['total_score'] for p in puzzles) / len(puzzles)
    avg_pangrams = sum(len(p['pangrams']) for p in puzzles) / len(puzzles)
    
    print(f"\nPuzzle Statistics:")
    print(f"Average words per puzzle: {avg_words:.1f}")
    print(f"Average score per puzzle: {avg_score:.1f}")
    print(f"Average pangrams per puzzle: {avg_pangrams:.1f}")

if __name__ == "__main__":
    main() 