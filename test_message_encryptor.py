import pytest

from message_encryptor import (
    base64_decrypt,
    base64_encrypt,
    caesar_decrypt,
    caesar_encrypt,
    encryption_strength,
    reverse_decrypt,
    reverse_encrypt,
)


# ---------- Caesar ----------

def test_caesar_basic_shift():
    assert caesar_encrypt("abc", 3) == "def"


def test_caesar_wraps_around_alphabet():
    assert caesar_encrypt("xyz", 3) == "abc"


def test_caesar_keeps_case_and_non_letters():
    assert caesar_encrypt("Hello, World! 123", 5) == "Mjqqt, Btwqi! 123"


def test_caesar_negative_and_large_shifts():
    assert caesar_encrypt("abc", -1) == "zab"
    assert caesar_encrypt("abc", 29) == caesar_encrypt("abc", 3)


def test_caesar_leaves_non_ascii_letters_alone():
    assert caesar_encrypt("Café", 3) == "Fdié"


@pytest.mark.parametrize("shift", [0, 1, 3, 13, 25, -7, 100])
def test_caesar_round_trip(shift):
    message = "Café, Hello World! 123"
    assert caesar_decrypt(caesar_encrypt(message, shift), shift) == message


# ---------- Reverse ----------

def test_reverse_basic():
    assert reverse_encrypt("abc") == "cba"


def test_reverse_empty_string():
    assert reverse_encrypt("") == ""


def test_reverse_round_trip():
    assert reverse_decrypt(reverse_encrypt("Hello, World!")) == "Hello, World!"


# ---------- Base64 ----------

def test_base64_known_value():
    assert base64_encrypt("hello") == "aGVsbG8="


def test_base64_round_trip_with_unicode():
    message = "Café 😀"
    assert base64_decrypt(base64_encrypt(message)) == message


def test_base64_decrypt_invalid_padding_returns_none():
    assert base64_decrypt("abc") is None


def test_base64_decrypt_invalid_utf8_returns_none():
    assert base64_decrypt("/w==") is None  # decodes to the byte 0xFF


# ---------- Strength score ----------

def test_strength_empty_message_only_gets_algorithm_bonus():
    assert encryption_strength("", "Base64") == 5


def test_strength_longer_message_scores_higher():
    assert encryption_strength("a" * 20, "Base64") > encryption_strength("a", "Base64")


def test_strength_more_character_types_scores_higher():
    assert encryption_strength("aB3!", "Base64") > encryption_strength("abcd", "Base64")


def test_strength_larger_caesar_shift_scores_higher():
    assert encryption_strength("abc", "Caesar", 5) > encryption_strength("abc", "Caesar", 0)


@pytest.mark.parametrize("algorithm", ["Caesar", "Reverse", "Base64"])
def test_strength_stays_between_0_and_100(algorithm):
    score = encryption_strength("Aa1!" * 50, algorithm, 25)
    assert 0 <= score <= 100