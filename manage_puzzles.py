#!/usr/bin/env python3
"""
Manage puzzle set updates without disrupting the live game.

Two modes:
  append          -- Keep existing set intact; re-date new puzzles to start after
                     the existing set ends and concatenate. Use when adding more
                     puzzles after the current set runs out.

  replace-forward -- Keep already-played puzzles (+ a grace window); discard
                     unplayed future puzzles; slot new puzzles in starting from
                     the next available date. Use when you improved the algorithm
                     and want better upcoming puzzles.

Workflow position (Step 3.5):
  Step 1: python generate_spelling_bee.py --input filtered_12dictionary_40k.json --output new_puzzles.json
  Step 2: python batch_process_words.py --puzzle-sets new_puzzles.json
  Step 3: python review_puzzles.py new_puzzles.json
  Step 3.5: python manage_puzzles.py --existing puzzle_sets.json --new new_puzzles.json --output puzzle_sets.json [--dry-run]
  Step 4: Drop puzzle_sets.json into game repo

First-time setup: skip Step 3.5 and just rename new_puzzles.json -> puzzle_sets.json.
"""

import json
import os
import sys
import argparse
import uuid
from datetime import datetime, timedelta, date
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: str) -> list:
    """Load a JSON file as a list. Returns [] if the file doesn't exist."""
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array, got {type(data).__name__}")
    return data


def date_from_str(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def str_from_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def redate_puzzles(puzzles: list, start: date) -> list:
    """Return a copy of puzzles with sequential live_dates starting from start."""
    result = []
    for i, p in enumerate(puzzles):
        copy = dict(p)
        copy['live_date'] = str_from_date(start + timedelta(days=i))
        result.append(copy)
    return result


def fix_id_collisions(existing: list, new_puzzles: list) -> list:
    """
    Return a copy of new_puzzles with any IDs that collide with existing replaced
    by fresh random IDs.
    """
    existing_ids = {p['id'] for p in existing if 'id' in p}
    collisions = 0
    result = []
    for p in new_puzzles:
        copy = dict(p)
        if copy.get('id') in existing_ids:
            copy['id'] = uuid.uuid4().hex[:8]
            collisions += 1
        result.append(copy)
    if collisions:
        print(f"  [ID collisions] Replaced {collisions} duplicate ID(s) in new set.")
    return result


def puzzle_letter_set(puzzle: dict) -> frozenset:
    return frozenset([puzzle['center_letter'], *puzzle['outside_letters']])


def puzzle_centered_set(puzzle: dict) -> tuple:
    return puzzle['center_letter'], frozenset(puzzle['outside_letters'])


def reject_duplicate_puzzles(existing: list, new_puzzles: list) -> None:
    """Fail rather than silently scheduling repeated gameplay."""
    existing_anchors = {p.get('anchor_word') for p in existing if p.get('anchor_word')}
    existing_letter_sets = {puzzle_letter_set(p) for p in existing}
    existing_centered_sets = {puzzle_centered_set(p) for p in existing}

    duplicate_anchors = [
        p.get('anchor_word') for p in new_puzzles
        if p.get('anchor_word') and p.get('anchor_word') in existing_anchors
    ]
    duplicate_letter_sets = [
        p.get('anchor_word', p.get('id', 'unknown')) for p in new_puzzles
        if puzzle_letter_set(p) in existing_letter_sets
    ]
    duplicate_centered_sets = [
        p.get('anchor_word', p.get('id', 'unknown')) for p in new_puzzles
        if puzzle_centered_set(p) in existing_centered_sets
    ]

    new_anchors = [p.get('anchor_word') for p in new_puzzles if p.get('anchor_word')]
    new_letter_sets = [puzzle_letter_set(p) for p in new_puzzles]
    new_centered_sets = [puzzle_centered_set(p) for p in new_puzzles]
    internal_duplicate_anchors = len(new_anchors) - len(set(new_anchors))
    internal_duplicate_letter_sets = len(new_letter_sets) - len(set(new_letter_sets))
    internal_duplicate_centered_sets = len(new_centered_sets) - len(set(new_centered_sets))

    problems = []
    if duplicate_anchors:
        problems.append(f"{len(duplicate_anchors)} anchor(s) repeated from existing")
    if duplicate_letter_sets:
        problems.append(f"{len(duplicate_letter_sets)} letter set(s) repeated from existing")
    if duplicate_centered_sets:
        problems.append(f"{len(duplicate_centered_sets)} centered set(s) repeated from existing")
    if internal_duplicate_anchors:
        problems.append(f"{internal_duplicate_anchors} duplicate anchor(s) within new set")
    if internal_duplicate_letter_sets:
        problems.append(f"{internal_duplicate_letter_sets} duplicate letter set(s) within new set")
    if internal_duplicate_centered_sets:
        problems.append(f"{internal_duplicate_centered_sets} duplicate centered set(s) within new set")
    if problems:
        print(f"\nError: refusing to merge: {', '.join(problems)}.")
        sys.exit(1)


def backup_file(path: str) -> str:
    """Write a timestamped backup of path. Returns the backup filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.replace('.json', '') + f"_backup_{timestamp}.json"
    with open(path, 'r') as src, open(backup_path, 'w') as dst:
        dst.write(src.read())
    return backup_path


def print_summary(label: str, puzzles: list) -> tuple:
    if not puzzles:
        print(f"  {label}: (empty)")
        return None, None
    dates = sorted(p['live_date'] for p in puzzles)
    print(f"  {label}: {len(puzzles)} puzzles, {dates[0]} to {dates[-1]}")
    return dates[0], dates[-1]


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def mode_append(
    existing: list,
    new_puzzles: list,
    requested_start: Optional[date] = None,
) -> list:
    if requested_start:
        start = requested_start
        if existing:
            max_date = max(date_from_str(p['live_date']) for p in existing)
            if start <= max_date:
                print(
                    f"Error: --start-date {str_from_date(start)} must be after the existing "
                    f"last date {str_from_date(max_date)}."
                )
                sys.exit(1)
        print(f"  Dating new puzzles from requested start date {str_from_date(start)}.")
    elif not existing:
        start = date.today()
        print("  Existing set is empty — dating new puzzles from today.")
    else:
        max_date = max(date_from_str(p['live_date']) for p in existing)
        start = max_date + timedelta(days=1)
        if max_date < date.today():
            print(f"  [Note] Existing set expired {(date.today() - max_date).days} day(s) ago.")
            print(f"         New puzzles will pick up from {str_from_date(start)} (no gap introduced).")

    redated = redate_puzzles(new_puzzles, start)
    return existing + redated


def mode_replace_forward(existing: list, new_puzzles: list, grace_days: int, confirm: bool) -> list:
    today = date.today()
    cutoff = today + timedelta(days=grace_days)

    kept = [p for p in existing if date_from_str(p['live_date']) <= cutoff]
    dropped = len(existing) - len(kept)

    print(f"\n  Cutoff date (today + {grace_days} grace days): {str_from_date(cutoff)}")
    print(f"  Keeping {len(kept)} puzzles from existing set.")
    print(f"  Dropping {dropped} future puzzle(s) from existing set.")

    if dropped > 0 and not confirm:
        print(
            f"\n  This will permanently remove {dropped} upcoming puzzle(s) from the live set.\n"
            f"  Re-run with --confirm to proceed.\n"
        )
        sys.exit(1)

    if kept:
        start = max(date_from_str(p['live_date']) for p in kept) + timedelta(days=1)
    else:
        start = today

    redated = redate_puzzles(new_puzzles, start)
    return kept + redated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Safely merge a newly generated puzzle set into the live puzzle set.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--existing', default='puzzle_sets.json',
                        help='Current live puzzle set (default: puzzle_sets.json)')
    parser.add_argument('--new', required=True,
                        help='Freshly generated + reviewed puzzle set')
    parser.add_argument('--output', default='puzzle_sets.json',
                        help='Output path (default: puzzle_sets.json, overwrites --existing)')
    parser.add_argument('--mode', choices=['append', 'replace-forward'], default='append',
                        help='append: extend the feed; replace-forward: swap upcoming puzzles (default: append)')
    parser.add_argument('--grace-days', type=int, default=2,
                        help='replace-forward: days of recent history to keep (default: 2)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview the plan without writing anything')
    parser.add_argument('--start-date',
                        help='append mode: first date for the new set (YYYY-MM-DD)')
    parser.add_argument('--confirm', action='store_true',
                        help='Required for replace-forward mode (destructive)')
    args = parser.parse_args()

    requested_start = date_from_str(args.start_date) if args.start_date else None
    if requested_start and args.mode != 'append':
        parser.error('--start-date is only valid in append mode')

    print(f"\n=== Puzzle Merge ({args.mode} mode{', DRY RUN' if args.dry_run else ''}) ===\n")

    # Load
    existing = load_json(args.existing)
    new_puzzles = load_json(args.new)

    if not new_puzzles:
        print(f"Error: --new file '{args.new}' is empty or missing.")
        sys.exit(1)

    print("Before:")
    print_summary(f"  Existing ({args.existing})", existing)
    print_summary(f"  New      ({args.new})", new_puzzles)

    # Fix ID collisions, then reject repeated gameplay before re-dating
    new_puzzles = fix_id_collisions(existing, new_puzzles)
    reject_duplicate_puzzles(existing, new_puzzles)

    # Run chosen mode
    if args.mode == 'append':
        merged = mode_append(existing, new_puzzles, requested_start)
    else:
        merged = mode_replace_forward(existing, new_puzzles, args.grace_days, args.confirm)

    print("\nAfter:")
    print_summary("  Merged", merged)

    if args.dry_run:
        print("\n[DRY RUN] No files written. Re-run without --dry-run to apply.\n")
        return

    # Backup before overwriting
    if os.path.exists(args.output):
        backup_path = backup_file(args.output)
        print(f"\nBacked up existing output to: {backup_path}")

    with open(args.output, 'w') as f:
        json.dump(merged, f, indent=2)

    print(f"Wrote {len(merged)} puzzles to: {args.output}\n")


if __name__ == '__main__':
    main()
