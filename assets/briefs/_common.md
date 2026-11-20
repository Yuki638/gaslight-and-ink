# Asset rules (read first) — GASLIGHT & INK

Game: Roblox, Victorian London 1890s at night, gaslight, fog, anime action RPG. Look: grounded
Victorian ironwork and wood, dark palette, readable silhouettes, slightly stylized (clean bevels,
no noisy detail). Must read well from a third-person camera ~15 studs away.

## Tooling
- Blender 5.2 headless: `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup -P <script.py>`
- Write ONE Python script per batch in `blender/` that builds every asset from scratch with bpy
  (no external downloads, no add-ons), exports, and renders previews. Re-runnable: it clears the scene first.
- Work only inside `D:\claude\roblox1\assets`. Do not touch anything else.

## Units, axes, origin
- 1 Blender unit = 1 Roblox stud. Character is 5.5 studs tall for reference.
- Build Z-up. Props: origin at bottom center (sits on ground at Z=0).
  Weapons/handheld: origin at the grip center, long axis along +Z (tip/blade pointing +Z).
- Apply all transforms and modifiers before export.

## Materials (critical — Roblox import ignores Blender shaders)
- Split each asset into one mesh object PER material. Name objects `<Asset>_<Mat>`, Mat from:
  Iron, Brass, Glass, Wood, Leather, Steel, Silver, Liquid, Cork, Flame, Stone, Fabric, Paper, Brick, Clay.
  Example: `Gaslamp_Iron`, `Gaslamp_Glass`, `Gaslamp_Brass`, `Gaslamp_Flame`.
- Max 4 materials per asset. Still give each a Blender material with a sensible base color (used for previews).

## Geometry
- Triangle budget is per asset (see your brief). Stay under it.
- Clean silhouettes: bevel hard edges (2 segments), smooth shading with "Smooth by Angle" ~35°, no n-gons left
  on curved surfaces, no interior/hidden faces, no zero-area faces, normals facing out.
- No flipped normals.

## Export
- One FBX per asset: `export/<Asset>.fbx`, selected objects only, `apply_scale_options='FBX_SCALE_UNITS'`,
  `axis_forward='-Z'`, `axis_up='Y'`, mesh only, no cameras/lights.

## Preview (I review these before anything ships)
- `renders/<Asset>.png`, 768x768, EEVEE (or Workbench with material colors if EEVEE fails headless),
  3/4 view from slightly above, whole asset framed, dark blue-grey background, one warm key light + cool rim.
- Also write `renders/<Asset>.json`: {"tris": N, "objects": [names], "dims": [x,y,z]}.

## When done
Print a short report: each asset, triangle count, dims, any problem. Keep it under 20 lines.
