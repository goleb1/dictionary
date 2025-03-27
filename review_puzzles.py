import json
import os
from typing import List, Dict, Set, Tuple
import curses
import textwrap
import sys
from nltk.corpus import wordnet
import pickle
from pathlib import Path
from datetime import datetime
import argparse
from collections import Counter
import statistics

class PuzzleReviewer:
    def __init__(self, puzzle_sets_file: str):
        self.puzzle_sets_file = puzzle_sets_file
        with open(puzzle_sets_file, 'r') as f:
            self.puzzle_sets = json.load(f)
            
        # Use base filenames for word lists
        self.word_cache_file = 'word_cache.json'
        
        # Cache for WordNet lookups to improve performance
        self.wordnet_cache = {}
        
        self.word_frequencies = self.load_word_frequencies()
        self.valid_words = set()
        self.obscure_words = set()
        self.load_word_cache()
        
        # Track progress
        self.reviewed_puzzles = 0
        self.total_puzzles = len(self.puzzle_sets)
        
    def load_word_frequencies(self) -> Dict[str, int]:
        """Load word frequencies from pickle file."""
        try:
            with open('word_frequency.pkl', 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}
            
    def load_word_cache(self):
        """Load valid and rejected words from word_cache.json."""
        if os.path.exists(self.word_cache_file):
            try:
                with open(self.word_cache_file, 'r') as f:
                    cache = json.load(f)
                    self.valid_words = set(cache.get('valid', []))
                    self.obscure_words = set(cache.get('rejected', []))
            except (json.JSONDecodeError, KeyError):
                print(f"Warning: Could not load word cache from {self.word_cache_file}")
                self.valid_words = set()
                self.obscure_words = set()
        
    def save_word_cache(self):
        """Save valid and rejected words to word_cache.json."""
        cache = {
            'valid': sorted(list(self.valid_words)),
            'rejected': sorted(list(self.obscure_words))
        }
        with open(self.word_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
            
        # Also create a backup copy
        backup_file = f'word_cache_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def calculate_word_score(self, word: str, is_pangram: bool) -> int:
        """Calculate score for a single word based on game rules."""
        length = len(word)
        if length == 4:
            base_score = 1
        else:
            base_score = length
        
        # Add pangram bonus
        if is_pangram:
            base_score += 10
            
        return base_score

    def is_pangram(self, word: str, center_letter: str, outside_letters: List[str]) -> bool:
        """Check if a word uses all available letters."""
        all_letters = set(outside_letters + [center_letter])
        word_letters = set(word.lower())
        return all_letters.issubset(word_letters)

    def has_bingo(self, words: List[str], all_letters: Set[str]) -> bool:
        """Check if there's at least one word starting with each available letter."""
        starting_letters = set(word[0].lower() for word in words)
        return all_letters.issubset(starting_letters)

    def update_puzzle_stats(self, puzzle: Dict, filtered_words: List[str]) -> Dict:
        """Update all puzzle statistics based on the filtered word list."""
        # Create a copy of the puzzle
        updated_puzzle = dict(puzzle)
        
        # Keep original ID and center/outside letters
        center_letter = puzzle['center_letter']
        outside_letters = puzzle['outside_letters']
        all_letters = set(outside_letters + [center_letter])
        
        # Update valid words and total words count
        updated_puzzle['valid_words'] = filtered_words
        updated_puzzle['total_words'] = len(filtered_words)
        
        # Find pangrams and calculate total score
        total_score = 0
        pangrams = []
        
        for word in filtered_words:
            is_pangram = self.is_pangram(word, center_letter, outside_letters)
            if is_pangram:
                pangrams.append(word)
            total_score += self.calculate_word_score(word, is_pangram)
        
        # Update pangrams
        updated_puzzle['pangrams'] = pangrams
        
        # Update total score
        updated_puzzle['total_score'] = total_score
        
        # Check if bingo is still possible
        updated_puzzle['bingo_possible'] = self.has_bingo(filtered_words, all_letters)
        
        # Add bingo bonus if applicable
        if updated_puzzle['bingo_possible']:
            total_score += 10
            updated_puzzle['total_score'] = total_score
        
        return updated_puzzle
        
    def save_filtered_puzzle_sets(self):
        filtered_sets = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        invalid_puzzles = []
        
        for puzzle in self.puzzle_sets:
            # Filter out obscure words and keep valid words
            filtered_words = [
                word for word in puzzle['valid_words']
                if (word not in self.obscure_words and  # Not marked as obscure
                    (word in self.valid_words or  # Either explicitly marked as valid
                     (word not in self.valid_words and  # Or not yet reviewed
                      word not in self.obscure_words)))
            ]
            
            # Update all puzzle stats based on filtered words
            filtered_puzzle = self.update_puzzle_stats(puzzle, filtered_words)
            
            # Add or update review metadata
            filtered_puzzle['last_reviewed'] = timestamp
            
            # Verify puzzle still meets minimum requirements
            if len(filtered_words) >= 20 and len(filtered_puzzle['pangrams']) >= 1:
                filtered_sets.append(filtered_puzzle)
            else:
                invalid_puzzles.append({
                    'id': puzzle['id'],
                    'words': len(filtered_words),
                    'pangrams': len(filtered_puzzle['pangrams'])
                })
        
        # Create a backup of the original file before overwriting
        backup_file = f"{os.path.splitext(self.puzzle_sets_file)[0]}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w') as f:
            json.dump(self.puzzle_sets, f, indent=2)
            
        # Save back to the original file
        with open(self.puzzle_sets_file, 'w') as f:
            json.dump(filtered_sets, f, indent=2)
            
        print(f"\nSaved filtered puzzles to {self.puzzle_sets_file}")
        print(f"Backup saved to {backup_file}")
        print(f"Last reviewed: {timestamp}")
        
        # Report on removed puzzles
        if invalid_puzzles:
            print("\nRemoved invalid puzzles:")
            for p in invalid_puzzles:
                print(f"Puzzle {p['id']}: {p['words']} words, {p['pangrams']} pangrams")
            print(f"\nTotal puzzles removed: {len(invalid_puzzles)}")
            print(f"Remaining valid puzzles: {len(filtered_sets)}")
            
        # Calculate and print puzzle statistics
        if filtered_sets:
            total_words = sum(p['total_words'] for p in filtered_sets)
            total_score = sum(p['total_score'] for p in filtered_sets)
            total_pangrams = sum(len(p['pangrams']) for p in filtered_sets)
            num_puzzles = len(filtered_sets)
            
            print(f"\nPuzzle Statistics:")
            print(f"Successfully filtered {num_puzzles} puzzles")
            print(f"Average words per puzzle: {total_words / num_puzzles:.1f}")
            print(f"Average score per puzzle: {total_score / num_puzzles:.1f}")
            print(f"Average pangrams per puzzle: {total_pangrams / num_puzzles:.1f}")

    def safe_addstr(self, stdscr, y: int, x: int, text: str):
        """Safely add a string to the screen, handling boundary errors."""
        height, width = stdscr.getmaxyx()
        if y < height:
            # Truncate the text if it would exceed screen width
            if x + len(text) > width:
                text = text[:width - x - 1] + '…'
            try:
                stdscr.addstr(y, x, text)
            except curses.error:
                pass  # Ignore curses errors from writing at screen boundaries

    def display_puzzle(self, stdscr, puzzle_idx: int):
        puzzle = self.puzzle_sets[puzzle_idx]
        words = puzzle['valid_words']
        center_letter = puzzle['center_letter']
        outside_letters = puzzle['outside_letters']
        
        stdscr.clear()
        
        # Get terminal dimensions
        height, width = stdscr.getmaxyx()
        
        # Display condensed instructions at the top
        self.safe_addstr(stdscr, 0, 0, "Instructions: UP/DOWN/LEFT/RIGHT arrows to navigate -- 'F' : mark/unmark current as obscure -- 'J' : mark/unmark current as valid")
        self.safe_addstr(stdscr, 1, 0, "'Y' : mark all remaining as valid -- 'G' : mark current + similar as obscure -- 'H' : mark current + similar words as valid")
        self.safe_addstr(stdscr, 2, 0, "'Q' : save and quit -- 'S' : previous puzzle -- 'D' next puzzle -- 'P' prioritize pangrams")
        
        # Add separator line
        self.safe_addstr(stdscr, 3, 0, "─" * width)
        
        # Display puzzle info with safe writing
        self.safe_addstr(stdscr, 4, 0, f"Puzzle {puzzle_idx + 1} of {len(self.puzzle_sets)} (ID: {puzzle['id']})")
        if 'last_reviewed' in puzzle:
            self.safe_addstr(stdscr, 4, width - 35, f"Last reviewed: {puzzle['last_reviewed']}")
            if all(word in self.valid_words or word in self.obscure_words for word in words):
                stdscr.attron(curses.color_pair(2))  # Green text
                self.safe_addstr(stdscr, 5, width - 15, "Review complete")
                stdscr.attroff(curses.color_pair(2))
        self.safe_addstr(stdscr, 5, 0, f"Center letter: {puzzle['center_letter'].upper()}")
        self.safe_addstr(stdscr, 6, 0, f"Outside letters: {', '.join(l.upper() for l in puzzle['outside_letters'])}")
        
        # Display pangrams list
        pangrams = puzzle['pangrams'] if isinstance(puzzle['pangrams'], list) else []
        pangram_count = len(pangrams)
        self.safe_addstr(stdscr, 7, 0, f"Total words: {len(puzzle['valid_words'])} | Pangrams ({pangram_count}): {', '.join(pangrams)}")
        self.safe_addstr(stdscr, 8, 0, f"Total score: {puzzle['total_score']} | Bingo possible: {puzzle['bingo_possible']}")
        
        # Display stats about word status
        obscure_count = sum(1 for word in puzzle['valid_words'] if word in self.obscure_words)
        valid_count = sum(1 for word in puzzle['valid_words'] if word in self.valid_words)
        remaining_count = len(puzzle['valid_words']) - obscure_count - valid_count
        self.safe_addstr(stdscr, 9, 0, f"Valid words: {valid_count} | Obscure words: {obscure_count} | Unreviewed: {remaining_count}")
        
        # Add another separator line
        self.safe_addstr(stdscr, 10, 0, "─" * width)
        
        return words

    def sort_words_for_review(self, words: List[str], puzzle) -> List[str]:
        """Sort words to optimize review order."""
        # Start with a copy of the original words
        sorted_words = list(words)
        
        # Extract pangrams first - they're most important for good puzzles
        center_letter = puzzle['center_letter']
        outside_letters = puzzle['outside_letters']
        pangrams = [w for w in sorted_words if self.is_pangram(w, center_letter, outside_letters)]
        non_pangrams = [w for w in sorted_words if w not in pangrams]
        
        # Sort non-pangrams by frequency (infrequent words first as they need more attention)
        def get_frequency(word):
            return self.word_frequencies.get(word, 0)
        
        non_pangrams.sort(key=get_frequency)
        
        # Combine pangrams and sorted non-pangrams
        return pangrams + non_pangrams

    def review_puzzles(self):
        def main(stdscr):
            # Hide the cursor
            try:
                curses.curs_set(0)
            except:
                pass  # Some terminals don't support cursor visibility
            
            # Initialize color pairs
            curses.start_color()
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)  # Obscure words
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Valid words
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Similar words
            curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Pangrams
            
            current_puzzle = 0
            current_word = 0
            prioritize_pangrams = False  # Flag to toggle pangram prioritization
            
            while True:
                try:
                    words = self.display_puzzle(stdscr, current_puzzle)
                    
                    # Apply word sorting if pangram prioritization is on or first viewing a puzzle
                    if prioritize_pangrams and current_word == 0:
                        words = self.sort_words_for_review(words, self.puzzle_sets[current_puzzle])
                    
                    height, width = stdscr.getmaxyx()
                    
                    # Calculate maximum words that can fit on screen
                    max_words_per_line = max((width - 1) // 16, 1)  # Ensure at least 1 word per line
                    max_lines = height - 18  # Reduce reserved space from 25 to 18 lines (11 for header + ~7 for word info)
                    max_visible_words = max(max_words_per_line * max_lines, 1)
                    
                    # Calculate which portion of the words to display
                    start_word = (current_word // max_words_per_line) * max_words_per_line
                    start_word = max(0, start_word - max_visible_words + max_words_per_line)
                    end_word = min(len(words), start_word + max_visible_words)
                    
                    # Get current word info
                    current_word_str = words[current_word]
                    freq_line, definitions, examples = self.get_word_info(current_word_str)
                    similar_words = self.find_similar_words(current_word_str, words)
                    
                    # Check if current word is a pangram
                    current_word_is_pangram = self.is_pangram(current_word_str, 
                                                            self.puzzle_sets[current_puzzle]['center_letter'],
                                                            self.puzzle_sets[current_puzzle]['outside_letters'])
                    
                    # Check if all words in current puzzle are reviewed
                    all_words_reviewed = all(word in self.valid_words or word in self.obscure_words for word in words)
                    
                    # Display word info section
                    info_start_line = 11
                    # Show selected word with color if marked
                    self.safe_addstr(stdscr, info_start_line, 0, "Selected word: ")
                    if current_word_str in self.obscure_words:
                        stdscr.attron(curses.color_pair(1))
                    elif current_word_str in self.valid_words:
                        stdscr.attron(curses.color_pair(2))
                    elif current_word_is_pangram:
                        stdscr.attron(curses.color_pair(4))
                    
                    # Add asterisk if pangram
                    display_word = current_word_str + ("*" if current_word_is_pangram else "")
                    self.safe_addstr(stdscr, info_start_line, 14, display_word)
                    
                    if current_word_str in self.obscure_words:
                        stdscr.attroff(curses.color_pair(1))
                    elif current_word_str in self.valid_words:
                        stdscr.attroff(curses.color_pair(2))
                    elif current_word_is_pangram:
                        stdscr.attroff(curses.color_pair(4))
                    
                    # Display similar words if available (right after selected word)
                    current_line = info_start_line + 1
                    if similar_words:
                        self.safe_addstr(stdscr, current_line, 0, "Similar words: ")
                        # Calculate total width needed for all words and separators
                        x_pos = 14  # Starting position after "Similar words: "
                        for i, similar in enumerate(similar_words):
                            # Add separator if not first word
                            if i > 0:
                                self.safe_addstr(stdscr, current_line, x_pos, " -- ")
                                x_pos += 4  # Length of " -- "
                            
                            # Check if similar word is a pangram
                            is_similar_pangram = self.is_pangram(similar,
                                                               self.puzzle_sets[current_puzzle]['center_letter'],
                                                               self.puzzle_sets[current_puzzle]['outside_letters'])
                            
                            # Style based on word status
                            if similar in self.obscure_words:
                                stdscr.attron(curses.color_pair(1))
                            elif similar in self.valid_words:
                                stdscr.attron(curses.color_pair(2))
                            elif is_similar_pangram:
                                stdscr.attron(curses.color_pair(4))
                            else:
                                stdscr.attron(curses.color_pair(3))  # Default yellow for similar
                                
                            display_similar = similar + ("*" if is_similar_pangram else "")
                            self.safe_addstr(stdscr, current_line, x_pos, display_similar)
                            
                            if similar in self.obscure_words:
                                stdscr.attroff(curses.color_pair(1))
                            elif similar in self.valid_words:
                                stdscr.attroff(curses.color_pair(2))
                            elif is_similar_pangram:
                                stdscr.attroff(curses.color_pair(4))
                            else:
                                stdscr.attroff(curses.color_pair(3))
                            
                            x_pos += len(display_similar)  # Move position by word length + possible asterisk
                        current_line += 1
                    
                    # Display frequency
                    self.safe_addstr(stdscr, current_line, 0, freq_line)
                    current_line += 1
                    
                    # Display definitions (limit to 3 lines total including wrapping)
                    total_def_lines = 0
                    for definition in definitions:
                        if total_def_lines >= 3:  # Stop after 3 lines of definitions
                            break
                        wrapped_def = textwrap.wrap(definition, width - 2)
                        for line in wrapped_def[:1]:  # Only show first line of each definition
                            self.safe_addstr(stdscr, current_line, 2, line)
                            current_line += 1
                            total_def_lines += 1
                            if total_def_lines >= 3:
                                break
                    
                    # Add separator line after word info section
                    self.safe_addstr(stdscr, current_line, 0, "─" * width)
                    
                    # Display words with highlighting
                    word_display_start = height - max_lines
                    for i, word in enumerate(words[start_word:end_word], start=start_word):
                        row = word_display_start + ((i - start_word) // max_words_per_line)
                        col = ((i - start_word) % max_words_per_line) * 16
                        
                        if row >= height:
                            break
                        
                        # Check if word is a pangram
                        is_pangram = self.is_pangram(word,
                                                   self.puzzle_sets[current_puzzle]['center_letter'],
                                                   self.puzzle_sets[current_puzzle]['outside_letters'])
                        
                        # Prepare the word display string with pangram indicator
                        display_word = word + ("*" if is_pangram else "")
                        display_word = display_word[:15].ljust(15)
                        
                        try:
                            # Apply appropriate color and highlighting
                            if i == current_word:
                                stdscr.attron(curses.A_REVERSE)
                            
                            if word in self.obscure_words:
                                stdscr.attron(curses.color_pair(1))
                            elif word in self.valid_words:
                                stdscr.attron(curses.color_pair(2))
                            elif is_pangram:
                                stdscr.attron(curses.color_pair(4))
                            elif word in similar_words:
                                stdscr.attron(curses.color_pair(3))
                            
                            stdscr.addstr(row, col, display_word)
                            
                            # Reset attributes
                            if word in self.obscure_words:
                                stdscr.attroff(curses.color_pair(1))
                            elif word in self.valid_words:
                                stdscr.attroff(curses.color_pair(2))
                            elif is_pangram:
                                stdscr.attroff(curses.color_pair(4))
                            elif word in similar_words:
                                stdscr.attroff(curses.color_pair(3))
                            
                            if i == current_word:
                                stdscr.attroff(curses.A_REVERSE)
                        except curses.error:
                            pass  # Ignore curses errors from writing at screen boundaries
                    
                    # Progress bar/indicator
                    progress_text = f"Progress: {current_puzzle+1}/{len(self.puzzle_sets)} puzzles"
                    self.safe_addstr(stdscr, height-1, 0, progress_text)
                    
                    # Word review status
                    review_status = f"Words: {len(self.valid_words)} valid, {len(self.obscure_words)} obscure"
                    self.safe_addstr(stdscr, height-1, width - len(review_status) - 1, review_status)
                    
                    stdscr.refresh()
                    
                    # Handle input
                    key = stdscr.getch()
                    if key == ord('q'):
                        break
                    elif key == ord('d'):  # Next puzzle
                        if current_puzzle < len(self.puzzle_sets) - 1:
                            current_puzzle += 1
                            current_word = 0
                    elif key == ord('s'):  # Previous puzzle
                        if current_puzzle > 0:
                            current_puzzle -= 1
                            current_word = 0
                    elif key == curses.KEY_UP:
                        if current_word >= max_words_per_line:
                            current_word -= max_words_per_line
                    elif key == curses.KEY_DOWN:
                        if current_word + max_words_per_line < len(words):
                            current_word += max_words_per_line
                    elif key == curses.KEY_LEFT:
                        if current_word > 0:
                            current_word -= 1
                    elif key == curses.KEY_RIGHT:
                        if current_word < len(words) - 1:
                            current_word += 1
                    elif key == ord('f'):  # Mark as obscure
                        word = words[current_word]
                        if word in self.obscure_words:
                            self.obscure_words.remove(word)
                        else:
                            self.obscure_words.add(word)
                            if word in self.valid_words:
                                self.valid_words.remove(word)
                            current_word = self.find_next_unmarked_word(words, current_word)
                    elif key == ord('j'):  # Mark as valid
                        word = words[current_word]
                        if word in self.valid_words:
                            self.valid_words.remove(word)
                        else:
                            self.valid_words.add(word)
                            if word in self.obscure_words:
                                self.obscure_words.remove(word)
                            current_word = self.find_next_unmarked_word(words, current_word)
                    elif key == ord('g'):  # Batch mark as obscure
                        word = words[current_word]
                        similar = self.find_similar_words(word, words)
                        for w in [word] + similar:
                            self.obscure_words.add(w)
                            if w in self.valid_words:
                                self.valid_words.remove(w)
                        current_word = self.find_next_unmarked_word(words, current_word)
                    elif key == ord('h'):  # Batch mark as valid
                        word = words[current_word]
                        similar = self.find_similar_words(word, words)
                        for w in [word] + similar:
                            self.valid_words.add(w)
                            if w in self.obscure_words:
                                self.obscure_words.remove(w)
                        current_word = self.find_next_unmarked_word(words, current_word)
                    elif key == ord('y'):  # Mark all remaining unmarked words as valid
                        for w in words:
                            if w not in self.obscure_words and w not in self.valid_words:
                                self.valid_words.add(w)
                    elif key == ord('p'):  # Toggle prioritize pangrams
                        prioritize_pangrams = not prioritize_pangrams
                        if prioritize_pangrams:
                            # Resort words to put pangrams first
                            words = self.sort_words_for_review(words, self.puzzle_sets[current_puzzle])
                            current_word = 0
                
                except curses.error:
                    # Handle any remaining curses errors
                    pass
        
        try:
            curses.wrapper(main)
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            sys.exit(1)
        finally:
            # Save word cache before exiting
            self.save_word_cache()
            self.save_filtered_puzzle_sets()

    def get_word_info(self, word: str) -> Tuple[str, List[str], List[str]]:
        """Get detailed information about a word."""
        # Check cache first for faster lookups
        if word in self.wordnet_cache:
            return self.wordnet_cache[word]
            
        # Word frequency info
        freq = self.word_frequencies.get(word, 0)
        if freq > 0:
            freq_line = f"Frequency: {freq:,} occurrences"
        else:
            freq_line = "Frequency: Not in frequency list"
            
        # WordNet definitions
        synsets = wordnet.synsets(word)
        definitions = []
        examples = []
        if synsets:
            for i, syn in enumerate(synsets[:3], 1):  # Show up to 3 definitions
                pos = syn.pos()
                pos_name = {'n': 'noun', 'v': 'verb', 'a': 'adj', 'r': 'adv', 's': 'adj'}.get(pos, pos)
                definitions.append(f"{i}. ({pos_name}) {syn.definition()}")
                if syn.examples():
                    examples.extend(syn.examples()[:2])  # Show up to 2 examples per synset
        else:
            definitions = ["Not found in WordNet"]
            
        # Cache the results
        result = (freq_line, definitions, examples)
        self.wordnet_cache[word] = result
        
        return result
        
    def find_similar_words(self, word: str, puzzle_words: List[str]) -> List[str]:
        """Find words that are similar to the given word."""
        word_lower = word.lower()
        prefix = word_lower[:4]  # Use first 4 letters for prefix matching
        
        # Only include words that haven't been marked yet
        similar = [w for w in puzzle_words 
                  if w.lower().startswith(prefix) 
                  and w != word
                  and len(w) - 2 <= len(word) <= len(w) + 2  # Length must be similar
                  and w not in self.obscure_words  # Exclude already marked words
                  and w not in self.valid_words]
                  
        return similar[:5]  # Return up to 5 similar words

    def find_next_unmarked_word(self, words: List[str], current_idx: int) -> int:
        """Find the next unmarked word in the list, starting from current_idx."""
        for i in range(current_idx + 1, len(words)):
            if words[i] not in self.obscure_words and words[i] not in self.valid_words:
                return i
        # If no unmarked words found after current, loop back to start
        for i in range(0, current_idx):
            if words[i] not in self.obscure_words and words[i] not in self.valid_words:
                return i
        # If no unmarked words at all, stay on current word
        return current_idx

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Review and filter puzzle sets')
    parser.add_argument('input_file', help='Path to the puzzle sets JSON file to review')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Could not find puzzle sets file at {args.input_file}")
        sys.exit(1)
    
    try:
        reviewer = PuzzleReviewer(args.input_file)
        reviewer.review_puzzles()
    except json.JSONDecodeError:
        print(f"Error: The file at {args.input_file} is not a valid JSON file")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 