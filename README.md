# 🔥 FIRE REGEX LOOPER 
Loops strings through a chained set of regex find/replace rules — originally built to fix TTS mispronunciations in Waze, but usable for any staged text-transformation pipeline.

## How it works
 Rules live in `source.csv` (tab-delimited), one rule per line:
 
| Column | Description |
|---|---|
| **Find** | A regex pattern to match |
| **Replace** | Replacement text — use `$1`, `$2`, etc. to reference capture groups |
| **Priority** | Lower numbers run first |

## Setup
Optional, improves color output on older Windows terminals
 ```bash
pip install colorama
```
 
## Usage
 ```bash
python fire_regex.py
```
You'll be asked to choose a mode:
 
- **Batch (`b`)** — runs a list of sample strings through the full pipeline and prints the step-by-step transformation for each. Edit the list in `strings.txt` to add or change cases.
- **Interactive (`i`)** — type in your own string and see it transformed on demand.
Each step prints which rule fired, its priority, and the before/after text, with the result of each transformation highlighted:
<img width="638" height="356" alt="image" src="https://github.com/user-attachments/assets/55d19aa5-1be5-41ab-acbb-b667bd53cc86" />

## Notes
- `source.csv` can be UTF-8, Windows-1257, or Windows-1252 — the script auto-detects encoding, since Excel often exports Baltic-language text in a non-UTF-8 codepage.
- A safety cap (`MAX_ITERATIONS`) stops the loop if two rules end up rewriting each other back and forth.
 
