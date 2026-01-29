# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Spelling Bee puzzle generator that creates unique puzzle sets for a New York Times Spelling Bee game clone. Each puzzle consists of 7 letters (1 central + 6 outer) where valid words must contain the central letter, use only available letters, and be at least 4 letters long.

## Common Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required NLTK data (wordnet corpus)
python download_nltk_data.py
```

### Puzzle Generation
```bash
# Generate new puzzle sets (creates ~180 puzzles)
python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output puzzle_sets.json

# Analyze generated puzzles
python analyze_puzzles.py

# Check puzzle randomization quality
python check_randomization.py
```

### Puzzle Review Workflow
```bash
# 1. Preview batch word processing
python batch_process_words.py --puzzle-sets puzzle_sets.json --dry-run

# 2. Apply batch processing (marks common words as valid, rare words as obscure)
python batch_process_words.py --puzzle-sets puzzle_sets.json

# 3. Interactive review of remaining words
python review_puzzles.py puzzle_sets.json

# Analyze word frequencies across puzzles
python analyze_word_frequencies.py puzzle_sets.json
```

### Dictionary Processing
```bash
# Analyze word length distribution in dictionary
python word_length_analyzer.py --dict filtered_dictionary.json
```

## Architecture and Key Concepts

### Core Data Flow

1. **Dictionary Processing** → 2. **Puzzle Generation** → 3. **Word Review** → 4. **Final Puzzle Sets**

### Important Data Files

- **dictionary.json**: Main dictionary (~6.8MB) containing all possible words
- **filtered_12dictionary_40k.json**: Filtered dictionary (~637KB) optimized for puzzle generation
- **word_frequency.pkl**: Pickle file (~23MB) containing word frequency data from corpus analysis
- **word_cache.json**: Tracks reviewed words marked as "valid" or "rejected" (obscure)
- **puzzle_sets.json**: Generated puzzle sets (currently deleted in working directory - needs regeneration)

### Puzzle Generation Algorithm (generate_spelling_bee.py)

The generator uses a multi-stage approach:

1. **Letter Set Generation** (generate_letter_sets:106-151):
   - Prioritizes letter combinations from 7-letter words (potential pangrams)
   - Forces 50/50 mix of vowels vs consonants as center letters
   - Generates ~360-540 candidate letter combinations

2. **Candidate Puzzle Creation** (generate_puzzles:200-241):
   - For each letter set, finds all valid words from dictionary
   - Filters puzzles requiring: 30-100 words, 1-4 pangrams
   - Calculates scores (1pt for 4-letter words, length for longer words, +10 for pangrams, +10 for bingo)

3. **Quality Filtering** (filter_puzzles:154-198):
   - Ensures no duplicate letter sets
   - Requires ≥20% long words (6+ letters)
   - Balances center letter distribution (targets 50-60% vowels)
   - Selects best 180 puzzles

4. **Randomization** (generate_puzzles:249):
   - Shuffles final puzzles to remove correlation between puzzle properties and time
   - Without this, puzzles would be ordered by pangram count (most to least)

### Interactive Review System (review_puzzles.py)

The review tool is a curses-based TUI with sophisticated word management:

- **Word Caching**: All review decisions cached in word_cache.json (valid/rejected words)
- **WordNet Integration**: Provides definitions, part-of-speech, and examples
- **Frequency Analysis**: Colors words by frequency (rare words need scrutiny)
- **Similar Word Detection** (find_similar_words:594-607): Groups words by 4-letter prefix match
- **Batch Operations**: Mark groups of similar words simultaneously
- **Auto-update Statistics** (update_puzzle_stats:96-134): Recalculates scores, pangrams, and bingo status after word removal
- **Automatic Backups**: Creates timestamped backups before saving changes

### Scoring System

Implemented in generate_spelling_bee.py and review_puzzles.py:
- 4-letter words: 1 point
- 5+ letter words: length points (e.g., 5-letter = 5 points)
- Pangrams: +10 bonus
- Bingo (word starting with each letter): +10 puzzle bonus

### Word Frequency System

- **word_frequency.pkl**: Pre-computed frequency data from large corpus
- **Frequency-based Processing**: batch_process_words.py uses frequency to auto-mark words
  - Common words (≥50k occurrences): marked valid
  - Rare short words (<50k, <8 letters): marked obscure
  - Rare long words: kept for manual review (may be technical terms)

## Development Notes

### Python Version
Project uses Python 3.9+ (uses typing hints, pickle protocol 5)

### Key Dependencies
- **nltk**: WordNet corpus for word definitions and validation
- **curses**: Terminal UI for interactive review (windows-curses on Windows)
- **matplotlib/scipy**: Visualization and analysis tools
- **pickle**: Binary storage for word frequency data

### File Naming Conventions
- Backup files: `{filename}_backup_{YYYYMMDD_HHMMSS}.json`
- Puzzle set descriptions: Include stats in filename (e.g., `puzzle_sets_180_108w_735s_4.1p.json` = 180 puzzles, avg 108 words, 735 score, 4.1 pangrams)

### Git Status Notes
- puzzle_sets.json is currently deleted (shown as 'D' in git status)
- puzzle_sets_backup_20250904.json exists as untracked file
- To restore: `cp puzzle_sets_backup_20250904.json puzzle_sets.json` or regenerate

### Critical Implementation Details

1. **Letter Set Deduplication**: filter_puzzles uses `frozenset` to detect duplicate letter combinations regardless of which is center (filter_puzzles:167)

2. **Pangram Detection**: Must check if word uses all 7 letters, not just contains them (is_pangram:60-62)

3. **Bingo Calculation**: Checks if at least one word starts with each of the 7 letters (check_bingo:86-89)

4. **Review State Management**: Words can be in valid_words, obscure_words, or neither (unreviewed). Never both simultaneously.

5. **Puzzle Stats Updates**: After word removal, must recalculate total_words, total_score, pangrams list, and bingo_possible (update_puzzle_stats:96-134)

6. **Puzzle Invalidation**: Puzzles with <20 words or <1 pangram after review are removed from final set (save_filtered_puzzle_sets:158)

### Common Pitfalls

- **Don't assume puzzle_sets.json exists**: It's currently deleted. Check for file or use backup.
- **Backup before modifying data files**: review_puzzles.py does this automatically; manual scripts should too.
- **Word cache is authoritative**: Once a word is marked in word_cache.json, that decision applies across all puzzles.
- **Live dates are relative**: Generated as current_date + puzzle_index. Update with update_dates.py if needed.
