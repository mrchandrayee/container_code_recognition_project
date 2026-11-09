import re

LETTER_VALUES = {
    "A":10,"B":12,"C":13,"D":14,"E":15,"F":16,"G":17,"H":18,
    "I":19,"J":20,"K":21,"L":23,"M":24,"N":25,"O":26,"P":27,
    "Q":28,"R":29,"S":30,"T":31,"U":32,"V":34,"W":35,"X":36,
    "Y":37,"Z":38
}

def normalize_code(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())

def is_iso6346_format(code: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{3}[UJZ]\d{7}", code))

def calculate_check_digit(code10: str):
    """Return ISO 6346 check digit for owner/category + 6-digit serial."""
    code = normalize_code(code10)
    if not re.fullmatch(r"[A-Z]{3}[UJZ]\d{6}", code):
        return None
    total = 0
    for i, char in enumerate(code):
        value = LETTER_VALUES[char] if char.isalpha() else int(char)
        total += value * (2 ** i)
    remainder = total % 11
    return remainder % 10

def validate_check_digit(code: str) -> bool:
    code = normalize_code(code)
    if not is_iso6346_format(code):
        return False
    expected = calculate_check_digit(code[:10])
    return expected == int(code[10])

def find_candidates(text: str):
    """Extract likely ISO 6346 codes from noisy OCR text."""
    raw = normalize_code(text)
    candidates = []
    # OCR can confuse O/0 and I/1; retain both raw and corrected candidate.
    for i in range(max(0, len(raw)-10)):
        chunk = raw[i:i+11]
        if len(chunk) != 11:
            continue
        fixed = chunk[:4].replace("0","O").replace("1","I") + chunk[4:].replace("O","0").replace("I","1")
        if is_iso6346_format(fixed) and fixed not in candidates:
            candidates.append(fixed)
    return candidates
