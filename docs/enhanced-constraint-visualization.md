# Enhanced Constraint Visualization with Distinct Colors

## Changes Made

### Problem
- All hard constraints used similar red/orange shades
- All soft constraints used similar green shades  
- Legend was difficult to read and distinguish lines

### Solution

#### 1. Distinct Color Palettes

**Hard Constraints (12 distinct colors across color families):**
- Red (#E74C3C)
- Blue (#3498DB)
- Green (#2ECC71)
- Orange (#F39C12)
- Purple (#9B59B6)
- Dark Orange (#E67E22)
- Turquoise (#1ABC9C)
- Pink (#E91E63)
- Dark Gray (#34495E)
- Yellow (#F1C40F)
- Dark Turquoise (#16A085)
- Dark Purple (#8E44AD)

**Soft Constraints (12 distinct colors across color families):**
- Green (#2ECC71)
- Red (#E74C3C)
- Blue (#3498DB)
- Orange (#F39C12)
- Purple (#9B59B6)
- Turquoise (#1ABC9C)
- Pink (#E91E63)
- Yellow (#F1C40F)
- Dark Gray (#34495E)
- Dark Orange (#E67E22)
- Dark Turquoise (#16A085)
- Dark Purple (#8E44AD)

#### 2. Multiple Visual Distinctions

Each constraint now has THREE distinguishing features:

**Colors**: 12 distinct colors spanning the spectrum
**Line Styles**: 
- Solid (-)
- Dashed (--)
- Dash-dot (-.)
- Dotted (:)

**Markers**:
- Circle (o)
- Square (s)
- Triangle (^)
- Diamond (D)
- Inverted Triangle (v)
- Pentagon (p)
- Star (*)
- X (X)
- Plus-filled (P)
- Hexagon (h)
- Plus (+)
- X-small (x)

**Marker Frequency**: Markers shown at intervals (every 10% of data points) to avoid cluttering

#### 3. Improved Legend

- Increased font size (10pt)
- Better positioning (outside plot area)
- Semi-transparent background (framealpha=0.9)
- Title in bold with larger font (14pt)
- Axis labels in 12pt font

#### 4. Higher Quality Output

- DPI increased to 300 (from default 100)
- Better for printing and presentations

## Benefits

✅ **12+ constraints can be distinguished** (previously ~3-4 max)
✅ **Three-way visual encoding** (color + linestyle + marker)
✅ **Color-blind friendly** (linestyle and markers provide backup)
✅ **Print-friendly** (works in grayscale too)
✅ **Professional quality** (300 DPI output)
✅ **Clear legend** (larger text, better spacing)

## Example Use Cases

### Identifying Specific Constraints
1. **By Color**: Quickly spot red vs blue vs green families
2. **By Line Style**: Distinguish solid from dashed from dotted
3. **By Marker**: Identify circles vs squares vs triangles

### Presentations
- High DPI makes plots crisp on projectors
- Distinct colors visible from distance
- Legend readable even when plot is small

### Reports
- Prints clearly in both color and grayscale
- Professional appearance
- Easy to reference in text ("the blue dashed line with triangles")

## Testing

Run the GA with:
```bash
python main.py
```

Check the output plots in:
- `output/evaluation_<timestamp>/hard/all_hard_constraints.pdf`
- `output/evaluation_<timestamp>/soft/all_soft_constraints.pdf`

## Before/After Comparison

**Before**: 
- All hard constraints = red/orange family (hard to distinguish)
- All soft constraints = green family (hard to distinguish)
- Single line style (solid)
- Single marker type (circle)

**After**:
- 12 distinct color families
- 4 different line styles cycling
- 12 different marker types cycling
- Multiple visual cues for each constraint

## Color Vision Accessibility

The combination of:
- **Line styles** (solid, dashed, dotted, dash-dot)
- **Marker shapes** (12 different shapes)
- **Colors** (12 distinct hues)

Ensures that even users with color vision deficiencies can distinguish between constraints using the patterns and shapes.
