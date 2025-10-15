# Thesis-Ready Plotting System

## Overview
All exporter plotting modules have been updated to use a **Seaborn-inspired theme** with **Times New Roman font** for professional thesis presentation.

## Key Changes

### 1. New Module: `thesis_style.py`
Central styling configuration that provides:
- **Seaborn color palette**: Professionally curated colors (`#4C72B0` blue, `#DD8452` orange, etc.)
- **Times New Roman font**: Applied globally via matplotlib rcParams
- **Grid styling**: Subtle, thesis-appropriate gridlines
- **High DPI**: 300 DPI for publication-quality PDFs
- **Helper functions**:
  - `create_thesis_figure()`: Creates styled figures with appropriate sizing
  - `format_axis()`: Consistent axis formatting (labels, titles, legends)
  - `save_figure()`: Saves PDFs with optimal settings
  - `get_color()`: Access predefined color palette

### 2. Updated Plotting Modules

#### `plotpareto.py`
- Seaborn colors for population (blue-orange) and Pareto front (red)
- Times New Roman font throughout
- Enhanced markers with proper spacing
- Improved alpha/transparency for overlapping points
- Consistent legend styling

#### `plothard.py`
- Red theme for hard constraints (violation = bad)
- Markers at intervals for trend visibility
- Professional grid and axis styling

#### `plotsoft.py`
- Green theme for soft constraints (penalties)
- Square markers for distinction from hard constraints
- Consistent styling with other plots

#### `plotdiversity.py`
- Orange theme for diversity metric
- Triangle markers for visual distinction
- Clear axis labels and grid

#### `plot_detailed_constraints.py`
- Individual constraint plots with consistent color mapping
- Combined plots using extended Seaborn palette
- Statistics summary bars with edge colors
- Proper legend placement for multi-line plots
- Dashboard-style constraint summary

### 3. Visual Improvements

**Before:**
- Inconsistent colors across plots
- Basic matplotlib default styling
- Mixed font families
- Variable DPI and sizing

**After:**
- Unified Seaborn-inspired color scheme
- Times New Roman throughout (thesis-standard)
- 300 DPI PDFs for print quality
- Consistent sizing and spacing
- Professional gridlines and axes
- Publication-ready legends

### 4. Technical Details

**Font Configuration:**
```python
'font.family': 'serif',
'font.serif': ['Times New Roman', 'DejaVu Serif', 'Liberation Serif'],
'font.size': 11,
'axes.titlesize': 13,
'axes.labelsize': 12,
```

**PDF Settings:**
```python
'savefig.dpi': 300,
'pdf.fonttype': 42,  # TrueType (editable in LaTeX)
```

**Color Palette:**
- Blue: `#4C72B0` (primary)
- Orange: `#DD8452`
- Green: `#55A868`
- Red: `#C44E52`
- Purple: `#8172B3`
- + 7 more colors for multi-line plots

### 5. Usage

The styling is **automatically applied** when any plotting module is imported:

```python
from .thesis_style import apply_thesis_style
apply_thesis_style()  # Called at module level
```

No changes needed to existing function calls. All exports maintain backward compatibility.

### 6. Benefits

1. **Thesis-ready**: Meets academic publication standards
2. **Consistent**: All figures share visual language
3. **Professional**: Seaborn-quality aesthetics
4. **Editable**: TrueType fonts work in LaTeX/Overleaf
5. **High-quality**: 300 DPI for print publications
6. **Accessible**: Clear visual hierarchy and readable text

## Testing

Run `main.py` to generate all figures with new styling:
```powershell
python main.py
```

Check `output/evaluation_<timestamp>/` for thesis-ready PDFs.

## Future Enhancements

- Color palette customization via config file
- Alternative font options (Helvetica, Arial)
- Dark mode theme for presentations
- SVG export option for vector graphics
