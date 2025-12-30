"""
================================================================================
UNIVERSITY: ESOGU - Electrical & Electronics / Computer Engineering
COURSE:     Introduction to Microcomputers - Term Project
FILE:       home_automation/tests/test_protocol_ranges.py
DESCRIPTION:
    Unit tests for the protocol encoding/decoding functions.
    It checks if the values are within the valid ranges and if the 
    command formats (bits) are correct for Board 1 and Board 2.

AUTHOR:
    1. Yiğit Ata - 152120221106
================================================================================
"""

import unittest

from home_automation.protocol import board1, board2


class TestBoard1DesiredTempEncoding(unittest.TestCase):
    """
    Tests for Board #1 Temperature Encoding logic.
    """
    
    def test_valid_range_encodes(self):
        """Checks if valid temperature values are encoded correctly."""
        # Test distinct values: Min, Mid, Max
        for t in (10.0, 25.5, 50.0):
            low, high = board1.encode_set_desired_temp(t)

            # Check Prefix Bits:
            # Low byte must start with 10... (0x80)
            self.assertEqual(low & 0b1100_0000, 0b1000_0000)
            # High byte must start with 11... (0xC0)
            self.assertEqual(high & 0b1100_0000, 0b1100_0000)

            # Check Payload:
            # The data part must be between 0 and 63
            self.assertTrue(0 <= (low & 0b0011_1111) <= 63)
            self.assertTrue(0 <= (high & 0b0011_1111) <= 63)

    def test_invalid_range_rejected(self):
        """Checks if invalid temperature values raise an error."""
        # Requirements say temp must be 10.0 - 50.0
        # These values should fail:
        for t in (9.9, -5.0, 0.0, 50.1, 999.0):
            with self.assertRaises(ValueError):
                board1.encode_set_desired_temp(t)


class TestBoard2CurtainEncoding(unittest.TestCase):
    """
    Tests for Board #2 Curtain Encoding logic.
    """
    
    def test_scaled_range_ok(self):
        """Checks if valid percentage values (0-100%) are encoded correctly."""
        for pct in (0.0, 12.3, 50.0, 100.0):
            low, high = board2.encode_set_desired_curtain(pct, mode="scaled_0_63")
            
            # Check Prefix Bits
            self.assertEqual(low & 0b1100_0000, 0b1000_0000)
            self.assertEqual(high & 0b1100_0000, 0b1100_0000)
            
            # Check Data Bits
            self.assertTrue(0 <= (low & 0b0011_1111) <= 63)
            self.assertTrue(0 <= (high & 0b0011_1111) <= 63)

        # Test Boundary Values specifically
        # 0% should result in 0
        low0, high0 = board2.encode_set_desired_curtain(0.0, mode="scaled_0_63")
        self.assertEqual(low0 & 0b0011_1111, 0)
        self.assertEqual(high0 & 0b0011_1111, 0)

        # 100% should result in max value (63)
        low100, high100 = board2.encode_set_desired_curtain(100.0, mode="scaled_0_63")
        self.assertEqual(low100 & 0b0011_1111, 0)
        self.assertEqual(high100 & 0b0011_1111, 63)

    def test_scaled_range_rejected(self):
        """Checks if invalid percentages are rejected."""
        for pct in (-1.0, 100.1, 1000.0):
            with self.assertRaises(ValueError):
                board2.encode_set_desired_curtain(pct, mode="scaled_0_63")

    def test_raw_range_ok_and_rejected(self):
        """Checks valid and invalid values for 'raw' mode."""
        # Valid value (Max raw is 63)
        low, high = board2.encode_set_desired_curtain(63.0, mode="raw_0_63")
        self.assertEqual(high & 0b0011_1111, 63)

        # Invalid values (>63 or negative)
        for v in (-1.0, 63.1, 80.0):
            with self.assertRaises(ValueError):
                board2.encode_set_desired_curtain(v, mode="raw_0_63")


if __name__ == "__main__":
    unittest.main()