**POSITIVE**

photograph of a quiet empty suburban bus stop on a bright summer morning, bus shelter made of (transparent cobalt-blue acrylic:1.2) and tinted polycarbonate panels, translucent cyan vinyl bench, sunlight passing through the tinted material and casting blue caustics and color spill onto a white concrete sidewalk, thick panel edges deep cobalt, thin edges glowing electric cyan with sharp specular edge highlights, overlapping panels layering into deeper blue, subsurface glow, glossy clear-resin bus stop sign, rolling hyperreal electric green grass lawn, saturated cerulean sky with soft white cumulus clouds, overexposed blue-tinted whites, bloom, halation, soft highlight clipping, high-key lighting, cool color temperature, minimal composition, large uninterrupted fields of blue, white and green, negative space, frutiger aero, y2k translucency, windows xp bliss, nostalgic digital optimism, serene, dreamlike, wide shot, eye level, 35mm photo, sharp focus, highly detailed

**NEGATIVE**

(opaque plastic:1.2), painted blue surfaces, flat matte color, solid colored panels, metal shelter, rust, graffiti, litter, advertising posters, people, crowd, cars, vehicles, traffic, power lines, clutter, busy background, night, dusk, overcast, gray sky, desaturated, dull colors, brown dry grass, warm cast, orange tint, sepia, teal and orange grading, purple, magenta, neon tubes, harsh black shadows, grime, dirt, text, watermark, logo, signature, lowres, blurry, jpeg artifacts, noise, oversharpened, cartoon, anime, illustration, cheap 3d render, low poly, distorted perspective, deformed geometry

**Notes**

1. Settings: use a native SDXL landscape size (1344x768 or 1216x832), CFG 5-7, 30-40 steps, DPM++ 2M Karras. CFG above 8 tends to crush the soft bloom.
2. The "color inside the material" look comes from the transmission phrases (caustics and spill on the sidewalk, dark thick edges vs. glowing thin edges, overlapping panels). If the shelter comes out looking painted, raise those weights rather than adding more color words.
3. Don't put "bus" in the negative: it leaks into the bus stop concept. "cars, vehicles" keeps the street empty. The `(term:1.2)` weighting is A1111/ComfyUI syntax, so remove the parentheses on front-ends that don't support it.
