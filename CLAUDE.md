# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repo generates Spelling Bee puzzle sets for a custom NYT Spelling Bee-style game. Each puzzle has 7 letters (1 center + 6 outer); valid words must contain the center letter, use only available letters, and be at least 4 letters long. The output (`puzzle_sets.json`) is dropped directly into the game.

This repo is visited infrequently — typically every couple of months to regenerate a fresh batch of ~180 puzzles.

---

## The 3-Step Workflow

Every session follows this sequence:

### Step 1 — Generate puzzles
```bash
python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output puzzle_sets.json
```
Creates ~180 puzzles. Takes 2–5 minutes. Prints stats on completion.

### Step 2 — Batch pre-mark words
```bash
# Preview first (dry run)
python batch_process_words.py --puzzle-sets puzzle_sets.json --dry-run

# Then apply
python batch_process_words.py --puzzle-sets puzzle_sets.json
```
Auto-marks high-frequency words as valid and rare short words as obscure, so the manual review step is faster.

### Step 3 — Manual review
```bash
python review_puzzles.py puzzle_sets.json
```
Interactive curses TUI. Navigate puzzles and words, mark valid/obscure, see WordNet definitions. See `puzzle_review_guide.md` for keyboard shortcuts.

When done, drop `puzzle_sets.json` into the game.

---

## Environment Setup (first time only)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# NLTK data (one-time, script is in archive/)
python archive/download_nltk_data.py
```

---

## Architecture: How Puzzles Are Generated

The generator uses a **pangram-first** approach (as of 2026):

1. **Find anchor candidates** — scans the dictionary for interesting 7-unique-letter words. Filters to words with no 'S' (prevents plural inflation), frequency in the 500–500k range (recognizable but satisfying), length ≥ 7, and no derivational suffixes (-ing, -ed, -tion, etc.). Scores by frequency + length; 8-letter words score highest.

2. **Select center letter** — for each anchor word's letter set, tries each possible center letter and picks the one whose word count is closest to 45 (the target midpoint of 30–60 words). Prefers vowel centers.

3. **Quality gates** — each candidate must pass: 30–60 valid words, 1–6 pangrams, morphological diversity ≥ 0.70 (prevents suffix-inflated puzzles), ≥ 20% of words 6+ letters long, and vowel/consonant center balance (≤ 65% vowels).

4. **Shuffle & date** — puzzles are shuffled so there's no correlation between quality and live date.

**Why no 'S' in letter sets?** When S is an outside letter, nearly half the valid words become trivial plurals (find "air", add "s", find "lair", add "s"…). The pangram-first approach solves this structurally: anchor words with S are excluded, so S never appears in any letter set.

**The `anchor_word` field** — each puzzle JSON now includes an `anchor_word` field identifying the "star" word that defined the letter set. This is always in `pangrams` as well.

---

## Key Data Files

| File | Purpose | Essential? |
|------|---------|-----------|
| `filtered_12dictionary_40k.json` | Input dictionary (~40k words, pre-filtered) | YES |
| `word_frequency.pkl` | Corpus frequency data (~23MB pickle) | YES — all 3 scripts use it |
| `puzzle_sets.json` | Current active puzzle set (game output) | YES |
| `word_cache.json` | Reviewed word decisions (valid/rejected) | YES — authoritative |
| `dictionary.json` | Original full dictionary (~6.8MB) | Source material, not used in workflow |

---

## Scoring System

| Word | Points |
|------|--------|
| 4-letter word | 1 pt |
| 5+ letter word | length pts (e.g., 7-letter = 7 pts) |
| Pangram bonus | +10 pts |
| Bingo bonus (puzzle has word starting with each of the 7 letters) | +10 pts |

---

## word_cache.json — Important

`word_cache.json` is the authoritative record of all reviewed word decisions. Once a word is marked valid or rejected, that decision applies across **all** puzzles — past and future. Never delete or overwrite this file carelessly.

Both `batch_process_words.py` and `review_puzzles.py` automatically create timestamped backups before writing.

---

## Archive Folder

`archive/` contains scripts that are not part of the standard workflow but are kept for reference:

| Script | What it does |
|--------|-------------|
| `analyze_puzzles.py` | Prints stats on a puzzle set (word counts, pangrams, center letters) |
| `analyze_word_frequencies.py` | Frequency distribution visualization; helps tune batch thresholds |
| `check_randomization.py` / `check_original.py` | Verify puzzle randomization quality |
| `create_custom_puzzle.py` | Generate a single puzzle for specified letters |
| `download_nltk_data.py` | One-time NLTK setup |
| `enhanced_filter.py` | Regenerate the filtered dictionary from scratch (rarely needed) |
| `process_frequency_file.py` | Created word_frequency.pkl from raw corpus data |
| `process_pangrams.py` | Legacy script, logic now in generator |
| `smart_review.py` | Older alternative to review_puzzles.py |
| `update_dates.py` | Reset live_dates on existing puzzles |
| `word_length_analyzer.py` | Word length distribution in a dictionary |

---

## Key Concepts & Pitfalls

- **word_cache.json is authoritative**: Decisions persist across regenerations. If you regenerate puzzles, the batch/review steps will still know which words were previously approved.
- **Backups are automatic**: Both `batch_process_words.py` and `review_puzzles.py` create `*_backup_YYYYMMDD_HHMMSS.json` files before writing. Keep only the most recent.
- **Puzzles with < 20 words or 0 pangrams after review are removed**: The review system enforces this automatically.
- **Live dates are sequential from today**: Each puzzle gets `today + N days`. If you need to shift dates, use `archive/update_dates.py`.
- **anchor_word may be reviewed away**: If the anchor word is marked obscure during review and the puzzle drops to 0 pangrams, the puzzle is invalidated. This is intentional.
