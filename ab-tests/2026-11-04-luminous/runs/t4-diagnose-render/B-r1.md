# Fixing the "flat painted plastic, grey whites" vase render

I haven't seen your render or your prompt, so this ranks the likeliest causes. In this aesthetic both symptoms usually trace back to the same two faults:

- light is bouncing off the vase instead of passing through it;
- the blue is set on the surface instead of building up inside the volume.

Items 1 to 4 fix most of it. Each item below gives the reason, the prompt change and the lighting or render change.

## Prioritized changes

### 1. Light passes through the vase, not onto it (fixes both symptoms)
**Why.** Front light, or big soft light, hides every cue that puts the color inside the material. Clear plastic lit from the front reads grey and flat, and soft sources smear the caustics and highlights into a dull haze.

**Lighting.**
- Use one small, hard source: direct sun, or one hard key in a studio.
- Place it high and behind the vase, or three-quarters behind it, so its light travels through the acrylic toward the camera.
- Remove the front key, any on-camera flash and large softboxes.
- Let the clear sky be the only fill. In a studio, use one large blue-tinted fill instead.

**Prompt.**
- Add: "a high, hard sun three-quarters behind the vase shines through it".
- Delete: "studio product shot", "softbox", "soft even lighting", "overcast".

### 2. The blue deepens with how far light travels through the acrylic
**Why.** This is the defining rule. A single even blue across the object reads as paint, whatever the prompt says. Real tinted acrylic gets its color from absorption along the light path, so the color depends on thickness.

A vase is a hollow vessel, so the depth map runs opposite to a solid block:

| Part of the vase | Target look | Target hex |
|---|---|---|
| Thin walls across the middle (you look through two thin walls) | Pale, clear blue | about #B9E0FF |
| Body | Mid blue | about #2E8BF0 |
| Both sides, where the wall is seen edge-on | Deep sapphire, the darkest part | about #0A43B0 |
| Thick solid base | Deep sapphire | about #0A43B0 |
| Flat, polished cut rim | Glows the most saturated blue in the object | about #1E6BFF |
| Rounded, tapered lip | Goes pale blue-white instead | none given |

**Prompt.** Write the depth ramp out in full: "the thin walls read pale clear blue across the middle, deepening to sapphire along both sides where the wall is seen edge-on and to deep cobalt in the thick solid base".

**Render.**
- Put the color in the volume, not in the base color:
  - base or diffuse color neutral;
  - transmission 1;
  - roughness near 0;
  - IOR about 1.49 (acrylic).
- Set the tint through volume absorption: transmission color plus transmission depth.
- Set transmission depth to about 0.5 to 1 times the thickest solid section (the base), not the vase's height.
- A transmission depth of 0 turns the tint into a constant surface tint. That is exactly the painted look.
- Model real wall thickness with a thicker base, for example with a solidify modifier. A single-sided shell has no path length, so it cannot show a depth gradient. (This last point is my addition, not from the dump.)

**Check.** The deepest part should be about 25 L* or more darker than the thinnest part, and more saturated.

### 3. The light lands on the white table
**Why.** A clear blue object with a grey shadow reads as painted. The blue transmitted shadow and its caustics are also what make the tabletop look luminous instead of grey.

**Lighting.**
- With the backlight from item 1, the shadow falls toward the camera, across the tabletop, where it can be seen.
- Keep the source hard so the caustic lines stay crisp.

**Prompt.** Add: "laying a luminous blue shadow with a bright caustic core and curved caustic lines across the white tabletop toward the camera".

**Render.**
- Path-trace with refractive caustics enabled, and don't clamp or filter them away.
- The caustic pool should land near #8FC8FF.
- Raise the transmission and glossy bounce limits. A vase has at least four surfaces along a line of sight, and low limits render the far wall and the shadow a dark grey. (My addition.)

### 4. Overexpose the whites on purpose, and give their blue a physical cause
**Why.** Grey, dull whites usually mean underexposed whites sitting next to neutral shadows. In this look the brightness goes into the whites and highlights only, and the blue, the grass and the sky stay saturated.

**Exposure.**
- Push it up until the sunlit tabletop sits just below clipping.
- The whites should roll off in a pale-blue gradient, not sit as a flat plateau.
- Pure white belongs only to the sun, the specular cores and small sunlit edges, about 1 to 10% of the frame (around 5%).

**Where the blue comes from.**
- Use three sources:
  - skylight filling the shadows (in a studio, the blue-tinted fill);
  - the vase's own blue spill;
  - bloom tinted pale blue.
- Do not use a global blue grade or an overall cool white balance: it would turn the grass teal.
- Keep the daylight white balance neutral, never warm.

**White targets.**

| Area | Hex |
|---|---|
| Near-clipped cores | #F6FAFF |
| Lit white surfaces and bloom | #DDEDFF |
| Shade on white | #B3CBEA |

In every white, the blue channel should be at or above red: about +8 to +40 levels (8-bit) in the blooms and near the vase.

**Tone mapping** (my addition, not from the dump). Filmic-style tone mappers (Filmic, AgX, ACES) compress diffuse white to light grey by design. Correct that with exposure, not with a global glow or lifted shadows.

**Prompt.**
- Add: "overexposed blue-tinted whites: the tabletop runs from pale blue-white in its shade to nearly white in the sun, blooming softly only around highlights, while the sky, grass and deep blue stay fully saturated".
- Avoid: "washed out", "blown out", "bright and airy", "faded".

### 5. Give the vase a bright, saturated world to reflect and to see through
**Why.** Clear acrylic shows whatever surrounds it. A grey room gives grey reflections and nothing to look through. The aesthetic also requires electric-green grass under a saturated blue sky.

**Options.**
- **Best.** Put the white table outdoors in sunlit grass under a deep blue sky, and keep the camera low so the vase is framed against the sky.
- **Studio fallback** (the dump's default for studio shots):
  - use a pale blue-white backdrop (#DDEDFF), not grey;
  - keep the bloom blue-tinted;
  - include at least one green accent.
- **Easy win** (my suggestion): stand a few blades of electric-green grass in clear water inside the vase. They provide the green accent and visibly bend through the walls, which proves the viewer can see into the vase.

**Render.** Use a clear-sky HDRI rather than a grey studio HDRI.

### 6. Highlights are white and sit on the surface
**Why.** A white highlight over a blue body is the fastest visible proof that the color is inside. Blue-tinted or metallic highlights, or no highlights at all, read as coated plastic.

**Prompt.** Add: "crisp white highlights following the curve of the body, a bright reflective rim around a see-through center".

**Render.**
- Keep specular color white and untinted.
- A correct IOR produces the Fresnel rim on its own.
- Angle broad flat faces away from the sky so large reflection sheets don't veil the tint.

**Avoid:** "blue sheen", "metallic", "chrome", "anodized", "pearlescent".

### 7. Remove the haze
**Why.** Strong diffusion, soft glow, an Orton effect or soft focus lifts the shadows and greys every color. This is often what "dull" actually is.

**Fixes.**
- Apply bloom only to near-clipped highlights: radius about 0.5 to 2% of the image width, pale-blue tint.
- If you use a mist filter, keep it at 1/8 to 1/4 strength at most.
- Keep the whole vase sharp at f/5.6 to f/11. Bokeh belongs only to the background.

**Prompt.** Delete "dreamy", "soft glow", "hazy", "soft focus", "light leaks".

### 8. Swap out the words that ask for paint

| If your prompt says | Write instead |
|---|---|
| "blue plastic vase", "glossy blue vase" | "a vase cast in transparent blue acrylic, water-clear" |
| "translucent" on its own | "transparent, water-clear". "Translucent" asks for a diffusing body, and pushed far it becomes milky and opaque. In 3D, use little or no subsurface scattering. |
| "acrylic" on its own | "cast acrylic" or "clear acrylic plastic". Bare "acrylic" drifts toward acrylic paint. |
| "blue colored", "tinted", "blue coating", "candy blue", "lacquered" | the thickness ramp from item 2 |
| "frosted", "glassmorphism" | "polished, clear" |
| "blue light", "blue gel", "blue rim light" on a clear vase | make the material itself blue and keep the light neutral daylight |
| "glowing" or "luminous" with no cause | "backlit by the sun". Otherwise the model adds a lamp inside the vase. |
| "toy", "clay render", "3D icon" | the acrylic wording above |
| "vibes", "8k", "masterpiece", "stunning" | cut them and spend the words on light and optics. Write "Frutiger Aero and Y2K translucency" without "vibes". |

### 9. Camera and framing (smaller gains)
- Shoot from a low angle with an 85 to 100mm lens at f/5.6 to f/11.
- Use 4:5 or 1:1 for a single-object study, or 3:2 if the shot includes grass and sky.

## Revised prompt (drop-in)

**Positive.**
> A tall rounded vase cast in transparent blue acrylic, water-clear, standing on a white tabletop in hyperreal electric-green grass under a deep, saturated blue sky. The color lives inside the material: the thin walls read pale clear blue across the middle, deepening to sapphire along both sides where the wall is seen edge-on and to deep cobalt in the thick solid base. A few blades of grass stand in clear water inside it, bent by refraction. A high, hard sun three-quarters behind the vase shines through it, laying a luminous blue shadow with a bright caustic core and curved caustic lines across the white tabletop toward the camera. Crisp white highlights follow the curve of the body, with a bright reflective rim around a see-through center. Overexposed blue-tinted whites: the tabletop runs from pale blue-white in its shade to nearly white in the sun, blooming softly only around highlights, while the sky, grass and deep blue stay fully saturated. Low camera, 100mm, f/8, Frutiger Aero and Y2K translucency.

Optional, to bring in the vinyl half of the material brief and an overlap cue:
> A thin sheet of translucent blue vinyl lies on the table beside it, darker where the vase's blue shadow crosses it.

**Studio swap.** Replace the setting sentence with:
> standing on a white tabletop against a pale blue-white paper sweep, one hard light behind and to one side, a soft sky-blue fill

Keep the grass in the water as the green accent.

**Constraints line.** Append this for gpt-image and Gemini:
> (1) the blue deepens with path length, pale through the thin walls and deep at the edge-on sides and base, never one flat blue; (2) highlights are white over the blue body, and the shadow on the table is blue light with caustics, never grey; (3) only whites and highlight cores bloom or clip, the sky, grass and deep blue stay saturated, no haze; (4) neutral-white daylight, azure-to-cobalt blue (never aqua), real vivid grass; (5) no logos, lettering or people.

**Negative.** Use this as written for SD. For Midjourney, pass single words with `--no`. For FLUX, drop it.
> painted surface, flat color fill, opaque glossy plastic, chrome trim, frosted glass, grey shadow, haze, golden hour, washed-out sky, neon, holographic, artificial turf, text

## Check the next render
These are the meta dump's image checks, most diagnostic first. All are "must" checks.

- **k-img-depth-tint.** Sample the thinnest wall and the edge-on side or base. They should differ by about 25 L* or more. A uniform blue fails.
- **k-img-light-lands.** The shadow on the table contains blue light and caustics. A neutral grey shadow fails.
- **k-img-white-speculars.** Highlight cores are near-neutral and brighter than any blue in the body.
- **k-img-luminous-whites.** Clipping covers about 1 to 10% of the frame and sits only at light sources and highlight cores. Deep blue keeps HSV saturation of 60% or more. The whites show a pale-blue gradient.
- **k-img-whites-blue.** In regions above 85% lightness, blue is at or above red. No warm whites or shadows.
- **k-img-material.** You can see into the vase (here, the grass stems bent through the walls), and it stays blue where it crosses white.
- **k-img-sky and k-img-grass.** Apply these if the shot is outdoors.

## How grounded this is
- **Stated by the client.** The defining rules come from the brief itself: color inside the material, overexposed blue-tinted whites, grass under a saturated sky, transparent blue acrylic and vinyl, not painted on.
- **Researched.** The optics are sourced: absorption with depth, transmission, subsurface scattering, caustics, and the fact that zero transmission depth gives a surface tint.
- **Inferred.** Most of the recipes are inferred in the dump: the backlight, the hard sun, the white highlights, the blue shadow, and how the whites get their blue.
- **Proposed, not measured.** Treat every number as a starting point: the 25 L* gap, the 1 to 10% clipping budget, the transmission depth range, the bloom radius, the hex ramps and the lens settings.
- **Vase-specific.** "Vase" isn't in the dump. Item 2 applies its default for hollow shells.
- **My own additions, not in the dump.** Modeled wall thickness, bounce limits, tone-mapper grey, and grass in water inside the vase.

Dump entries relied on: us-aesthetic, us-inside-material, us-blue-acrylic-vinyl, us-blue-tinted-whites, us-grass-sky, inv-ml-depth-tint, inv-ml-luminous-whites, inv-ml-white-speculars, inv-ml-light-lands, inv-ml-see-into, opt-thickness-absorption, opt-transmission, opt-subsurface, opt-caustics, opt-edge-glow, opt-overlap-deepening, opt-specular-highlights, opt-fresnel-rim, opt-tinted-shadow, lt-ml-backlight, lt-ml-hard-sun, lt-ml-white-receiver, cam-ml-lens-angle, cam-ml-diffusion, wh-bloom, wh-rolloff, wh-blue-source, wh-luminous-vs-blown, p-ml-ior, p-ml-transmission-depth, p-ml-depth-contrast, p-ml-clip, p-ml-bloom, pal-material-blue, pal-white-ramp, b-ml-transparent, b-ml-luminous, b-ml-overexposed, b-ml-blue-tinted, mat-cast-acrylic, mat-vinyl, ak-painted-on, ak-ml-grey-shadows, ak-ml-tinted-highlights, ak-global-haze, ak-overexposed-ruined, ak-translucency-opacity, ak-acrylic-paint, ak-clear-glass-blue-backdrop, ak-plastic-toy, ak-luminous-emissive, ak-noise-vibes, ak-pe-warm-light, ak-pe-aqua-drift, q-hollow-shells, q-pe-environment-required, q-product-negatives, q-default-clarity, q-ml-aspect, exports.image.generic (v1, current), checks k-img-*.

Suggested write-back for the main loop. I'm a subagent, so I have not edited the dump. Add an `inferred` tier-2 entry, "vessel / vase", covering:
- the hollow-vessel depth ramp;
- the need for real wall and base thickness in 3D;
- the rim choice (polished cut rim glows saturated, tapered lip goes pale);
- a note that a studio tabletop is a valid receiving surface under q-pe-environment-required.
