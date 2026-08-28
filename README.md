# Spelling Bee Puzzle Generator

Generates puzzle sets for a custom NYT Spelling Bee-style game. Each puzzle has 7 letters (1 center + 6 outer); valid words must contain the center letter, use only those letters, and be at least 4 letters long.

---

## Workflow

Every session follows 3 steps:

### 1. Generate
```bash
python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output new_puzzles.json --exclude-existing puzzle_sets.json
```
Produces ~180 puzzles in 2–5 minutes. Prints a stats summary on completion.

### 2. Batch pre-mark words
```bash
python batch_process_words.py --puzzle-sets new_puzzles.json --dry-run  # preview
python batch_process_words.py --puzzle-sets new_puzzles.json            # apply
```
Auto-marks common words as valid and rare short words as obscure, reducing the manual review burden.

### 3. Review
```bash
python review_puzzles.py new_puzzles.json
```
Interactive terminal UI for manually reviewing remaining words. See `puzzle_review_guide.md` for keyboard shortcuts.

Then merge the reviewed batch with an explicit deployment date:

```bash
python manage_puzzles.py --existing puzzle_sets.json --new new_puzzles.json --dry-run --start-date YYYY-MM-DD
python manage_puzzles.py --existing puzzle_sets.json --new new_puzzles.json --output puzzle_sets.json --start-date YYYY-MM-DD
```

**Output:** the merged `puzzle_sets.json` — drop this into the game.

---

## How Puzzle Generation Works

The generator uses a **pangram-first** approach:

1. **Find anchor words** — scans the dictionary for interesting 7-unique-letter words. Must have no 'S' (prevents plural inflation as an outside letter), frequency in the recognizable-but-satisfying range, length ≥ 7, and no derivational suffixes. Scored and sorted by quality.

2. **Choose center letter** — for each anchor word's letter set, selects the center letter that brings total valid word count closest to 45 (the target midpoint of 30–60). Prefers vowel centers.

3. **Quality gates** — each puzzle must pass: 30–60 valid words, 1–6 pangrams, morphological diversity ≥ 0.70, ≥ 20% of words 6+ letters long, vowel/consonant center balance.

4. **Shuffle** — puzzles are shuffled so there's no correlation between quality and live date.

**Why no S?** When S appears as an outside letter, nearly half the valid words become trivial plurals. Excluding S from anchor words means it never appears in any letter set.

---

## Output Format

```json
{
  "id": "a3f82c91",
  "last_reviewed": "2026-02-19 10:00:00",
  "live_date": "2026-02-19",
  "center_letter": "o",
  "outside_letters": ["c", "k", "t", "a", "i", "l"],
  "anchor_word": "cocktail",
  "pangrams": ["cocktail"],
  "bingo_possible": false,
  "total_score": 284,
  "total_words": 47,
  "valid_words": ["attic", "calk", "click", "clock", "cocktail", "coil", ...]
}
```

`anchor_word` is the "star" word that defined the letter set — always one of the pangrams.

---

## Scoring Rules

| Word | Points |
|------|--------|
| 4-letter word | 1 pt |
| 5+ letter word | length pts (e.g. 7-letter = 7 pts) |
| Pangram | +10 pts |
| Bingo (word starts with each of the 7 letters) | +10 pts |

---

## Key Files

| File | Purpose |
|------|---------|
| `generate_spelling_bee.py` | Puzzle generator |
| `batch_process_words.py` | Auto-mark words before review |
| `review_puzzles.py` | Interactive review TUI |
| `puzzle_review_guide.md` | Keyboard shortcuts for review |
| `filtered_12dictionary_40k.json` | Input dictionary |
| `word_frequency.pkl` | Corpus frequency data (used by all 3 scripts) |
| `puzzle_sets.json` | Generated puzzle output |
| `word_cache.json` | Reviewed word decisions — authoritative, persists across regenerations |

---

## Archive

`archive/` contains scripts not needed for the standard workflow — analysis tools, one-time setup scripts, legacy alternatives, and rarely-used utilities. See `CLAUDE.md` for the full list.

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python archive/download_nltk_data.py  # one-time NLTK setup
```
