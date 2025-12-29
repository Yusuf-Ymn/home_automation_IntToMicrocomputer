"""Protokol encoding/decoding fonksiyonlarının doğruluğunu test eder.

Board1 ve Board2 için değer aralıklarını ve komut formatlarını kontrol eder.
"""
import unittest

from home_automation.protocol import board1, board2


class TestBoard1DesiredTempEncoding(unittest.TestCase):
    """Board #1 sıcaklık encoding testleri."""
    
    def test_valid_range_encodes(self):
        """Geçerli sıcaklık değerlerinin doğru encode edildiğini test eder."""
        for t in (10.0, 25.5, 50.0):
            low, high = board1.encode_set_desired_temp(t)

            # Low: 10xxxxxx, High: 11xxxxxx formatında olmalı
            self.assertEqual(low & 0b1100_0000, 0b1000_0000)
            self.assertEqual(high & 0b1100_0000, 0b1100_0000)

            # Payload 0-63 arasında olmalı
            self.assertTrue(0 <= (low & 0b0011_1111) <= 63)
            self.assertTrue(0 <= (high & 0b0011_1111) <= 63)

    def test_invalid_range_rejected(self):
        """Geçersiz sıcaklık değerlerinin reddedildiğini test eder."""
        for t in (9.9, -5.0, 0.0, 50.1, 999.0):
            with self.assertRaises(ValueError):
                board1.encode_set_desired_temp(t)


class TestBoard2CurtainEncoding(unittest.TestCase):
    """Board #2 perde encoding testleri."""
    
    def test_scaled_range_ok(self):
        """Scaled mod için geçerli değerlerin doğru encode edildiğini test eder."""
        for pct in (0.0, 12.3, 50.0, 100.0):
            low, high = board2.encode_set_desired_curtain(pct, mode="scaled_0_63")
            self.assertEqual(low & 0b1100_0000, 0b1000_0000)
            self.assertEqual(high & 0b1100_0000, 0b1100_0000)
            self.assertTrue(0 <= (low & 0b0011_1111) <= 63)
            self.assertTrue(0 <= (high & 0b0011_1111) <= 63)

        # Sınır değerleri test et
        low0, high0 = board2.encode_set_desired_curtain(0.0, mode="scaled_0_63")
        self.assertEqual(low0 & 0b0011_1111, 0)
        self.assertEqual(high0 & 0b0011_1111, 0)

        low100, high100 = board2.encode_set_desired_curtain(100.0, mode="scaled_0_63")
        self.assertEqual(low100 & 0b0011_1111, 0)
        self.assertEqual(high100 & 0b0011_1111, 63)

    def test_scaled_range_rejected(self):
        """Scaled mod için geçersiz değerlerin reddedildiğini test eder."""
        for pct in (-1.0, 100.1, 1000.0):
            with self.assertRaises(ValueError):
                board2.encode_set_desired_curtain(pct, mode="scaled_0_63")

    def test_raw_range_ok_and_rejected(self):
        """Raw mod için geçerli ve geçersiz değerleri test eder."""
        # Geçerli değer
        low, high = board2.encode_set_desired_curtain(63.0, mode="raw_0_63")
        self.assertEqual(high & 0b0011_1111, 63)

        # Geçersiz değerler
        for v in (-1.0, 63.1, 80.0):
            with self.assertRaises(ValueError):
                board2.encode_set_desired_curtain(v, mode="raw_0_63")


if __name__ == "__main__":
    unittest.main()
