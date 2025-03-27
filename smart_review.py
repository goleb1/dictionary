import json
import curses
import sys
from typing import Dict, List, Set, Tuple
import textwrap
from nltk.corpus import wordnet, names
import pickle
from pathlib import Path
from collections import defaultdict

class WordReviewer:
    def __init__(self):
        # Configuration for auto-accept criteria
        self.auto_accept_config = {
            'min_frequency': 10000,  # Increased minimum frequency
            'require_wordnet': True,  # Must be in WordNet
            'min_score': 0.8,  # Increased minimum score
            'max_length': 8,  # Prefer shorter, common words
        }
        
        # Quick reject patterns (prefix -> description)
        self.reject_patterns = {
            # Chemical/Scientific
            'bio': 'biological terms',
            'hydro': 'chemical/water terms',
            'poly': 'chemical/many terms',
            'mono': 'chemical/single terms',
            'micro': 'microscopic terms',
            'macro': 'large-scale terms',
            'iso': 'equal/same terms',
            'neo': 'new terms',
            'proto': 'first/primary terms',
            'pseudo': 'false terms',
            # Medical
            'hyper': 'medical excessive terms',
            'hypo': 'medical deficient terms',
            'cardio': 'heart-related terms',
            'neuro': 'nerve-related terms',
            'psycho': 'mind-related terms',
            # Technical
            'cyber': 'computer-related terms',
            'techno': 'technology terms',
            'meta': 'self-referential terms',
            'multi': 'multiple terms',
            'inter': 'between terms'
        }
        
        # Name detection patterns
        self.name_endings = {
            'ie', 'y', 'ey', 'i', 'ee', 'anne', 'anna', 'a', 
            'beth', 'elle', 'ena', 'ene', 'ina', 'ine', 'lynn'
        }
        
        # Load name lists for filtering
        self.names_set = set()
        self.load_name_lists()
        
        self.current_category = None
        self.current_words = []
        self.current_index = 0
        self.batch_decisions = {}
        self.current_batch = []
        
        self.load_data()
        
    def load_name_lists(self):
        """Load and combine multiple name lists for better coverage."""
        from nltk.corpus import names
        # Add names from NLTK
        self.names_set.update(name.lower() for name in names.words())
        # Add common name variations
        for name in list(self.names_set):
            # Add common diminutive forms
            if len(name) > 3:
                self.names_set.add(name + 'ie')
                self.names_set.add(name + 'y')
                if name.endswith('y'):
                    self.names_set.add(name[:-1] + 'ie')
        
    def is_likely_name(self, word: str) -> bool:
        """Enhanced name detection."""
        word_lower = word.lower()
        
        # Direct match in names list
        if word_lower in self.names_set:
            return True
            
        # Check common name endings
        for ending in self.name_endings:
            if word_lower.endswith(ending) and len(word_lower) > len(ending) + 2:
                return True
                
        # Check if it's capitalized in WordNet
        synsets = wordnet.synsets(word)
        if synsets:
            # If the first synset is a person and the word is typically capitalized
            if synsets[0].lexname() == 'noun.person':
                examples = [ex for s in synsets for ex in s.examples()]
                if any(word in ex for ex in examples) and any(word[0].isupper() for ex in examples):
                    return True
                    
        return False
        
    def should_auto_accept(self, word: str) -> bool:
        """Check if a word meets the auto-accept criteria."""
        word_lower = word.lower()
        
        # Skip likely names
        if self.is_likely_name(word):
            return False
            
        # Skip if too long
        if len(word) > self.auto_accept_config['max_length']:
            return False
            
        # Check frequency
        freq = self.word_frequencies.get(word, 0)
        if freq < self.auto_accept_config['min_frequency']:
            return False
            
        # Check WordNet presence and ensure it's not just a name
        if self.auto_accept_config['require_wordnet']:
            synsets = wordnet.synsets(word)
            if not synsets:
                return False
            # Check if the first synset is a person
            if synsets[0].lexname() == 'noun.person':
                return False
            
        # Calculate and check score
        score = self.get_word_score(word)
        if score < self.auto_accept_config['min_score']:
            return False
            
        return True
        
    def get_word_score(self, word: str) -> float:
        """Calculate a composite score for word commonness/validity."""
        score = 1.0
        word_lower = word.lower()
        
        # Heavily penalize likely names
        if self.is_likely_name(word):
            score *= 0.1
            
        # Factor in frequency
        freq = self.word_frequencies.get(word, 0)
        if freq > 0:
            freq_score = min(1.0, freq / 20000)
            score *= (0.5 + 0.5 * freq_score)
        else:
            score *= 0.4
            
        # Factor in WordNet presence
        synsets = wordnet.synsets(word)
        if not synsets:
            score *= 0.65
        elif synsets[0].lexname() == 'noun.person':
            score *= 0.2  # Heavily penalize person nouns
            
        # Penalize long words
        if len(word) > 8:
            score *= 0.8
            
        # Penalize words with common name endings
        for ending in self.name_endings:
            if word_lower.endswith(ending):
                score *= 0.5
                break
                
        return score
        
    def sort_words(self, words: List[str]) -> List[str]:
        """Sort words by frequency and score, with name filtering."""
        # Create tuples of (word, frequency, score, is_name)
        word_data = []
        for word in words:
            freq = self.word_frequencies.get(word, 0)
            score = self.get_word_score(word)
            is_name = self.is_likely_name(word)
            word_data.append((word, freq, score, is_name))
            
        # Sort by: not a name first, then frequency, then score
        word_data.sort(key=lambda x: (-x[2], -x[1], x[3]))  # Higher score first, higher freq first, names last
        return [w[0] for w in word_data]
        
    def find_similar_words(self, word: str) -> List[str]:
        """Find words that are similar to the given word for batch processing."""
        similar = []
        word_lower = word.lower()
        
        # Only use prefix matching with longer prefix
        prefix = word_lower[:4]  # Increased from 3 to 4 characters
        similar = [w for w in self.current_words 
                  if w.lower().startswith(prefix) 
                  and w != word
                  and len(w) - 2 <= len(word) <= len(w) + 2]  # Length must be similar
                  
        return similar[:5]  # Reduced from 10 to 5 similar words
        
    def get_word_info(self, word: str) -> str:
        """Get detailed information about a word."""
        # Word frequency info
        freq = self.word_frequencies.get(word, 0)
        if freq > 0:
            freq_line = f"Frequency: {freq:,} occurrences"
        else:
            freq_line = "Frequency: Not in frequency list"
            
        # WordNet definitions
        synsets = wordnet.synsets(word)
        if synsets:
            defs = []
            defs.append("Definitions:")
            for i, syn in enumerate(synsets[:3], 1):  # Show up to 3 definitions
                defs.append(f"{i}. {syn.definition()}")
        else:
            defs = ["Not found in WordNet"]
            
        # Previous decisions
        if word in self.word_cache['accepted']:
            status = "Previously: Accepted"
        elif word in self.word_cache['rejected']:
            status = "Previously: Rejected"
        else:
            status = ""
            
        # Combine all parts with proper spacing
        result = freq_line + "    " + defs[0]
        if len(defs) > 1:
            result += "    " + "    ".join(defs[1:])
        if status:
            result += "    " + status
            
        return result
        
    def review_words(self, stdscr):
        """Main review interface using curses."""
        # Setup colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        
        # Select category
        categories = list(self.categories.keys())
        current_cat = 0
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # Show category selection
            stdscr.addstr(0, 0, "Select category to review (use arrow keys, Enter to select):")
            for i, cat in enumerate(categories):
                count = len(self.categories[cat])
                if i == current_cat:
                    stdscr.addstr(i + 2, 2, f"> {cat} ({count} words)", curses.A_REVERSE)
                else:
                    stdscr.addstr(i + 2, 2, f"  {cat} ({count} words)")
                    
            stdscr.refresh()
            
            # Handle input
            key = stdscr.getch()
            if key == curses.KEY_UP and current_cat > 0:
                current_cat -= 1
            elif key == curses.KEY_DOWN and current_cat < len(categories) - 1:
                current_cat += 1
            elif key == 10:  # Enter key
                self.current_category = categories[current_cat]
                self.current_words = self.categories[self.current_category]
                self.review_category(stdscr)
            elif key == ord('q'):
                return
                
    def review_category(self, stdscr):
        """Review words in the selected category."""
        # Filter out already reviewed words
        self.current_words = [
            word for word in self.categories[self.current_category]
            if word not in self.word_cache['accepted']
            and word not in self.word_cache['rejected']
        ]
        
        # Sort words by frequency and score
        self.current_words = self.sort_words(self.current_words)
        self.current_index = 0
        
        if not self.current_words:
            stdscr.clear()
            stdscr.addstr(0, 0, f"All words in {self.current_category} have been reviewed!")
            stdscr.addstr(2, 0, "Press any key to return to category selection...")
            stdscr.refresh()
            stdscr.getch()
            return
            
        # Load initial batch of similar words
        self.current_batch = self.find_similar_words(self.current_words[0])
            
        while self.current_index < len(self.current_words):
            word = self.current_words[self.current_index]
            info = self.get_word_info(word)
            
            while True:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                # Show progress
                progress = f"[{self.current_index + 1}/{len(self.current_words)}]"
                stdscr.addstr(0, 0, f"Reviewing {self.current_category} {progress}")
                
                # Show current word
                stdscr.addstr(2, 0, f"Word: {word}", curses.A_BOLD)
                
                # Show word information
                info = self.get_word_info(word)
                parts = info.split("    ")
                
                # Display frequency on first line
                stdscr.addstr(4, 0, parts[0])  # Frequency info
                
                # Display definitions starting on next line
                current_line = 5
                if len(parts) > 1:
                    stdscr.addstr(current_line, 0, parts[1])  # "Definitions:" or "Not found in WordNet"
                    current_line += 1
                    
                    # Display each definition on its own line
                    for part in parts[2:-1]:  # Skip the last part if it's the status
                        if part.startswith(("1.", "2.", "3.")):  # It's a definition
                            stdscr.addstr(current_line, 2, part)  # Indent definitions
                            current_line += 1
                
                # Display status if present
                if parts[-1].startswith("Previously:"):
                    stdscr.addstr(current_line + 1, 0, parts[-1])
                    current_line += 1
                
                # Always show similar words
                if self.current_batch:
                    stdscr.addstr(current_line + 2, 0, "Similar words:")
                    for i, batch_word in enumerate(self.current_batch, 1):
                        if batch_word != word:
                            stdscr.addstr(current_line + 2 + i, 2, batch_word)
                    current_line += len(self.current_batch) + 3
                
                # Show controls
                controls = [
                    "Controls:",
                    "j: Accept current word only",
                    "f: Reject current word only",
                    "n: Accept current word and similar words",
                    "v: Reject current word and similar words",
                    "h: Skip word",
                    "g: Go back",
                    "q: Save and quit",
                    "r+[1-9]: Quick reject patterns"
                ]
                
                # Show quick reject patterns
                if height > len(controls) + 15:  # Only show if there's room
                    controls.append("")
                    controls.append("Quick Reject Patterns:")
                    for i, (prefix, desc) in enumerate(self.reject_patterns.items(), 1):
                        if i <= 9:  # Only show first 9
                            controls.append(f"r+{i}: {prefix}* ({desc})")
                
                for i, control in enumerate(controls):
                    if height - len(controls) + i - 1 >= 0:
                        stdscr.addstr(height - len(controls) + i - 1, 0, control)
                        
                stdscr.refresh()
                
                # Handle input
                key = stdscr.getch()
                if key == ord('j'):  # Accept current word only
                    self.batch_decisions[word] = 'accept'
                    self.current_index += 1
                    break
                elif key == ord('f'):  # Reject current word only
                    self.batch_decisions[word] = 'reject'
                    self.current_index += 1
                    break
                elif key == ord('n'):  # Accept current word and batch
                    words_to_accept = [word] + self.current_batch
                    for w in words_to_accept:
                        self.batch_decisions[w] = 'accept'
                    self.current_index += 1
                    break
                elif key == ord('v'):  # Reject current word and batch
                    words_to_reject = [word] + self.current_batch
                    for w in words_to_reject:
                        self.batch_decisions[w] = 'reject'
                    self.current_index += 1
                    break
                elif key == ord('h'):
                    self.current_index += 1
                    break
                elif key == ord('g') and self.current_index > 0:
                    self.current_index -= 1
                    break
                elif key == ord('r'):
                    # Wait for the number key after 'r'
                    pattern_key = stdscr.getch()
                    if ord('1') <= pattern_key <= ord('9'):
                        pattern_idx = pattern_key - ord('1')
                        if pattern_idx < len(self.reject_patterns):
                            prefix = list(self.reject_patterns.keys())[pattern_idx]
                            if word.lower().startswith(prefix.lower()):
                                self.batch_decisions[word] = 'reject'
                                self.current_index += 1
                                break
                elif key == ord('q'):
                    self.save_progress()
                    return
                
            if self.current_index >= len(self.current_words):
                self.save_progress()
                return
            # Always load next batch of similar words
            next_word = self.current_words[self.current_index]
            self.current_batch = self.find_similar_words(next_word)
            
    def save_progress(self):
        """Save current progress to files."""
        # Update word cache with batch decisions
        saved_count = 0
        for word, decision in self.batch_decisions.items():
            if decision == 'accept':
                if word not in self.word_cache['accepted']:
                    self.word_cache['accepted'].append(word)
                    saved_count += 1
                if word in self.word_cache['rejected']:
                    self.word_cache['rejected'].remove(word)
            elif decision == 'reject':
                if word not in self.word_cache['rejected']:
                    self.word_cache['rejected'].append(word)
                    saved_count += 1
                if word in self.word_cache['accepted']:
                    self.word_cache['accepted'].remove(word)
                    
        # Save word cache
        with open('word_cache.json', 'w') as f:
            json.dump(self.word_cache, f, indent=2)
            
        # Show save confirmation
        stdscr = curses.initscr()
        try:
            height, width = stdscr.getmaxyx()
            stdscr.addstr(height-1, 0, f"Progress saved: {saved_count} new decisions", curses.A_BOLD)
            stdscr.refresh()
            curses.napms(1000)  # Show message for 1 second
        except:
            pass  # Ignore any curses errors
            
        # Clear batch decisions after saving
        self.batch_decisions = {}
        
    def load_data(self):
        """Load all necessary data files."""
        # Load word cache first since we need it to filter categories
        try:
            with open('word_cache.json', 'r') as f:
                self.word_cache = json.load(f)
        except FileNotFoundError:
            self.word_cache = {
                'accepted': [],
                'rejected': [],
                'pending_review': []
            }

        # Load word categories and filter out reviewed words
        try:
            with open('word_categories.json', 'r') as f:
                raw_categories = json.load(f)
                # Filter out already reviewed words from each category
                self.categories = {}
                for category, words in raw_categories.items():
                    self.categories[category] = [
                        word for word in words
                        if word not in self.word_cache['accepted']
                        and word not in self.word_cache['rejected']
                        and not self.is_likely_name(word)  # Filter out names during load
                    ]
        except FileNotFoundError:
            print("Error: word_categories.json not found. Run enhanced_filter.py first.")
            sys.exit(1)
            
        # Load word frequencies if available
        try:
            with open('word_frequency.pkl', 'rb') as f:
                self.word_frequencies = pickle.load(f)
        except FileNotFoundError:
            self.word_frequencies = {}
            
        # Auto-accept highly common words
        self.auto_accept_common_words()
            
    def auto_accept_common_words(self):
        """Automatically accept words that meet the auto-accept criteria."""
        auto_accepted = []
        for category, words in self.categories.items():
            for word in words:
                if self.should_auto_accept(word):
                    auto_accepted.append(word)
                    if word not in self.word_cache['accepted']:
                        self.word_cache['accepted'].append(word)
                        
        if auto_accepted:
            print(f"Auto-accepted {len(auto_accepted)} common words")
            self.save_progress()

def main():
    reviewer = WordReviewer()
    curses.wrapper(reviewer.review_words)
    
if __name__ == "__main__":
    main() 