from container_reader.iso6346 import normalize_code, calculate_check_digit, is_iso6346_format, validate_check_digit

def test_normalize_and_format():
    code=normalize_code("KKTU 779726 1")
    assert code=="KKTU7797261"
    assert is_iso6346_format(code)

def test_check_digit_calculation():
    assert calculate_check_digit("CSQU305438") == 3
    assert validate_check_digit("CSQU3054383")

def test_invalid_check_digit():
    assert not validate_check_digit("CSQU3054384")
