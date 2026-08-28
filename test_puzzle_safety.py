import unittest
from datetime import date

import generate_spelling_bee
import manage_puzzles


class PuzzleSafetyTests(unittest.TestCase):
    def setUp(self):
        self.existing = [{
            "id": "old",
            "live_date": "2026-08-20",
            "center_letter": "a",
            "outside_letters": ["b", "c", "d", "e", "f", "g"],
            "anchor_word": "abcdefg",
        }]
        self.fresh = [{
            "id": "new",
            "live_date": None,
            "center_letter": "h",
            "outside_letters": ["i", "j", "k", "l", "m", "n"],
            "anchor_word": "hijklmn",
        }]

    def test_explicit_start_date_is_applied(self):
        merged = manage_puzzles.mode_append(
            self.existing, self.fresh, date(2026, 8, 28)
        )
        self.assertEqual(merged[-1]["live_date"], "2026-08-28")

    def test_start_date_cannot_overlap_existing_schedule(self):
        with self.assertRaises(SystemExit):
            manage_puzzles.mode_append(
                self.existing, self.fresh, date(2026, 8, 20)
            )

    def test_duplicate_letter_set_is_rejected_even_with_new_center(self):
        duplicate = [{
            **self.existing[0],
            "id": "different-id",
            "center_letter": "b",
            "outside_letters": ["a", "c", "d", "e", "f", "g"],
            "anchor_word": "different-anchor",
        }]
        with self.assertRaises(SystemExit):
            manage_puzzles.reject_duplicate_puzzles(self.existing, duplicate)

    def test_duplicate_within_new_batch_is_rejected(self):
        duplicate = {
            **self.fresh[0],
            "id": "another-id",
            "anchor_word": "another-anchor",
        }
        with self.assertRaises(SystemExit):
            manage_puzzles.reject_duplicate_puzzles([], self.fresh + [duplicate])

    def test_generator_signature_ignores_center_and_order(self):
        first = self.existing[0]
        second = {
            **first,
            "center_letter": "g",
            "outside_letters": ["f", "e", "d", "c", "b", "a"],
        }
        self.assertEqual(
            generate_spelling_bee.puzzle_letter_set(first),
            generate_spelling_bee.puzzle_letter_set(second),
        )


if __name__ == "__main__":
    unittest.main()
