import base64
import json

import pytest

from message_encryptor import (
    base64_decrypt,
    base64_encrypt,
    caesar_decrypt,
    caesar_encrypt,
    decrypt_package,
    encrypt_message,
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

# ---------- Packages ----------

def make_package(payload):
    return base64.b64encode(json.dumps(payload).encode()).decode()


@pytest.mark.parametrize(
    "algorithm, shift",
    [("Caesar", 3), ("Caesar", -7), ("Reverse", None), ("Base64", None)],
)
def test_package_round_trip(algorithm, shift):
    package = encrypt_message("Café, Hello 123!", algorithm, shift)
    text, alg, got_shift = decrypt_package(package)
    assert text == "Café, Hello 123!"
    assert alg == algorithm
    assert got_shift == shift


def test_encrypt_unknown_algorithm_raises():
    with pytest.raises(ValueError, match="Unknown algorithm"):
        encrypt_message("hi", "ROT47")


def test_encrypt_caesar_without_shift_raises():
    with pytest.raises(ValueError, match="Shift"):
        encrypt_message("hi", "Caesar")


def test_decrypt_rejects_text_that_is_not_a_package():
    with pytest.raises(ValueError, match="Invalid encrypted package"):
        decrypt_package("not a package")


def test_decrypt_rejects_missing_msg():
    with pytest.raises(ValueError, match="Invalid encrypted package"):
        decrypt_package(make_package({"meta": {"alg": "Reverse"}}))


def test_decrypt_rejects_non_string_msg():
    with pytest.raises(ValueError, match="Invalid encrypted package"):
        decrypt_package(make_package({"msg": 123, "meta": {"alg": "Reverse"}}))


def test_decrypt_rejects_meta_that_is_not_an_object():
    with pytest.raises(ValueError, match="Invalid encrypted package"):
        decrypt_package(make_package({"msg": "abc", "meta": ["x"]}))


def test_decrypt_rejects_non_numeric_caesar_shift():
    package = make_package({"msg": "abc", "meta": {"alg": "Caesar", "shift": "x"}})
    with pytest.raises(ValueError, match="invalid Caesar shift"):
        decrypt_package(package)


def test_decrypt_rejects_unknown_algorithm():
    with pytest.raises(ValueError, match="Unknown algorithm in package"):
        decrypt_package(make_package({"msg": "abc", "meta": {"alg": "ROT47"}}))


def test_decrypt_rejects_undecodable_base64_message():
    with pytest.raises(ValueError, match="failed to decode"):
        decrypt_package(make_package({"msg": "abc", "meta": {"alg": "Base64"}}))


def test_decrypt_caesar_without_shift_defaults_to_zero():
    package = make_package({"msg": "abc", "meta": {"alg": "Caesar"}})
    assert decrypt_package(package) == ("abc", "Caesar", 0)