# BUGFIX: Progress Time Display Freezing

## Problem
Rich progress bar time display (elapsed/remaining) froze between generation updates instead of updating every second, causing poor UX during long-running generations.

## Root Cause
1. **Manual time calculation**: Custom time formatting (`time_display` field) only updated at end of each generation
2. **Low refresh rate**: Missing `refresh_per_second` parameter limited UI updates
3. **Blocking operations**: Long fitness evaluations prevented progress updates within generations

## Solution
1. **Use built-in Rich columns**: Replace custom time fields with `TimeElapsedColumn()` and `TimeRemainingColumn()` that auto-update
2. **Add refresh rate**: Set `refresh_per_second=10` for smoother UI updates
3. **Simplify logic**: Remove manual elapsed/remaining time calculations, let Rich handle it based on task progress

## Changes
**File**: `src/core/ga_scheduler.py`

### Before
```python
with Progress(
    ...
    TextColumn("[yellow]{task.fields[time_display]}[/yellow]"),
    ...
) as progress:
    task = progress.add_task(..., time_display="--:--/--:--")
    
    # Manual time calculation after each generation
    elapsed = time.time() - start_time
    time_display = f"{elapsed_mins}:{elapsed_secs:02d}/..."
    progress.update(task, time_display=time_display)
```

### After
```python
with Progress(
    ...
    TimeElapsedColumn(),  # Auto-updates every refresh
    TextColumn("/"),
    TimeRemainingColumn(),  # Auto-updates based on progress
    ...
    refresh_per_second=10,  # Update 10x per second
) as progress:
    task = progress.add_task(...)
    # Time updates automatically, no manual calculation needed
    progress.update(task, speed_display=speed_display)
```

## Benefits
- **Real-time updates**: Time display refreshes ~10x per second even during long generations
- **Less code**: Removed ~20 lines of manual time calculation
- **Better UX**: Users see live progress instead of frozen time counters
- **Accurate estimates**: Rich's built-in `TimeRemainingColumn` uses moving average for better predictions

## Testing
Run `python main.py` and observe:
- Time elapsed updates continuously (not frozen)
- Time remaining estimates adjust as generations complete
- Speed display (ms/gen or s/gen) updates after each generation
