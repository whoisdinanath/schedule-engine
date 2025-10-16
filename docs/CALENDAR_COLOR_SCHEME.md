# Calendar PDF Color Scheme

## Overview
ScheduleCalendar.pdf uses a **course-type-based color scheme** to visually distinguish theory and practical sessions.

## Color Assignment
- **Theory courses**: Blue background (`#0000FF`) with black text
- **Practical courses**: Red background (`#FF0000`) with black text

## Implementation
Colors are assigned in `src/exporter/exporter.py` based on the `(TH)` or `(PR)` suffix in the course display name:

```python
# Detect course type from label suffix
if "(PR)" in course:
    color_map[course] = "#FF0000"  # Red
else:
    color_map[course] = "#0000FF"  # Blue
```

## Rationale
- **Simplicity**: Two distinct colors, easy to differentiate at a glance
- **Convention**: Blue often represents regular/theoretical content, red indicates hands-on/practical work
- **Readability**: Black text on both backgrounds ensures legibility

## Configuration
Color values are hardcoded in `exporter.py`. Document any changes in `config/calendar_config.py` comments.

## Related Files
- `src/exporter/exporter.py`: Color assignment logic
- `config/calendar_config.py`: Calendar configuration (includes color scheme documentation)
