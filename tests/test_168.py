import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# `from 168 import ...` ist in Python syntaktisch ungueltig, weil Modulnamen in
# Import-Statements gueltige Bezeichner sein muessen. Fuer eine wirklich gruen
# laufende Pruefung wird deshalb das Modul `168.py` ueber importlib geladen.
import importlib

m168 = importlib.import_module("168")

prime_factors = m168.prime_factors
divisors = m168.divisors
classify_against_168 = m168.classify_against_168
MISSION_NUMBER = m168.MISSION_NUMBER


def test_prime_factors_and_divisors_of_168():
    assert MISSION_NUMBER == 168
    assert prime_factors(168) == {2: 3, 3: 1, 7: 1}
    assert divisors(168) == [1, 2, 3, 4, 6, 7, 8, 12, 14, 21, 24, 28, 42, 56, 84, 168]


def test_classify_against_168():
    exact = classify_against_168(168)
    assert exact["is_equal"] is True
    assert exact["is_divisor_of_168"] is True
    assert exact["is_multiple_of_168"] is True
    assert exact["gcd_with_168"] == 168

    partial = classify_against_168(56)
    assert partial["is_equal"] is False
    assert partial["is_divisor_of_168"] is True
    assert partial["is_multiple_of_168"] is False
    assert partial["gcd_with_168"] == 56
    assert partial["shares_all_168_prime_bases"] is True
