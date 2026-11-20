# Brief: Hero props + weapons (Codex)

Read `briefs/_common.md` first and follow it exactly. Script: `blender/hero.py`.

1. **Gaslamp** — Victorian cast-iron street lamp, 15 studs tall. Fluted shaft on a stepped octagonal
   plinth, decorative collar rings, crossbar ladder-rest arms under the lantern, square tapered
   4-pane lantern with brass frame, pyramid hood with small finial. Inner flame/mantle as a separate
   small object `Gaslamp_Flame` (centered in the lantern, ~0.9 x 1.2 studs) — the game puts a light on it.
   Objects: Gaslamp_Iron, Gaslamp_Brass, Gaslamp_Glass, Gaslamp_Flame. Budget 3500 tris.
2. **Cane** — gentleman's walking cane, 4.4 studs long, dark lacquered wood shaft tapering to a
   silver ferrule, silver knob handle (engraved band, slightly flattened sphere). Origin at grip
   (just below knob). Objects: Cane_Wood, Cane_Silver. Budget 900 tris.
3. **Sabre** — 19th-century cavalry sabre, 4.4 studs total, slightly curved single-edged blade
   (3.2 studs, fuller groove), brass stirrup guard (D-shaped knuckle bow), leather-wrapped grip
   with wire bands, brass pommel cap. Origin at grip center, blade toward +Z.
   Objects: Sabre_Steel, Sabre_Brass, Sabre_Leather. Budget 1500 tris.
4. **TonicVial** — thrown alchemical vial, 0.9 studs tall: round-bottom flask, long neck, cork,
   twine wrap around the neck, glowing liquid filling 2/3 (separate object).
   Objects: TonicVial_Glass, TonicVial_Liquid, TonicVial_Cork. Budget 800 tris.
