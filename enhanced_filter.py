import json
import nltk
from nltk.corpus import words as nltk_words
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from nltk.corpus import names
from collections import defaultdict, Counter
import requests
from typing import Dict, Set, List, Tuple
import logging
from pathlib import Path
import pickle
import sys
import argparse
from multiprocessing import Pool, cpu_count
from functools import partial
import time
import warnings
import urllib3
from datetime import datetime

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='.*SSL.*')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download all required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)
nltk.download('names', quiet=True)
nltk.download('wordnet', quiet=True)

class WordFilter:
    def __init__(self):
        self.initialize_data()
        self.load_word_frequencies()
        self.load_cached_data()
        self.filter_counts = Counter()
        
    def initialize_data(self):
        """Initialize all necessary data and constants."""
        # Initialize name lists for proper noun detection
        self.male_names = set(name.lower() for name in names.words('male.txt'))
        self.female_names = set(name.lower() for name in names.words('female.txt'))
        self.all_names = self.male_names | self.female_names
        
        # Common month names, days, and other proper nouns we want to filter
        self.common_proper_nouns = {
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december'
        }
        
        # Cache NLTK words set
        self.nltk_words_set = set(w.lower() for w in nltk_words.words())
        
        # Cache for WordNet results
        self.wordnet_cache = {}
        
        # Initialize pattern lists
        self.initialize_patterns()
        
    def initialize_patterns(self):
        """Initialize all pattern-based filtering lists."""
        # Common prefixes that should be treated more leniently
        self.common_prefixes = {
            'un', 're', 'in', 'out', 'over', 'under', 'up', 'down',
            'non', 'pre', 'post', 'sub', 'super', 'inter', 'anti',
            'dis', 'mis', 'en', 'em', 'fore', 'pro', 'semi', 'mid'
        }
        
        # Common suffixes that should be treated more leniently
        self.common_suffixes = {
            'ing', 'ed', 'er', 'est', 'ly', 'ness', 'ment', 'able',
            'ible', 'ful', 'less', 'ish', 'like', 'ive', 'ous',
            'al', 'ic', 'y', 'en'
        }
        
        # Uncommon suffixes often found in technical/scientific terms
        self.uncommon_suffixes = [
            'osis', 'itis', 'otic', 'oid', 'ium',
            'yne', 'ase', 'rrh', 'emia', 'genic'
        ]
        
        # Uncommon prefixes
        self.uncommon_prefixes = [
            'poly', 'mono', 'meta', 'hypo', 'hyper',
            'iso', 'neo', 'bio', 'geo', 'theo', 'proto', 'pseudo'
        ]
        
        # Uncommon letter combinations
        self.uncommon_combos = [
            'phth', 'thm', 'chth', 'rh', 'zh',
            'eau', 'oeu', 'ieu', 'rrh', 'chm', 'zz', 'cq', 'kh'
        ]
        
        # Uncommon endings
        self.uncommon_endings = [
            'eum', 'uum', 'rrh', 'chm', 'thm', 'phth',
            'pth', 'dth', 'tzt'
        ]
        
        # Place name endings for proper noun detection
        self.place_endings = [
            'ia', 'stan', 'istan', 'burgh', 'town', 'city', 'port',
            'son', 'ton', 'land', 'burg', 'ville', 'berg', 'shire'
        ]
        
    def load_word_frequencies(self):
        """Load word frequencies from cached file or download if not available."""
        freq_file = Path('word_frequency.pkl')
        if not freq_file.exists():
            logger.info("Downloading word frequency data...")
            url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_full.txt"
            try:
                response = requests.get(url, timeout=30, stream=True)
                response.raise_for_status()
                
                frequencies = {}
                total_lines = 0
                for line in response.iter_lines(decode_unicode=True):
                    if line.strip():
                        try:
                            word, freq = line.split(' ')
                            frequencies[word] = int(freq)
                            total_lines += 1
                            if total_lines % 10000 == 0:
                                logger.info(f"Processed {total_lines:,} words...")
                        except ValueError:
                            logger.warning(f"Skipping malformed line: {line}")
                
                logger.info(f"Download complete. Saving {total_lines:,} words to {freq_file}")
                with open(freq_file, 'wb') as f:
                    pickle.dump(frequencies, f)
                    
            except Exception as e:
                logger.error(f"Error with frequency data: {str(e)}")
                frequencies = {}
                
        try:
            with open(freq_file, 'rb') as f:
                self.word_frequencies = pickle.load(f)
            logger.info(f"Loaded {len(self.word_frequencies):,} word frequencies")
        except:
            logger.warning("Using empty frequency dictionary")
            self.word_frequencies = {}
            
    def load_cached_data(self):
        """Load cached word decisions."""
        try:
            with open('word_cache.json', 'r') as f:
                cache_data = json.load(f)
                self.word_cache = {
                    'accepted': set(cache_data.get('accepted', [])),
                    'rejected': set(cache_data.get('rejected', [])),
                    'pending_review': set(cache_data.get('pending_review', []))
                }
        except FileNotFoundError:
            self.word_cache = {
                'accepted': set(),
                'rejected': set(),
                'pending_review': set()
            }
            
    def save_cached_data(self):
        """Save word cache to file."""
        with open('word_cache.json', 'w') as f:
            json.dump({
                'accepted': list(self.word_cache['accepted']),
                'rejected': list(self.word_cache['rejected']),
                'pending_review': list(self.word_cache['pending_review'])
            }, f, indent=2)
            
    def is_proper_noun(self, word: str) -> bool:
        """Enhanced proper noun detection combining both approaches."""
        word_lower = word.lower()
        
        # Check cached decisions
        if word_lower in self.word_cache['accepted']:
            return False
        if word_lower in self.word_cache['rejected']:
            return True
            
        # Check against name lists
        if word_lower in self.all_names:
            return True
            
        # Check against common proper nouns
        if word_lower in self.common_proper_nouns:
            return True
            
        # Check WordNet for common noun usage
        if bool(wordnet.synsets(word_lower)):
            # If it has common noun meanings, it's not exclusively a proper noun
            return False
            
        # Use NLTK's POS tagger
        try:
            tokens_lower = nltk.word_tokenize(word_lower)
            tokens_cap = nltk.word_tokenize(word.capitalize())
            
            pos_lower = pos_tag(tokens_lower)
            pos_cap = pos_tag(tokens_cap)
            
            if (pos_lower[0][1] in ['NNP', 'NNPS'] or 
                pos_cap[0][1] in ['NNP', 'NNPS']):
                return True
                
        except Exception:
            pass
            
        # Check for place name endings
        if any(word_lower.endswith(ending) for ending in self.place_endings):
            return True
            
        return False
        
    def has_uncommon_patterns(self, word: str) -> bool:
        """Check for patterns that typically indicate obscure words."""
        word = word.lower()
        
        # Check suffixes
        if any(word.endswith(suffix) for suffix in self.uncommon_suffixes):
            self.filter_counts['uncommon_suffix'] += 1
            return True
            
        # Check prefixes
        if any(word.startswith(prefix) for prefix in self.uncommon_prefixes):
            self.filter_counts['uncommon_prefix'] += 1
            return True
            
        # Check for repetitive syllables
        for i in range(len(word)-1):
            if word[i:i+2] == word[i+2:i+4] and len(word[i:i+2].strip()) > 0:
                self.filter_counts['repetitive_syllables'] += 1
                return True
                
        # Check letter combinations
        if any(combo in word for combo in self.uncommon_combos):
            self.filter_counts['uncommon_letter_combo'] += 1
            return True
            
        # Check vowel patterns
        vowels = 'aeiou'
        vowel_count = 0
        for char in word:
            if char in vowels:
                vowel_count += 1
                if vowel_count > 3:
                    self.filter_counts['too_many_vowels'] += 1
                    return True
            else:
                vowel_count = 0
                
        # Check consonant patterns
        consonants = 'bcdfghjklmnpqrstvwxz'
        consonant_count = 0
        for char in word:
            if char in consonants:
                consonant_count += 1
                if consonant_count > 4:
                    self.filter_counts['too_many_consonants'] += 1
                    return True
            else:
                consonant_count = 0
                
        # Check vowel/consonant ratio
        total_vowels = sum(1 for c in word if c in vowels)
        total_consonants = sum(1 for c in word if c in consonants)
        if total_vowels > 0 and total_consonants > 0:
            ratio = total_vowels / total_consonants
            if ratio > 0.9 or ratio < 0.15:
                self.filter_counts['unusual_letter_ratio'] += 1
                return True
                
        # Check endings
        if any(word.endswith(ending) for ending in self.uncommon_endings):
            self.filter_counts['uncommon_ending'] += 1
            return True
            
        return False
        
    def get_word_score(self, word: str) -> float:
        """Calculate a composite score for word commonness/validity."""
        word = word.lower()
        
        # Start with base score
        score = 1.0
        
        # Factor in word frequency with higher weight
        if word in self.word_frequencies:
            freq = self.word_frequencies[word]
            freq_score = min(1.0, freq / 10000)  # More lenient frequency threshold
            score *= (0.6 + 0.4 * freq_score)  # Increased base score for known words
        else:
            score *= 0.5
        
        # Check for common prefixes and suffixes
        has_common_prefix = any(word.startswith(prefix) for prefix in self.common_prefixes)
        has_common_suffix = any(word.endswith(suffix) for suffix in self.common_suffixes)
        
        # Boost score for words with common affixes
        if has_common_prefix:
            score *= 1.2
        if has_common_suffix:
            score *= 1.2
            
        # Check if it's a compound word (contains two known words)
        for i in range(3, len(word) - 2):  # Only check reasonable splits
            if (word[:i] in self.word_frequencies and 
                word[i:] in self.word_frequencies):
                score *= 1.3  # Significant boost for compound words
                break
            
        # Check WordNet with higher weight for common words
        if word not in self.wordnet_cache:
            self.wordnet_cache[word] = bool(wordnet.synsets(word))
        if self.wordnet_cache[word]:
            score *= 1.3  # Increased from 1.2
        else:
            score *= 0.7  # Less penalty for unknown words
            
        # Check NLTK words
        if word in self.nltk_words_set:
            score *= 1.2
        else:
            score *= 0.8  # Less penalty
            
        # Length penalties (more lenient)
        if len(word) > 12:
            score *= 0.95  # Reduced penalty
        elif len(word) <= 6:  # Slight boost for shorter words
            score *= 1.1
            
        # Pattern penalties (with exceptions for common affixes)
        if self.has_uncommon_patterns(word):
            if has_common_prefix or has_common_suffix:
                score *= 0.8  # Reduced penalty for words with common affixes
            else:
                score *= 0.6  # Still significant penalty for truly uncommon patterns
                
        return score
        
    def process_word_batch(self, words: List[str]) -> List[Tuple[str, float]]:
        """Process a batch of words and return their scores."""
        return [(word, self.get_word_score(word)) for word in words]
        
    def filter_dictionary(self, input_dict: Dict[str, int]) -> Dict[str, int]:
        """Main filtering function combining both approaches."""
        logger.info("Starting dictionary filtering process...")
        
        # Initial fast filtering
        filtered_dict = {}
        for word, freq in input_dict.items():
            word_lower = word.lower()
            
            # Skip if too short or too long
            if len(word) < 4 or len(word) > 15:
                self.filter_counts['length'] += 1
                continue
                
            # Skip if not all letters
            if not word.isalpha():
                self.filter_counts['non_alpha'] += 1
                continue
                
            # Skip if too many unique letters (must be 7 or fewer for game mechanics)
            if len(set(word_lower)) > 7:
                self.filter_counts['too_many_unique'] += 1
                continue
                
            # Skip if proper noun (unless it's a very common word)
            if self.is_proper_noun(word) and word_lower not in self.word_frequencies:
                self.filter_counts['proper_noun'] += 1
                continue
                
            # Calculate word score
            score = self.get_word_score(word_lower)
            
            # Accept word if it passes threshold (more lenient threshold)
            if score > 0.45:  # Reduced from 0.5
                filtered_dict[word_lower] = freq
            else:
                self.filter_counts['low_score'] += 1
                
        # Generate timestamp for output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'filtered_dictionary_{timestamp}.json'
        
        # Save filtered dictionary
        with open(output_filename, 'w') as f:
            json.dump(filtered_dict, f, indent=2)
            
        # Print statistics
        print(f"\nOriginal dictionary size: {len(input_dict):,}")
        print(f"Filtered dictionary size: {len(filtered_dict):,}")
        print(f"\nFiltered dictionary saved to '{output_filename}'")
        
        print("\nWords filtered by reason:")
        for reason, count in self.filter_counts.most_common():
            print(f"{reason}: {count:,} words")
            
        # Print word length distribution
        lengths = Counter(len(word) for word in filtered_dict)
        print("\nWord length distribution:")
        for length in sorted(lengths):
            print(f"{length} letters: {lengths[length]:,} words")
            
        return filtered_dict
        
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Filter dictionary for word game.')
    parser.add_argument('--dict', '-d', 
                      help='Path to input dictionary JSON file (defaults to dictionary.json)',
                      default='dictionary.json')
    args = parser.parse_args()
    
    # Initialize word filter
    word_filter = WordFilter()
    
    # Load original dictionary
    logger.info(f"Loading dictionary from {args.dict}...")
    try:
        with open(args.dict, 'r') as f:
            original_dict = json.load(f)
        logger.info(f"Successfully loaded {len(original_dict):,} words")
    except FileNotFoundError:
        logger.error(f"Dictionary file '{args.dict}' not found!")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"File '{args.dict}' is not a valid JSON file!")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading dictionary: {str(e)}")
        sys.exit(1)
        
    # Filter dictionary
    filtered_dict = word_filter.filter_dictionary(original_dict)
    
    # Save word cache
    word_filter.save_cached_data()
    
if __name__ == "__main__":
    main() 