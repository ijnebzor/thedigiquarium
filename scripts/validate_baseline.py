#!/usr/bin/env python3
"""
Baseline Validation Script
Validates baseline result JSON files against strict criteria
Exit code: 0 for pass, 1 for fail
"""

import sys
import json
import re
from pathlib import Path
from typing import Tuple, List


class BaselineValidator:
    """Validates baseline assessment results"""

    def __init__(self, baseline_file: str):
        self.file = Path(baseline_file)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """Run all validation checks. Returns True if valid, False otherwise."""
        if not self._check_file_exists():
            return False
        if not self._check_valid_json():
            return False
        if not self._check_structure():
            return False
        if not self._check_question_count():
            return False
        if not self._check_responses():
            return False
        if not self._check_data_quality():
            return False
        return True

    def _check_file_exists(self) -> bool:
        """Verify file exists and is readable"""
        if not self.file.exists():
            self.errors.append(f"File not found: {self.file}")
            return False
        if not self.file.is_file():
            self.errors.append(f"Path is not a file: {self.file}")
            return False
        if self.file.stat().st_size == 0:
            self.errors.append(f"File is empty: {self.file}")
            return False
        return True

    def _check_valid_json(self) -> bool:
        """Verify file contains valid JSON"""
        try:
            with open(self.file) as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False

    def _check_structure(self) -> bool:
        """Verify baseline data has required structure"""
        required_fields = ['tank_name', 'gender', 'started', 'completed', 'questions_answered', 'responses']
        for field in required_fields:
            if field not in self.data:
                self.errors.append(f"Missing required field: {field}")
                return False

        if not isinstance(self.data['responses'], list):
            self.errors.append("'responses' field must be a list")
            return False

        return True

    def _check_question_count(self) -> bool:
        """Verify all 14 questions are present"""
        expected_count = 14
        actual_count = len(self.data['responses'])

        if actual_count != expected_count:
            self.errors.append(
                f"Question count mismatch: expected {expected_count}, got {actual_count}"
            )
            return False

        # Verify all question numbers are present
        question_nums = {r.get('question_num') for r in self.data['responses']}
        expected_nums = set(range(1, 15))
        if question_nums != expected_nums:
            missing = expected_nums - question_nums
            self.errors.append(f"Missing question numbers: {sorted(missing)}")
            return False

        return True

    def _check_responses(self) -> bool:
        """Verify all responses are present and non-empty"""
        all_valid = True

        for i, response in enumerate(self.data['responses'], 1):
            # Check required fields
            if 'response' not in response:
                self.errors.append(f"Question {i}: missing 'response' field")
                all_valid = False
                continue

            resp_text = response.get('response', '')

            # Check for empty response
            if not resp_text or not resp_text.strip():
                self.errors.append(f"Question {i}: empty response")
                all_valid = False
                continue

            # Check for obvious error indicators
            if any(x in resp_text.lower() for x in ['error', 'failed', 'exception']):
                if not self._looks_like_legitimate_response(resp_text):
                    self.warnings.append(f"Question {i}: response contains error keyword")

            # Check for garbage patterns
            if self._is_garbage_response(resp_text):
                self.errors.append(f"Question {i}: response appears to be garbage/malformed")
                all_valid = False
                continue

        return all_valid

    def _check_data_quality(self) -> bool:
        """Verify response quality and coherence"""
        all_valid = True

        for i, response in enumerate(self.data['responses'], 1):
            resp_text = response.get('response', '')

            # Check for minimum length (should have some substance)
            if len(resp_text) < 10:
                self.warnings.append(f"Question {i}: response is very short ({len(resp_text)} chars)")

            # Check for coherence
            if not self._is_coherent_text(resp_text):
                self.errors.append(f"Question {i}: response lacks coherence")
                all_valid = False
                continue

            # Check for anomalous values if mentioned (negative valences, extreme scores)
            if self._contains_anomalies(resp_text):
                self.warnings.append(f"Question {i}: response contains potentially anomalous values")

            # Check for timestamp
            if 'timestamp' not in response:
                self.warnings.append(f"Question {i}: missing timestamp")

        return all_valid

    @staticmethod
    def _looks_like_legitimate_response(text: str) -> bool:
        """Check if error keywords appear in legitimate context"""
        # True if it's discussing error/failure as a topic, not an actual error
        legitimate_contexts = [
            'no error', 'error is', 'learn from error', 'handle.*error', 'make error'
        ]
        for pattern in legitimate_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def _is_garbage_response(text: str) -> bool:
        """Detect garbage/malformed responses"""
        # Check for excessive repetition
        words = text.split()
        if len(words) > 3:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # More than 70% same word
                return True

        # Check for random characters/encoding issues
        if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text):
            return True

        # Check for excessive special characters
        special_count = sum(1 for c in text if not c.isalnum() and c.isascii() and c not in ' .,!?\'"():-')
        if len(text) > 20 and special_count / len(text) > 0.4:
            return True

        return False

    @staticmethod
    def _is_coherent_text(text: str) -> bool:
        """Check if response is coherent English/natural language"""
        # Remove common punctuation and check word count
        words = text.split()
        if len(words) < 2:
            return False

        # Check that not all words are single characters (garbage pattern)
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 1.5:  # Too short on average
            return False

        # Check for basic sentence structure
        has_vowels = any(c.lower() in 'aeiou' for c in text)
        if not has_vowels:
            return False

        return True

    @staticmethod
    def _contains_anomalies(text: str) -> bool:
        """Detect potentially anomalous values"""
        anomalies = [
            r'-\d{3,}',  # Large negative numbers
            r'nan|inf|null|undefined',  # Invalid numeric values
        ]
        for pattern in anomalies:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def report(self) -> str:
        """Generate validation report"""
        lines = []
        lines.append(f"\nValidation Report: {self.file.name}")
        lines.append("=" * 70)

        if not self.errors and not self.warnings:
            lines.append("Status: PASS - All validation checks passed")
            return "\n".join(lines) + "\n"

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"  ✗ {error}")

        if self.warnings:
            lines.append(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")

        if self.errors:
            lines.append("\nStatus: FAIL - Validation errors found")
        else:
            lines.append("\nStatus: PASS (with warnings)")

        return "\n".join(lines) + "\n"

    def is_valid(self) -> bool:
        """Return True if no errors (warnings OK)"""
        return len(self.errors) == 0


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: validate_baseline.py <baseline_json_file>")
        print("Exit codes: 0 = valid, 1 = invalid")
        sys.exit(1)

    baseline_file = sys.argv[1]

    validator = BaselineValidator(baseline_file)
    validator.validate()
    print(validator.report())

    sys.exit(0 if validator.is_valid() else 1)


if __name__ == '__main__':
    main()
