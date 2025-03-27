# Spelling Bee Puzzle Generator

A Python script that generates unique puzzle sets for a New York Times Spelling Bee game clone.

## Overview

This project generates approximately 180 unique puzzle sets, each consisting of 7 letters (1 central letter and 6 outer letters). Valid words in each puzzle must:
- Contain the central letter
- Only use letters from the set
- Be at least 4 letters long

Each puzzle has at least one pangram (word using all 7 letters) and contains between 25-200 valid words.

## Features

- Generates diverse puzzle sets with balanced letter distributions
- Ensures each puzzle has 1-6 pangrams
- Avoids letter set repetition within a 60-day period
- Randomizes puzzle order for optimal variety over time
- Calculates scores according to Spelling Bee rules
- Checks for "bingo" possibility (at least one word starting with each letter)
- Creates unique IDs for each puzzle

## Puzzle Randomization

The generator ensures that puzzles are presented in a randomized order with respect to their properties:

- Without randomization, puzzles would follow a predictable pattern from more pangrams to fewer pangrams over time
- With our randomization, there's no significant correlation between puzzle properties and time
- This provides a more engaging player experience with varied difficulty levels throughout the game's lifecycle

Correlation analysis of randomized puzzles shows:
- Words correlation: -0.0967 (essentially random)
- Score correlation: -0.1140 (essentially random)
- Pangrams correlation: -0.0201 (essentially random)

## Usage

### Requirements

Install the required packages:

```bash
pip install -r requirements.txt
```

### Generating Puzzles

Run the puzzle generator script:

```bash
python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output puzzle_sets.json
```

**Parameters:**
- `--input`: Input dictionary file path (default: `filtered_12dictionary_40k.json`)
- `--output`: Output puzzle sets file path (default: `puzzle_sets.json`)

### Analyzing Puzzles

To get statistics about the generated puzzles:

```bash
python analyze_puzzles.py
```

To check the randomization of puzzles over time:

```bash
python check_randomization.py
```

## Output Format

The script generates a JSON file with the following structure for each puzzle:

```json
{
  "id": "dc553376",
  "last_reviewed": "2025-02-24 12:04:11",
  "live_date": "2025-02-24",
  "center_letter": "i",
  "outside_letters": ["a", "e", "n", "o", "r", "t"],
  "pangrams": ["aeration", "anterior", "iteration", "orientate", "orientation", "reiteration"],
  "bingo_possible": true,
  "total_score": 656,
  "total_words": 99,
  "valid_words": [...]
}
```

## Scoring Rules

- 1 point for 4-letter words
- Word length for longer words
- +10 points for pangrams
- +10 points if bingo is possible

## Statistics

The generated puzzles have the following characteristics:
- 16.1% have 1 pangram, 36.7% have 2 pangrams, 25.0% have 3 pangrams
- Average of 112 words per puzzle
- Average score of 593 points per puzzle
- 85.6% of puzzles have "bingo" possibility
- Most common center letters: e (28.3%), a (27.2%), i (21.1%)

## Scripts and Their Functions

This section describes each Python script in the project, including their purpose, inputs, outputs, and any command-line arguments they accept.

- **`analyze_puzzles.py`**
  - **Purpose**: Analyzes generated puzzle sets to provide detailed statistics.
  - **Inputs**: A JSON file containing puzzle sets (default: `puzzle_sets.json`).
  - **Outputs**: Printed statistics including:
    - Number of pangrams per puzzle
    - Word count statistics (min, max, average)
    - Score statistics (min, max, average)
    - Percentage of puzzles with "bingo" possibility
    - Distribution of center letters and overall letter frequencies
  - **Arguments**: None explicitly defined; assumes `puzzle_sets.json` in the current directory.

- **`analyze_word_frequencies.py`**
  - **Purpose**: Analyzes word frequencies across all puzzles to provide insights and suggest auto-review thresholds.
  - **Inputs**:
    - Puzzle sets JSON file (specified via command-line argument)
    - Word frequency pickle file (`word_frequency.pkl`)
  - **Outputs**:
    - Printed frequency distribution for all words and pangrams
    - Word length distribution
    - A plot saved as `word_frequency_analysis.png`
    - Suggested frequency thresholds for auto-review
  - **Arguments**:
    - `input_file`: Path to the puzzle sets JSON file (required)

  ```bash
  python analyze_word_frequencies.py puzzle_sets.json
  ```

- **`batch_process_words.py`**
  - **Purpose**: Batch processes words across all puzzles to pre-mark common words as valid and rare words as invalid, speeding up manual review.
  - **Inputs**:
    - Puzzle sets JSON file (default: `puzzle_sets.json`)
    - Word cache JSON file (`word_cache.json`)
    - Word frequency pickle file (`word_frequency.pkl`)
  - **Outputs**:
    - Updated `word_cache.json` with marked valid and rejected words
    - Printed preview of changes (if `--dry-run` is used)
  - **Arguments**:
    - `--puzzle-sets`: Path to puzzle sets JSON file (default: `puzzle_sets.json`)
    - `--word-cache`: Path to word cache JSON file (default: `word_cache.json`)
    - `--freq-threshold`: Frequency threshold for processing (default: 50000)
    - `--min-length`: Minimum word length for rare words (default: 8)
    - `--action`: Action to perform (`auto`, `valid`, `obscure`; default: `auto`)
    - `--dry-run`: Preview changes without saving (flag)

  ```bash
  python batch_process_words.py --puzzle-sets puzzle_sets.json --freq-threshold 10000 --action auto
  ```

- **`check_original.py`**
  - **Purpose**: Compares properties of randomized versus non-randomized puzzle sets to verify randomization effects.
  - **Inputs**:
    - Original puzzle sets JSON file (`puzzle_sets.json`)
    - Randomized puzzle sets JSON file (`puzzle_sets_randomized.json`)
  - **Outputs**:
    - Printed correlation statistics for words, scores, and pangrams over time
    - Visualizations saved as `puzzle_(original|randomized).png`
  - **Arguments**: None; assumes files are in the current directory.

- **`check_randomization.py`**
  - **Purpose**: Analyzes the randomization of puzzle properties over time for a single puzzle set.
  - **Inputs**: A JSON file containing puzzle sets (default: `puzzle_sets_randomized.json` assumed).
  - **Outputs**:
    - Printed correlation statistics for words, scores, and pangrams over time
    - Visualizations saved (filename truncated in provided code, likely `puzzle_randomization.png`)
  - **Arguments**: None explicitly defined; assumes a file in the current directory.

- **`create_custom_puzzle.py`**
  - **Purpose**: Generates a custom Spelling Bee puzzle based on user-specified letters.
  - **Inputs**:
    - User-specified center letter and outer letters (via command-line or interactive input, assumed)
    - Dictionary JSON file (`dictionary.json`)
    - Word frequency pickle file (`word_frequency.pkl`)
  - **Outputs**: A custom puzzle with valid words and pangrams (format not specified, likely printed or saved).
  - **Arguments**: Not detailed in provided code; likely accepts letters as inputs.

- **`download_nltk_data.py`**
  - **Purpose**: Downloads necessary NLTK (Natural Language Toolkit) data for the project.
  - **Inputs**: None (connects to NLTK servers).
  - **Outputs**: Downloaded NLTK data stored locally.
  - **Arguments**: None assumed; standard NLTK download script.

- **`enhanced_filter.py`**
  - **Purpose**: An enhanced version of dictionary filtering, creating a subset of words suitable for puzzle generation.
  - **Inputs**: Main dictionary JSON file (`dictionary.json` assumed).
  - **Outputs**: A filtered dictionary JSON file (e.g., `filtered_*.json`).
  - **Arguments**: Not specified; likely similar to `filter_dictionary.py`.

- **`filter_dictionary.py`**
  - **Purpose**: Filters the main dictionary to create a subset suitable for puzzle generation based on criteria like word length or frequency.
  - **Inputs**: Main dictionary JSON file (`dictionary.json` assumed).
  - **Outputs**: A filtered dictionary JSON file (e.g., `filtered_12dictionary_40k.json`).
  - **Arguments**: Not specified; likely configurable via command-line.

- **`generate_puzzles.py`** and **`generate_spelling_bee.py`**
  - **Purpose**: Generates puzzle sets for the Spelling Bee game. **Note**: Both scripts are listed; `generate_spelling_bee.py` is referenced in code and README, while `generate_puzzles.py` is in the directory. They may be duplicates or variants. Below assumes `generate_spelling_bee.py` is the primary generator.
  - **Inputs**: A filtered dictionary JSON file (e.g., `filtered_12dictionary_40k.json`).
  - **Outputs**: A JSON file containing generated puzzle sets (e.g., `puzzle_sets.json`).
  - **Arguments**:
    - `--input`: Path to the input dictionary file
    - `--output`: Path to the output puzzle sets file

  ```bash
  python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output puzzle_sets.json
  ```

- **`process_frequency_file.py`**
  - **Purpose**: Processes a frequency data file to create a word frequency pickle file.
  - **Inputs**: A frequency data file (format not specified).
  - **Outputs**: `word_frequency.pkl`.
  - **Arguments**: Not specified; assumes a default input file.

- **`process_pangrams.py`**
  - **Purpose**: Identifies or processes pangrams within the dictionary for use in puzzle generation.
  - **Inputs**: Dictionary JSON file (`dictionary.json` assumed).
  - **Outputs**: Pangram-related data (format not specified, possibly a list or file).
  - **Arguments**: Not specified.

- **`review_puzzles.py`**
  - **Purpose**: Facilitates manual review and editing of generated puzzle sets.
  - **Inputs**: Puzzle sets JSON file (e.g., `puzzle_sets.json`).
  - **Outputs**: Allows editing or marking of puzzles (updated JSON file assumed).
  - **Arguments**: Not specified.

- **`smart_review.py`**
  - **Purpose**: Automates parts of the puzzle review process based on predefined criteria.
  - **Inputs**:
    - Puzzle sets JSON file (e.g., `puzzle_sets.json`)
    - Possibly `word_cache.json` or `word_frequency.pkl`
  - **Outputs**: Updated puzzle sets or review suggestions.
  - **Arguments**: Not specified.

- **`update_dates.py`**
  - **Purpose**: Updates dates (e.g., `live_date`, `last_reviewed`) in the puzzle sets.
  - **Inputs**: Puzzle sets JSON file (e.g., `puzzle_sets.json`).
  - **Outputs**: Updated puzzle sets JSON file with new dates.
  - **Arguments**: Not specified.

- **`word_length_analyzer.py`**
  - **Purpose**: Analyzes the distribution of word lengths in a dictionary.
  - **Inputs**: Dictionary JSON file (default: `filtered_dictionary.json`).
  - **Outputs**: Printed statistics on word length distribution and total word count.
  - **Arguments**:
    - `--dict` or `-d`: Path to the dictionary JSON file (default: `filtered_dictionary.json`)

  ```bash
  python word_length_analyzer.py --dict filtered_dictionary_119k.json
  ```

## Data Files

- **`dictionary.json`**: The main dictionary containing all possible words.
- **`filtered_*.json`**: Filtered dictionary files (e.g., `filtered_12dictionary_40k.json`, `filtered_dictionary_119k.json`), each with different sizes or criteria.
- **`puzzle_sets_*.json`**: Generated puzzle sets (e.g., `puzzle_sets_180_110w_575s_2.7p.json`, `puzzle_sets_randomized.json`).
- **`word_cache.json`**: Cache of reviewed words, marking them as valid or rejected.
- **`word_categories.json`**: Word categorizations (e.g., by difficulty or theme).
- **`word_frequency.pkl`**: Pickle file with word frequency data.
- **`puzzle_review_guide.md`**: Markdown file with guidelines for reviewing puzzles (not a script).

---

### Notes
- **Naming Discrepancy**: The directory lists both `generate_puzzles.py` and `generate_spelling_bee.py`. The existing README and code references suggest `generate_spelling_bee.py` is the primary generator. Verify which script is current; `generate_puzzles.py` might be an older version or serve a different purpose.
- **Missing Details**: For scripts without provided code (e.g., `create_custom_puzzle.py`, `process_pangrams.py`), inputs and outputs are inferred from context. Check the scripts for exact arguments.
- **Usage Tip**: Run scripts with `--help` (if implemented) to see additional argument details not listed here.