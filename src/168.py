"""Kernmodul fuer df-168.

Das Modul stellt kleine, konkrete Zahlwerkzeuge rund um die Missionszahl 168
bereit. Es ist eigenstaendig und nutzt nur die Python-Standardbibliothek.
"""

from __future__ import annotations

from math import gcd
from typing import Dict, List

MISSION_NUMBER = 168


def _validate_positive_int(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("value must be an int")
    if value <= 0:
        raise ValueError("value must be > 0")
    return value


def prime_factors(value: int) -> Dict[int, int]:
    """Gibt die Primfaktorzerlegung als {prime: exponent} zurueck."""
    n = _validate_positive_int(value)
    factors: Dict[int, int] = {}

    while n % 2 == 0:
        factors[2] = factors.get(2, 0) + 1
        n //= 2

    p = 3
    while p * p <= n:
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
        p += 2

    if n > 1:
        factors[n] = factors.get(n, 0) + 1

    return factors


def divisors(value: int) -> List[int]:
    """Gibt alle positiven Teiler sortiert aufsteigend zurueck."""
    factors = prime_factors(value)
    result = [1]

    for prime, exponent in factors.items():
        current = list(result)
        for power in range(1, exponent + 1):
            result.extend(d * (prime ** power) for d in current)

    return sorted(result)


def classify_against_168(value: int) -> dict:
    """Beschreibt die Beziehung einer Zahl zur Missionszahl 168."""
    n = _validate_positive_int(value)
    common = gcd(n, MISSION_NUMBER)
    return {
        "value": n,
        "mission": MISSION_NUMBER,
        "is_equal": n == MISSION_NUMBER,
        "is_divisor_of_168": MISSION_NUMBER % n == 0,
        "is_multiple_of_168": n % MISSION_NUMBER == 0,
        "gcd_with_168": common,
        "shares_all_168_prime_bases": set(prime_factors(n)).issubset(set(prime_factors(MISSION_NUMBER))),
    }
# [CRUX-MK]
