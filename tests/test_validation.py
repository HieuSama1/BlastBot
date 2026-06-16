import unittest

from utils.error_handler import ValidationError, validate_number_range, validate_string_length


class ValidationHelperTests(unittest.TestCase):
    def test_validate_string_length_strips_whitespace(self):
        self.assertEqual(validate_string_length("  hello  "), "hello")

    def test_validate_string_length_raises_on_short_input(self):
        with self.assertRaises(ValidationError):
            validate_string_length(" ", min_len=1)

    def test_validate_number_range_returns_value(self):
        self.assertEqual(validate_number_range(5, 1, 10), 5)

    def test_validate_number_range_raises_out_of_bounds(self):
        with self.assertRaises(ValidationError):
            validate_number_range(11, 1, 10)


if __name__ == "__main__":
    unittest.main()