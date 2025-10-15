# Thesis-Ready Figure Styling: Quick Reference

## Color Palette (Seaborn-Inspired)

### Primary Colors
| Use Case | Color Name | Hex Code | RGB |
|----------|-----------|----------|-----|
| Hard Constraints | Red | `#C44E52` | (196, 78, 82) |
| Soft Constraints | Green | `#55A868` | (85, 168, 104) |
| Diversity | Orange | `#DD8452` | (221, 132, 82) |
| Population | Blue | `#4C72B0` | (76, 114, 176) |

### Extended Palette (Multi-line Plots)
```
#4C72B0  #DD8452  #55A868  #C44E52  #8172B3
#937860  #DA8BC3  #8C8C8C  #CCB974  #64B5CD
```

## Font Specifications

### Hierarchy
```
Figure Title:    14pt, Bold, Times New Roman
Plot Title:      13pt, Bold, Times New Roman
Axis Labels:     12pt, Regular, Times New Roman
Tick Labels:     10pt, Regular, Times New Roman
Legend:          10pt, Regular, Times New Roman
Annotations:     9-11pt, Regular, Times New Roman
```

## Figure Dimensions

### Standard Sizes
| Plot Type | Width | Height | Aspect Ratio |
|-----------|-------|--------|--------------|
| Single Plot | 9" | 5" | 1.8:1 |
| Individual Constraint | 10" | 5.5" | 1.82:1 |
| 2×2 Grid | 14" | 11" | 1.27:1 |
| Multi-line Combined | 12" | 7" | 1.71:1 |
| Bar Summary | 11" | 6.5" | 1.69:1 |

## Line Styles

### Markers
- Hard constraints: Circle `o`
- Soft constraints: Square `s`
- Diversity: Triangle up `^`

### Line Widths
- Main trend lines: 2.5pt
- Multi-line plots: 2.2pt
- Reference lines (avg/max): 1.5pt

### Marker Frequency
```python
markevery = max(1, len(data) // 15)  # ~15 markers per line
```

## Grid Specifications

```python
grid.color: '#CCCCCC'
grid.linestyle: '--'
grid.linewidth: 0.8
grid.alpha: 0.5
```

## Legend Configuration

```python
framealpha: 0.95
edgecolor: '#CCCCCC'
fontsize: 9-10pt
location: upper right or bbox_to_anchor=(1.02, 1)
```

## Export Settings

### PDF Output
```python
dpi: 300
format: 'pdf'
bbox_inches: 'tight'
pdf.fonttype: 42  # TrueType (LaTeX-editable)
facecolor: 'white'
```

## Updated Files

1. ✅ `src/exporter/thesis_style.py` — **NEW**: Central styling module
2. ✅ `src/exporter/plotpareto.py` — Updated with thesis style
3. ✅ `src/exporter/plothard.py` — Updated with thesis style
4. ✅ `src/exporter/plotsoft.py` — Updated with thesis style
5. ✅ `src/exporter/plotdiversity.py` — Updated with thesis style
6. ✅ `src/exporter/plot_detailed_constraints.py` — Updated with thesis style

## Compatibility

### LaTeX/Overleaf
- Font type 42 (TrueType) ensures editability
- Times New Roman matches standard thesis templates
- 300 DPI suitable for print

### PowerPoint/Presentations
- High contrast colors work on projectors
- Large font sizes readable from distance
- Clean gridlines don't distract

### Printing
- 300 DPI resolution
- CMYK-friendly color palette
- Black text on white background

## Code Examples

### Creating a Thesis Figure
```python
from .thesis_style import create_thesis_figure, format_axis, save_figure, get_color

fig, ax = create_thesis_figure(1, 1, figsize=(9, 5))
ax.plot(data, color=get_color('blue'), linewidth=2.5)
format_axis(ax, xlabel="Generation", ylabel="Value", 
            title="My Plot", legend=True)
save_figure(fig, "output/my_plot.pdf")
```

### Using Color Palette
```python
from .thesis_style import PALETTE, get_color

# Single color
ax.plot(x, y, color=get_color('red'))

# Multiple lines
for i, dataset in enumerate(datasets):
    ax.plot(dataset, color=PALETTE[i])
```

## Visual Standards Checklist

- [ ] Times New Roman font throughout
- [ ] 300 DPI resolution
- [ ] Seaborn color palette
- [ ] Consistent line widths (2.2-2.5pt)
- [ ] Appropriate markers with spacing
- [ ] Professional gridlines (dashed, subtle)
- [ ] Clean legends (no box, or subtle frame)
- [ ] Axis labels present and readable
- [ ] Title uses proper capitalization
- [ ] No overlapping text
- [ ] White background, dark text
- [ ] PDF format with Type 42 fonts
