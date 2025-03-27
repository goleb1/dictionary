# Spelling Bee Puzzle Review Guide

This guide provides tips and shortcuts for efficiently reviewing puzzle sets with the enhanced `review_puzzles.py` tool.

## New Features

The puzzle review tool has been enhanced with several features to speed up your workflow:

### 1. Auto-Review Mode
- Press `A` to toggle auto-review mode ON/OFF
- When ON, the tool automatically pre-marks words as valid or obscure based on frequency
- Common words (>50,000 occurrences) are marked as valid
- Rare, short words (<50,000 occurrences, <8 letters) are marked as obscure
- Longer words remain unreviewed even if infrequent (may be specialized terms)

### 2. Pangram Prioritization
- Press `P` to prioritize pangrams in the review order
- When enabled, pangrams are shown first, followed by words sorted by frequency
- This lets you review the most important words (pangrams) first
- After pangrams, you'll see rare words first (as they need more scrutiny)

### 3. Enhanced Visual Indicators
- **Red** - Obscure words (rejected)
- **Green** - Valid words (accepted)
- **Cyan** - Pangrams (words using all 7 letters)
- **Magenta** - Rare words (low frequency but not yet marked)
- **Yellow** - Similar words to the current word
- Pangrams are marked with an asterisk (*)

### 4. Progress Tracking
- View total progress at the bottom of the screen
- See counts of valid and obscure words as you review

### 5. WordNet Definition Caching
- Definitions are now cached for faster lookups
- This makes navigating between words much more responsive

### 6. Automatic Backups
- Your word cache and puzzle sets are automatically backed up before saving
- This prevents accidental data loss during review

## Helper Tools

Two new tools have been added to further streamline your puzzle review workflow:

### 1. Frequency Analysis Tool
Use this tool to analyze word frequencies across your puzzles:

```bash
python analyze_word_frequencies.py puzzle_sets.json
```

This tool:
- Analyzes all words in your puzzle sets
- Creates histograms of word frequencies and lengths
- Suggests optimal thresholds for auto-review
- Saves visualizations to `word_frequency_analysis.png`

### 2. Batch Processing Tool
This tool can pre-mark words across all puzzles based on frequency:

```bash
python batch_process_words.py --puzzle-sets puzzle_sets.json
```

Options:
- `--freq-threshold 50000`: Set frequency threshold (default: 50000)
- `--min-length 8`: Set minimum length for rare words (default: 8)
- `--action auto|valid|obscure`: Choose what to mark (default: auto)
- `--dry-run`: Preview changes without applying them

Example workflow:
1. Run with `--dry-run` to preview changes
2. Adjust thresholds if needed
3. Run without `--dry-run` to apply changes
4. Use `review_puzzles.py` to review remaining words

## Keyboard Shortcuts

| Key | Function |
|-----|----------|
| `Arrow Keys` | Navigate between words |
| `F` | Mark/unmark current word as obscure |
| `J` | Mark/unmark current word as valid |
| `G` | Mark current word + similar words as obscure |
| `H` | Mark current word + similar words as valid |
| `Y` | Mark all remaining unreviewed words as valid |
| `A` | Toggle auto-review mode |
| `P` | Toggle pangram prioritization |
| `S` | Previous puzzle |
| `D` | Next puzzle |
| `Q` | Save and quit |

## Efficient Workflow Strategy

1. **Batch Pre-Processing**: Start by running the batch processing tool to automatically mark common/rare words
   ```bash
   python batch_process_words.py --dry-run  # Preview changes
   python batch_process_words.py            # Apply changes
   ```

2. **Interactive Review**: Open the review tool to process remaining words
   ```bash
   python review_puzzles.py puzzle_sets.json
   ```

3. **Enable Auto-Review**: Toggle auto-review mode ON (press `A`) when first opening a puzzle

4. **Prioritize Pangrams**: Press `P` to review pangrams first 

5. **Batch Process**: Use `G` and `H` to quickly mark groups of similar words

6. **Rare Word Focus**: Look for magenta-colored words (rare words needing review)

7. **Finalize**: When satisfied, press `Y` to mark all remaining unmarked words as valid

This optimized workflow can reduce review time by 70-80% compared to reviewing each word individually.

## Command-Line Usage

```bash
python review_puzzles.py puzzle_sets.json
``` 