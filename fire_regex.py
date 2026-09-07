import csv
import os
import re
import sys

# Enable ANSI escape sequences on Windows terminals
try:
    import colorama
    colorama.init()
except ImportError:
    # Fallback for Windows cmd/powershell to process ANSI codes natively
    os.system("")

SOURCE_FILE = "source.csv"
STRINGS_FILE = "strings.txt"
MAX_ITERATIONS = 200  # safety guard against infinite loops

# ANSI escape codes for terminal color formatting
CLR_WHITE = "\033[1;37m"
CLR_YELLOW = "\033[1;33m"
CLR_GREEN = "\033[1;32m"
CLR_RESET = "\033[0m"


def _read_text(path):
    """Try a chain of encodings, since Excel on Windows often saves tab-delimited
    files as Windows-1257 (Baltic) or plain Windows-1252 instead of UTF-8."""
    encodings_to_try = ["utf-8-sig", "utf-8", "cp1257", "cp1252", "latin-1"]
    last_error = None
    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            print(f"(loaded {path} using encoding: {enc})")
            return text
        except UnicodeDecodeError as e:
            last_error = e
            continue
    raise last_error


def load_test_strings(path):
    """Load one test string per line from a plain text file.
    Blank lines and lines starting with # (comments) are skipped."""
    if not os.path.exists(path):
        print(f"WARNING: {path} not found — creating an empty one. "
              f"Add one test string per line and re-run.")
        with open(path, "w", encoding="utf-8") as f:
            pass
        return []

    raw_text = _read_text(path)
    strings = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        strings.append(line)
    return strings


def load_rules(path):
    """Load (priority, compiled_pattern, python_replacement, raw_match, raw_replace) tuples."""
    rules = []
    raw_text = _read_text(path)
    reader = csv.reader(raw_text.splitlines(), delimiter="\t")
    for line_num, row in enumerate(reader, start=1):
        if not row or not row[0].strip():
            continue  # skip blank lines
        if row[0].lstrip().startswith("#"):
            continue  # skip comment lines
        if len(row) < 3:
            print(f"Skipping invalid row (line {line_num}, expected 3 columns): {row}")
            continue

        match, replace, priority_str = row[0], row[1], row[2]

        try:
            priority = int(priority_str.strip())
        except ValueError:
            print(f"Skipping row with bad priority (line {line_num}): {row}")
            continue

        # Convert Waze-style $1, $2 backreferences to Python's \1, \2
        python_replace = re.sub(r'\$(\d+)', r'\\\1', replace)

        try:
            # Enable re.UNICODE so Baltic diacritics match correctly in \w and \b
            pattern = re.compile(match, flags=re.UNICODE)
        except re.error as e:
            print(f"Skipping row with bad regex (line {line_num}): {match!r} -> {e}")
            continue

        rules.append((priority, pattern, python_replace, match, replace))

    # Sort by priority ascending (lowest priority number runs first)
    rules.sort(key=lambda r: r[0])
    return rules


def apply_rules(text, rules, verbose=True):
    """Repeatedly scan the rule list top-to-bottom (in priority order), restarting
    from the top of the list every time any rule matches and changes the text.
    Stops when a full pass produces no changes, or MAX_ITERATIONS is hit."""
    step = 0
    for _ in range(MAX_ITERATIONS):
        changed_this_pass = False
        for priority, pattern, python_replace, raw_match, raw_replace in rules:
            new_text = pattern.sub(python_replace, text)
            if new_text != text:
                step += 1
                if verbose:
                    print(f"  Step {step} — priority {priority}")
                    print(f"      RULE  : {raw_match}  ->  {raw_replace}")
                    print(f"      BEFORE: {text}")
                    # AFTER in Yellow
                    print(f"      {CLR_YELLOW}AFTER : {new_text}{CLR_RESET}")
                text = new_text
                changed_this_pass = True
                break  # restart scan from the top of the priority-sorted list
        if not changed_this_pass:
            break
    else:
        print(f"  WARNING: stopped after {MAX_ITERATIONS} iterations — possible infinite loop "
              f"(a rule may be matching and replacing with identical or cyclic text).")

    return text


def run_batch(rules, test_strings):
    if not test_strings:
        print(f"No test strings found in {STRINGS_FILE}. "
              f"Add one string per line and re-run.")
        return

    print(f"Running {len(test_strings)} sample strings through {len(rules)} rules\n")
    print("=" * 70)
    for original in test_strings:
        # INPUT in White (space below removed)
        print(f"\n{CLR_WHITE}INPUT: {original}{CLR_RESET}")
        result = apply_rules(original, rules, verbose=True)
        # RESULT in Green (space above removed)
        print(f"  {CLR_GREEN}RESULT: {original}  ->  {result}{CLR_RESET}")
        print("=" * 70)


def run_interactive(rules):
    while True:
        text = input("Enter the string to process (or press Enter to quit):\n").strip()
        if not text:
            break
        print(f"\n{CLR_WHITE}=== Transformation steps ==={CLR_RESET}")
        result = apply_rules(text, rules, verbose=True)
        # Final result in Green (space above removed)
        print(f"=== Final result ===")
        print(f"{CLR_GREEN}{result}{CLR_RESET}")
        print()


def main():
    rules = load_rules(SOURCE_FILE)
    print(f"Loaded {len(rules)} valid rules from {SOURCE_FILE}\n")

    mode = input("Run (b)atch test strings or (i)nteractive input? [b/i]: ").strip().lower()
    if mode == "i":
        run_interactive(rules)
    else:
        test_strings = load_test_strings(STRINGS_FILE)
        run_batch(rules, test_strings)

    input("\nDone. Press Enter to exit...")


if __name__ == "__main__":
    main()
