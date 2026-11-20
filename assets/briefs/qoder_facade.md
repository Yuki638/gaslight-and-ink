# Brief: Building facade kit (Qoder)

Read `briefs/_common.md` first and follow it exactly. Script: `blender/facade.py`.
Extra materials allowed for this kit: Brick, Clay. These pieces get placed over existing walls and
stretched to many sizes in-game, so keep them **non-uniform-scale friendly**: no round details that
would visibly squash, frame widths in proportion, back face flat at Y=0 (the wall plane), depth toward -Y.
Origin: bottom center of the back face.

1. **SashWindow** — Georgian sash window, overall 4.6 wide x 5.8 tall x 1.0 deep. Limestone surround
   with a keystone lintel (top) and projecting sill (bottom), recessed wooden frame, two sashes with
   6-over-6 glazing bars (meeting rail in the middle). Panes as ONE separate object (the game lights
   some windows up). Objects: SashWindow_Stone, SashWindow_Wood, SashWindow_Glass. Budget 1500 tris.
2. **Door** — Victorian four-panel front door, door leaf 4.0 x 7.0, limestone surround 5.2 x 7.8 with
   pilasters and a cornice hood, semicircular-looking fanlight above (keep it inside the 7.8 height),
   brass knob, letter plate and knocker, one stone step 5.6 wide x 0.5 tall x 1.2 deep.
   Objects: Door_Wood, Door_Stone, Door_Brass, Door_Glass. Budget 2000 tris.
3. **ChimneyStack** — brick chimney stack 3.0 x 2.6 footprint, 5.4 tall, with a corbelled stone/brick
   cap band and 3 clay chimney pots (0.8 diameter, 1.8 tall, slight flare at top) on top.
   Objects: ChimneyStack_Brick, ChimneyStack_Stone, ChimneyStack_Clay. Origin bottom center
   (this one sits on a roof, not a wall). Budget 1500 tris.
