# Console Output Formatting

## Overview

Centralized console output formatting utilities for consistent, terminal-width-aware output across the codebase.

## Module

`src/utils/console.py`

## Key Features

- **Terminal-width awareness**: Automatically detects terminal width (60-120 char range)
- **tqdm compatibility**: Uses `tqdm.write()` for proper progress bar interleaving
- **Consistent styling**: No hardcoded widths, no emoji clutter
- **Simple API**: Header, separator, info, box functions

## Core Functions

### `get_terminal_width() -> int`
Returns current terminal width with fallback to 80. Clamped between 60-120 chars.

### `write_separator(char="=", width=None)`
Prints horizontal line. Auto-detects width if not specified.

### `write_header(title, width=None)`
Prints centered title with top/bottom separators.

### `write_info(message, indent=0)`
Prints info message with optional indentation.

### `write_section(title, prefix="", width=None)`
Prints section header with dashed separators.

### `write_box(title, content, width=None)`
Prints boxed content with title and content lines.

## Usage Examples

```python
from src.utils.console import write_header, write_separator, write_info

# Header with auto-width
write_header("WORKFLOW COMPLETE")

# Simple info messages
write_info("Loading data...")
write_info("  Courses: 42")
write_info("  Groups: 15")

# Separator
write_separator()

# Section header
write_section("Step 1: Data Loading", prefix="[1/5]")
```

## Migration Notes

**Before:**
```python
tqdm.write("=" * 60)
tqdm.write("TITLE".center(60))
tqdm.write("=" * 60)
```

**After:**
```python
from src.utils.console import write_header
write_header("TITLE")
```

## Benefits

1. **No magic numbers**: Terminal width auto-detected
2. **Consistent styling**: All headers/separators look uniform
3. **Maintainable**: Change formatting once, applies everywhere
4. **Clean**: No emoji or hardcoded Unicode characters
5. **Flexible**: Works with any terminal width (60-120)

## Files Updated

- `main.py`: Final results display
- `src/workflows/standard_run.py`: Workflow sections
- `src/validation/input_validator.py`: Validation reports
- `scripts/show_config.py`: Config display
- `scripts/show_soft_config.py`: Soft constraints
- `scripts/show_time_config.py`: Time configuration
- `src/ga/group_hierarchy.py`: Analysis output
- `src/ga/course_group_pairs.py`: Pair generation output

## Design Principles

- **Width awareness**: Terminal size matters
- **tqdm first**: Always use `tqdm.write()` for output
- **No decoration**: Avoid emojis, keep ASCII-only
- **Readability**: Clear visual hierarchy
- **Simplicity**: Minimal API surface
