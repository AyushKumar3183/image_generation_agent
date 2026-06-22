"""Mandatory fashion image quality rules injected into every generation request."""

FASHION_QUALITY_RULES = """
FASHION IMAGE QUALITY REQUIREMENTS (MANDATORY — HIGHEST PRIORITY):

1. BACKGROUND — CLEAN, PROFESSIONAL, HIGHEST PRIORITY
   - Completely clean, smooth, uniform solid-color studio background (white, light gray, or neutral).
   - ZERO lines of any kind in the background: no grid lines, outline lines, border lines, separation lines,
     segmentation marks, cutout seams, matte lines, halos, glows, fringes, edge auras, or visible boundaries.
   - No patterns, textures, gradients, or artifacts in the background area.
   - Subject must blend seamlessly with background — no visible line or edge between outfit/model and background.
   - Preserve foreground subject with sharp accurate colors; background must remain perfectly plain and line-free.

2. MODEL FACE VISIBILITY — COMPLETE AND UNOBSTRUCTED
   - Full face visible: forehead/hairline, eyes, nose, mouth, chin, and neck.
   - Never crop, cut off, hide, or obstruct any part of the face.
   - No partial face; natural framing with complete head and face in frame.

3. FULL OUTFIT VISIBILITY — TOP TO BOTTOM
   - Entire outfit visible from neckline/shoulders to hem/floor.
   - No cropping or hiding at top, middle, or bottom.
   - Show complete garment length and hemline; model positioned so full outfit fits in frame.

4. OUTFIT DETAILS — MAXIMUM CLARITY
   - All patterns, embroidery, decorative elements, thread work, sequins, beads, borders, and motifs must be sharp.
   - Details must remain clear when zoomed; enhance texture and craftsmanship fidelity.
""".strip()
