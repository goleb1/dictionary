import json
from collections import defaultdict
import argparse

# Default dictionary file path
DEFAULT_DICTIONARY_FILE = "filtered_dictionary.json"

def analyze_word_lengths(dictionary_file):
    """
    Analyzes the length distribution of words in a JSON dictionary.
    
    Args:
        dictionary_file (str): Path to the JSON dictionary file
    """
    # Initialize a defaultdict to store length counts
    length_counts = defaultdict(int)
    
    try:
        # Read and parse the JSON file
        with open(dictionary_file, 'r', encoding='utf-8') as file:
            word_dict = json.load(file)
            
        # Count words of each length
        for word in word_dict.keys():
            word_length = len(word)
            length_counts[word_length] += 1
            
        # Convert to regular dict and sort by length
        sorted_counts = dict(sorted(length_counts.items()))
        
        # Print the results
        print("\nWord Length Distribution:")
        print("------------------------")
        for length, count in sorted_counts.items():
            print(f"{length} letter words: {count:,}")
            
        # Print total word count
        total_words = sum(length_counts.values())
        print("\nTotal words in dictionary:", f"{total_words:,}")
        
        return sorted_counts
        
    except FileNotFoundError:
        print(f"Error: File '{dictionary_file}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{dictionary_file}' is not valid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze word length distribution in a JSON dictionary file.')
    parser.add_argument('--dict', '-d', 
                      default=DEFAULT_DICTIONARY_FILE,
                      help='Path to the JSON dictionary file (default: filtered_dictionary.json)')
    
    args = parser.parse_args()
    analyze_word_lengths(args.dict)