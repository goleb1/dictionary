import json
from collections import Counter
import random
from datetime import datetime
import nltk
from nltk.tag import pos_tag
from nltk.corpus import names
import logging
import string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download all required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)
nltk.download('names', quiet=True)

# Initialize counters for each filter reason
filter_counts = Counter()

# Load name lists for proper noun detection
male_names = set(name.lower() for name in names.words('male.txt'))
female_names = set(name.lower() for name in names.words('female.txt'))
all_names = male_names | female_names

# Common month names, days, and other proper nouns we want to filter
common_proper_nouns = {
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december'
}

def load_full_dictionary():
    with open('dictionary.json', 'r') as f:
        return json.load(f)

def count_unique_letters(word):
    return len(set(word.lower()))

def is_proper_noun(word):
    word_lower = word.lower()
    
    # Check against our known name lists
    if word_lower in all_names:
        logger.debug(f"Word '{word}' found in names list")
        return True
        
    # Check against common proper nouns
    if word_lower in common_proper_nouns:
        logger.debug(f"Word '{word}' found in common proper nouns list")
        return True
    
    # Use NLTK's POS tagger with multiple checks
    try:
        # Always check both lowercase and capitalized versions
        tokens_lower = nltk.word_tokenize(word_lower)
        tokens_cap = nltk.word_tokenize(word.capitalize())
        
        # Get POS tags for both versions
        pos_lower = pos_tag(tokens_lower)
        pos_cap = pos_tag(tokens_cap)
        
        # Check if either version is tagged as a proper noun
        if (pos_lower[0][1] in ['NNP', 'NNPS'] or 
            pos_cap[0][1] in ['NNP', 'NNPS']):
            logger.debug(f"Word '{word}' identified as proper noun by POS tagger")
            return True
            
    except Exception as e:
        logger.debug(f"Error in POS tagging for word '{word}': {str(e)}")
    
    # Additional heuristics
    # Check if word looks like an initial (single letter followed by period)
    if len(word) == 2 and word[1] == '.':
        return True
        
    # Check for common name endings
    name_endings = ['son', 'ton', 'land', 'burg', 'ville', 'berg', 'shire']
    if any(word_lower.endswith(ending) for ending in name_endings):
        return True
        
    # Additional checks for common first names and place names
    # This helps catch proper nouns that NLTK might miss
    if word_lower in male_names or word_lower in female_names:
        return True
        
    # Add more common place name endings
    place_endings = ['ia', 'stan', 'istan', 'burgh', 'town', 'city', 'port']
    if any(word_lower.endswith(ending) for ending in place_endings):
        return True
    
    return False

def has_uncommon_patterns(word):
    """Check for patterns that typically indicate obscure words."""
    word = word.lower()
    
    # Uncommon suffixes often found in technical/scientific terms
    uncommon_suffixes = [
        'ation', 'mania', 'onia', 'osis', 'itis', 'otic',
        'oid', 'iac', 'ium', 'yne', 'ase'  # Removed common suffixes like 'ate', 'ine', etc.
    ]
    if any(word.endswith(suffix) for suffix in uncommon_suffixes):
        filter_counts['uncommon_suffix'] += 1
        return True

    # Uncommon prefixes often found in technical/scientific terms
    uncommon_prefixes = [
        'poly', 'mono', 'meta', 'para', 'hypo', 'hyper',
        'iso', 'neo', 'bio', 'geo', 'theo', 'proto', 'pseudo',
        'trans', 'ultra', 'quad', 'multi'  # Removed common prefixes like 'anti', 'uni', 'tri'
    ]
    if any(word.startswith(prefix) for prefix in uncommon_prefixes):
        filter_counts['uncommon_prefix'] += 1
        return True
        
    # Check for repetitive syllables (e.g., "tootmoot")
    for i in range(len(word)-1):
        if word[i:i+2] == word[i+2:i+4] and len(word[i:i+2].strip()) > 0:
            filter_counts['repetitive_syllables'] += 1
            return True
            
    # Check for uncommon letter combinations
    uncommon_combos = [
        'mn', 'tm', 'aeo', 'uu', 'ii', 'uo',  # Removed common combinations like 'nn', 'mm', 'io'
        'phth', 'thm', 'chth', 'rh', 'zh',
        'eau', 'oeu', 'ieu', 'rrh', 'chm', 'zz', 'cq', 'kh'
    ]
    if any(combo in word for combo in uncommon_combos):
        filter_counts['uncommon_letter_combo'] += 1
        return True

    # Words with too many vowels in a row
    vowels = 'aeiou'
    vowel_count = 0
    for char in word:
        if char in vowels:
            vowel_count += 1
            if vowel_count > 3:  # Changed from 2 to 3 vowels in a row
                filter_counts['too_many_vowels'] += 1
                return True
        else:
            vowel_count = 0
        
    # Words with too many consonants in a row
    consonants = 'bcdfghjklmnpqrstvwxz'
    consonant_count = 0
    for char in word:
        if char in consonants:
            consonant_count += 1
            if consonant_count > 4:  # Changed from 3 to 4 consonants in a row
                filter_counts['too_many_consonants'] += 1
                return True
        else:
            consonant_count = 0

    # Check vowel to consonant ratio
    vowel_count = sum(1 for c in word if c in vowels)
    consonant_count = sum(1 for c in word if c in consonants)
    if vowel_count > 0 and consonant_count > 0:
        ratio = vowel_count / consonant_count
        if ratio > 0.9 or ratio < 0.15:  # Made ratio more lenient (was 0.8 and 0.2)
            filter_counts['unusual_letter_ratio'] += 1
            return True

    # Check for words ending in uncommon combinations
    uncommon_endings = [
        'eum', 'uum', 'rrh', 'chm', 'thm', 'phth',
        'pth', 'dth', 'tzt', 'tz'  # Removed common endings like 'ght', 'mpt', 'tch', 'nth'
    ]
    if any(word.endswith(ending) for ending in uncommon_endings):
        filter_counts['uncommon_ending'] += 1
        return True

    return False

def load_obscure_words():
    """Load the list of known obscure words."""
    try:
        with open('obscure_words.json', 'r') as f:
            data = json.load(f)
            # Handle both old dictionary format and new list format
            if isinstance(data, dict):
                # Flatten all word lists into a single set
                return {word.lower() for word_list in data.values() for word in word_list}
            else:
                return {word.lower() for word in data}
    except FileNotFoundError:
        logger.warning("obscure_words.json not found, skipping obscure word filtering")
        return set()

def is_valid_word(word):
    # Check if word has at least 4 letters
    if len(word) < 4:
        return False
    
    # Check if word has more than 7 unique letters
    if len(set(word)) > 7:
        return False
    
    # Check for spaces or punctuation
    if any(c in string.punctuation or c.isspace() for c in word):
        return False
    
    return True

def main():
    # Initialize counters for filtering statistics
    filter_stats = {
        'too_short': 0,
        'too_many_unique': 0,
        'non_alpha': 0
    }
    word_lengths = Counter()
    
    # Read and process input file
    all_words = []
    with open('3of6game.txt', 'r') as f:
        all_words = [line.strip().lower() for line in f]
    
    original_size = len(all_words)
    filtered_words = {}
    
    # Process each word and collect statistics
    for word in all_words:
        # Track filter reasons
        if len(word) < 4:
            filter_stats['too_short'] += 1
            continue
        if len(set(word)) > 7:
            filter_stats['too_many_unique'] += 1
            continue
        if any(c in string.punctuation or c.isspace() for c in word):
            filter_stats['non_alpha'] += 1
            continue
            
        # Word passed all filters
        filtered_words[word] = 1
        word_lengths[len(word)] += 1
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f'filtered_dictionary_{timestamp}.json'
    
    # Write output file
    with open(output_filename, 'w') as f:
        json.dump(filtered_words, f, indent=2)
    
    # Print statistics
    print(f"\nOriginal dictionary size: {original_size} words")
    print(f"Filtered dictionary size: {len(filtered_words)} words")
    
    print("\nWords filtered by reason:")
    print(f"  - <4 letters: {filter_stats['too_short']}")
    print(f"  - >7 unique letters: {filter_stats['too_many_unique']}")
    print(f"  - non-alpha characters: {filter_stats['non_alpha']}")
    
    print("\nWord length distribution:")
    for length in sorted(word_lengths.keys()):
        print(f"{length} letters: {word_lengths[length]:,} words")
    
    print(f"\nFiltered dictionary saved to '{output_filename}'")

if __name__ == "__main__":
    main() 