# Rich Library Migration

## Overview

Migrated from `tqdm` to `rich` library for console output and progress bars, following rich's design philosophy of direct API usage without custom wrappers.

## Changes Made

### Dependencies
- **Removed**: `tqdm>=4.66.0`
- **Added**: `rich>=13.0.0`

### Deleted Files
- `src/utils/console.py` - Custom wrapper utility removed; use rich directly

### Core Updates

#### 1. **main.py**
- Import `Console` from rich
- Replace `write_header()` → `console.rule()`
- Replace `write_info()` → `console.print()` with markup
- Replace `write_separator()` → `console.rule()`
- Added colored, styled output with emojis

#### 2. **src/core/ga_scheduler.py**
- Import `Console`, `Progress` from rich
- Replace tqdm progress bars with rich `Progress` contexts
- `initialize_population()`: Two-phase progress (init → eval)
- `evolve()`: Main evolution progress bar with time elapsed
- `_log_generation_details()`: Colored constraint breakdowns

#### 3. **src/workflows/standard_run.py**
- Replace all console utilities with rich
- Loading phase: `Progress` with spinner
- Validation phase: `Progress` with time elapsed
- Report generation: `Progress` with spinner
- Styled section headers with `console.rule()`
- Colored metrics output

#### 4. **src/ga/population.py**
- Removed tqdm progress bar (redundant with higher-level progress)
- Simple loop—progress shown by ga_scheduler

#### 5. **src/validation/input_validator.py**
- Import `Console`, `Panel` from rich
- `print_report()`: Styled validation reports with colors
- Error/warning differentiation with emojis (✗, ⚠, ✓)

### Rich Design Philosophy

**Direct API Usage**:
```python
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn

console = Console()
console.print("[bold cyan]Message[/bold cyan]")

with Progress(...) as progress:
    task = progress.add_task("Description", total=100)
    progress.advance(task)
```

**No Custom Wrappers**: Rich's API is expressive enough—use it directly.

### Color Scheme

- **Cyan**: Info, data loading, metrics
- **Green**: Success, completion
- **Yellow**: Warnings, hard constraints
- **Blue**: Soft constraints
- **Red**: Errors
- **Magenta**: Special tasks (reports)
- **Dim**: Secondary info

### Progress Bar Patterns

**Spinner + Text**:
```python
Progress(
    SpinnerColumn(),
    TextColumn("[bold cyan]{task.description}"),
    TimeElapsedColumn(),
    console=console,
    transient=True  # Clears after completion
)
```

**Bar + Counter**:
```python
Progress(
    SpinnerColumn(),
    TextColumn("{task.description}"),
    BarColumn(),
    TextColumn("[cyan]{task.completed}/{task.total}"),
    console=console
)
```

## Migration Benefits

1. **Beautiful Output**: Rich styling, colors, emojis
2. **Better UX**: Transient progress bars, clear hierarchies
3. **Simpler Code**: No custom wrappers, direct API
4. **Consistent**: One library for all console output
5. **Modern**: Active development, rich ecosystem

## Breaking Changes

- Scripts in `scripts/` may need updates if they import `src.utils.console`
- Any external tools importing console utilities will break
- `tqdm.write()` → `console.print()`

## Future Enhancements

- Use `rich.table.Table` for tabular data
- Use `rich.panel.Panel` for grouped info
- Use `rich.tree.Tree` for hierarchy displays
- Use `rich.syntax.Syntax` for code highlighting

## Notes

- Progress bars use `transient=True` to auto-clear after completion
- Console instance created per-module (no global state)
- Rich handles terminal width automatically
- Markup syntax: `[style]text[/style]` (e.g., `[bold red]Error[/bold red]`)
