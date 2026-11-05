**POSITIVE**

A quiet suburban bus stop: a rounded shelter of thick transparent blue acrylic panels with a taut translucent blue vinyl canopy and a blue acrylic bench, on a pale concrete sidewalk beside hyperreal electric-green grass with sunlit yellow-green tips, under a deep, saturated blue sky. The color lives inside the material: pale clear blue where panels are thin, deep sapphire where they thicken and overlap, polished edges glowing saturated blue, crisp white highlights. A high sun behind the shelter shines through it, casting blue-tinted shadows and bright caustic light across the sidewalk toward the camera. Overexposed blue-tinted whites bloom around highlights and clouds while sky and grass stay saturated. Empty street, distant white houses, low camera, Frutiger Aero and Y2K translucency.

**NEGATIVE**

painted surface, flat color fill, colorless glass, frosted glass, chrome trim, grey shadow, golden hour, washed-out sky, haze, artificial turf, text, people

**Notes**

1. Run at 1216×832, the SDXL bucket closest to the 3:2 scene default, with CFG around 5–7. Let the words carry the saturation: a high CFG burns the whites and pushes the blue toward cyan.
2. Past 75 tokens, A1111 and ComfyUI split the prompt into chunks. The subject, both materials, the grass and the sky all sit in the first chunk. If the shelter still comes out as ordinary clear glass on a metal frame, weight `(transparent blue acrylic:1.2)` rather than adding more negatives, which can backfire in SDXL.
3. Assumed defaults: no people, no named reference works, and any sign left plain with no lettering. The vinyl canopy is there to carry the "vinyl" half of the brief; a curved acrylic roof works too.
