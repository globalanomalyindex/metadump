# Fixing the translucent blue vase render: prompt and lighting changes

Source: `luminous-translucency.metadump.json` (v1), used in use mode. I pulled the tier-1 route, the "diagnose or fix the optics" route, the whites, lighting/camera and materials sections, the generic image export, and the image-scoped anti-keywords and checks. Entry ids are in brackets so you can look any of them up with `jq '.index["<term>"]'`.

## Why it looks this way (short version)

- **"Flat painted blue plastic"** means the vase is one even blue all over. The dump's central rule, tier 1 [inv-ml-depth-tint], is that the blue has to change with how far light travels through the material: pale where it's thin, deep where it's thick, edge-on or overlapped. It puts it bluntly: "A uniform blue across an object is the painted-on look, whatever the prompt says." Two things almost always cause this. Either the light is in front of the object, or (in a 3D renderer) the blue sits in the surface or base color instead of in absorption along the light's path [opt-thickness-absorption].
- **"Grey, dull whites"** come from the same lighting problem plus three more: (a) the whites have no physical reason to be blue, so they come out neutral grey [wh-blue-source]; (b) the vase casts a neutral grey contact shadow onto the white table [ak-ml-grey-shadows]; (c) the whites sit at mid-grey with no high-key gradient, or a soft diffusion or haze lifts them [wh-luminous-vs-blown, cam-ml-diffusion].

The single biggest lever is the light, so it comes first.

---

## Prioritized changes

### 1. Light it from behind with one hard source (fixes both symptoms)
**Lighting:** Move the key, ideally a high direct sun, *behind or three-quarters behind* the vase so its light passes through the material toward the camera. Use a **small, hard** source: clear-sky sun outdoors, or one hard key in a studio. No big softboxes, no overcast light, no on-camera or front fill as the key.
**Why:** The dump says front light "hides all of this and makes clear plastic look grey and flat" [lt-ml-backlight]. Only a hard source draws crisp caustics, sharp blue shadows and tight white highlights; soft light "smear[s] them into a faint haze and make[s] clear plastic dull" [lt-ml-hard-sun]. This is likely why you're getting the painted look and the dull look at the same time.
**Prompt:** add "a high sun three-quarters behind the vase shines through it toward the camera". Cut any "studio product shot", "softbox" or "front-lit" wording (the dump lists "front-lit studio product shot" and "on-camera flash" as its bad examples).

### 2. Put the blue in the light path, not on the surface
**Prompt:** don't write "a blue acrylic vase" or "blue plastic vase". The dump lists those as bad wording [mat-cast-acrylic ex.bad]. "Acrylic" on its own can also be read as *acrylic paint* [ak-acrylic-paint], and for a vase that pushes toward a painted ceramic pot. Describe the thickness gradient for a vase's actual form instead. A vase is a hybrid: its walls behave like a hollow shell (deepest along the silhouette), and its base behaves like a solid (deepest through the thickest part) [inv-ml-depth-tint]:
> "made of transparent blue cast acrylic: pale clear blue where you look straight through the thin walls, deepening to sapphire along both sides of the silhouette where the wall is seen edge-on, deepest in the thick solid base; where the near and far walls overlap the blue is darker than either alone; the polished flat rim glows bright saturated blue."

If the lip is thin and tapered rather than a flat cut edge, ask for it to glow *pale white-blue* instead. Thin tapered rims glow pale; polished cut edges glow deep [opt-edge-glow: "say which one"].
**3D renderer:** put the blue in **transmission color with a transmission depth**, not in base or diffuse color. With zero depth the tint "becomes a constant surface tint, which is the painted-on look" (researched, Autodesk Standard Surface) [opt-thickness-absorption]. Starting values:
- transmission depth about **0.5–1×** the object's thickest dimension. For a hollow vase I'd measure that against the solid base, which is my reading of the rule. Much larger flattens everything to pale; much smaller makes it dark and near-opaque [p-ml-transmission-depth, proposed].
- **IOR 1.49** for acrylic [p-ml-ior]; **thin-walled off**, since thin-walled is for vinyl film [opt-transmission].
- **Little or no subsurface scattering.** A little makes it glow from inside; too much turns it opaque [opt-subsurface].
**Target:** the thickest or overlapped areas should be about **25 L\* or more darker** and more saturated than the thinnest areas [p-ml-depth-contrast, proposed]. Proposed ramp: thin #B9E0FF, body #2E8BF0, thick core #0A43B0, cut-edge glow #1E6BFF [pal-material-blue, proposed].

### 3. Make the vase's light land on the white table (this replaces the grey shadow)
**Prompt:** "laying a luminous blue transmitted shadow across the white tabletop, deepest under the thick base, with a bright caustic core and caustic lines where the curved body focuses the sun."
**Lighting and composition:** with the sun behind, the shadow falls *toward the camera*, so leave enough tabletop in front of the vase to hold it [lt-ml-backlight]. The white table works well here as the "receiving surface" [lt-ml-white-receiver]: it's where the color inside the material visibly ends up.
**Why:** "A clear blue object with a grey shadow reads as painted" [inv-ml-light-lands]. Product-shot defaults add a neutral contact shadow as if the object were opaque [ak-ml-grey-shadows]. **3D:** turn on path-traced caustics so the transmitted blue actually reaches the table [rv-ml-render-vocab]. Caustic pool color is about #8FC8FF [pal-material-blue].

### 4. Give the whites a blue source, then push them high-key with a gradient
**Lighting:** whites read blue only when something physically makes them blue [wh-blue-source]:
1. open skylight. Outdoors, the saturated blue sky is a huge soft blue fill. In a studio, add a **blue-tinted fill** alongside the hard back key [lt-ml-hard-sun];
2. blue light transmitted through the vase onto the table (item 3);
3. bloom carrying the tint into highlight halos.
With none of these, you get the neutral grey table you have now.
**Exposure:** raise it until the lit tabletop reads near-white with a **pale-blue gradient**, not a flat plateau. The proposed ramp is #F6FAFF near the highlight cores, #DDEDFF for lit white and bloom, and #B3CBEA for white in shade or under the vase [pal-white-ramp, proposed]. Keep pure clipping to about **1–10% of the frame, around 5%**, at the sun and specular cores only [p-ml-clip, proposed]. The blue in the vase must stay saturated while you do this [inv-ml-luminous-whites, tier 1].
**Bloom and diffusion:** a light touch only. Bloom radius about 0.5–2% of image width, triggered only by highlights already near clipping, tinted pale blue [p-ml-bloom]. If you use a mist filter or post glow, keep it to about 1/8–1/4 strength: "strong diffusion lifts the shadows, greys the colors" [cam-ml-diffusion]. No global soft glow, Orton effect or soft focus [ak-global-haze].
**Prompt:** attach "overexposed" to the whites only. A bare "overexposed" makes models raise the whole exposure, which washes out the sky and the material color [b-ml-overexposed, ak-pe-washed-sky]. Write: "the tabletop whites are overexposed and faintly blue, running from near-white where the sun hits to pale sky-blue in shade, blooming softly only around the highlights, while the vase's deep blue stays fully saturated." Keep whites cool: no golden hour, warm white balance, cream whites or film halation [ak-pe-warm-light, ak-ml-warm-halation].

### 5. Give the viewer something to look *into*
**Setting:** the aesthetic is tier-1 bound to "hyperreal electric green grass under a saturated blue sky" [us-grass-sky]. Put the white table *in* that scene: on grass, under a deep sky. That also gives you the skylight fill from item 4 for free. A seamless studio void has nothing behind the vase to refract, so it reads as a solid object.
**Camera:** short telephoto or macro, about 85–100mm, at a low angle so the vase is framed against the sky. Use about f/5.6–f/11 so the whole vase stays sharp, with bokeh only in the far background [cam-ml-lens-angle, proposed]. Trade-off: if the camera is right at table height, the shadow on the table foreshortens to nothing. Sit just high enough to see the blue shadow pool (my inference, not in the dump).
**Prompt:** "the sky and grass behind are visible through the vase, bent and magnified by the thick base." The material must read as "a volume you can see into", with transparency shown as depth, not faintness [inv-ml-see-into].
**Studio fallback:** if you have to stay indoors, use a hard back key, a blue-tinted fill and a pale backdrop with some tonal gradient to refract. This drops the tier-1 grass and sky, so treat it as a deliberate deviation.

### 6. Keep the highlights white and on top of the blue
**Prompt:** "crisp white highlights streak down the curved body following its form, with the blue visible beneath them; a bright reflective rim along both sides, clear center."
**Why:** a white highlight over a blue body is "the fastest visual test for color inside versus color on top" [inv-ml-white-speculars]. Highlights reflect the light and sky, not the tint [opt-specular-highlights]. The Fresnel rim gives a bright silhouette around a see-through center [opt-fresnel-rim]. Avoid "glossy blue" and "shiny blue": they pull toward metallic or anodized finishes where the highlight itself turns blue [ak-ml-tinted-highlights, ak-chromecore]. **3D:** low specular roughness, untinted (white) specular, correct IOR. Give broad flat faces an angle away from the sky so large reflection sheets don't veil the tint [opt-specular-highlights].

### 7. Clean the wording
Remove words that bring back paint, opaque plastic or haze, and swap in the dump's rewrites:
| Remove | Use instead |
|---|---|
| painted, coated, glossy blue finish, candy, lacquered [ak-painted-on] | "color carried inside the material: tint that deepens with thickness and glows at thin edges as light passes through" |
| blue plastic, toy plastic, 3D render look [ak-plastic-toy] | "optically clear blue acrylic: refraction, tint deepening with thickness, bright edges, faint structure visible through the body" |
| clear glass vase with blue lighting / blue gel [ak-clear-glass-blue-backdrop] | the material itself is blue and stays blue against the white table |
| luminous, glowing, dreamy, ethereal on their own [d-ml-luminous, d-ml-ethereal] | write the cues: backlit, edge glow, blue spill on white, cool bloom at the brightest points |
| 8k, masterpiece, stunning, vibrant colors [k-noise-words] | spend the words on material, optics and light |

### 8. Hold the hue (lower priority, but a common drift)
Keep the material **azure to cobalt (hue about 205–228°)**, never aqua or turquoise. Glass and "transparent" defaults pull toward greenish edges, which merge the blue into the grass [ak-pe-aqua-drift, k-img-blue-not-aqua]. If you want a glass vase instead, say "blue-tinted low-iron glass", because ordinary glass edges go green [mat-blue-glass].

---

## Revised prompt (assembled from the dump's generic image export with your subject swapped in)

**Positive:**
> A hollow vase of transparent blue cast acrylic with a thick solid base, standing on a white table set in hyperreal electric-green grass under a deep, saturated blue sky. The color lives inside the material: pale clear blue where you look straight through the thin walls, deepening to sapphire along both sides of the silhouette where the wall is seen edge-on, deepest in the thick base; where the near and far walls overlap the blue is darker than either alone. The polished flat rim glows bright saturated blue. Crisp white highlights streak down the curved body following its form, a bright reflective rim along both sides, clear center; the sky and grass behind are visible through the vase, bent and magnified by the base. A high sun three-quarters behind the vase shines through it toward the camera, laying a luminous blue transmitted shadow with a bright caustic core across the white tabletop. The tabletop whites are overexposed and faintly blue, from near-white in direct sun to pale sky-blue in shade, blooming softly only around the highlights, while the sky, grass and deep blue stay fully saturated. Low camera, 90mm, f/8. Frutiger Aero and Y2K translucency.

**Constraints line** (append for gpt-image and Gemini, which have no negative field):
> Constraints: (1) the blue deepens with thickness and overlap, never one flat blue on the vase; (2) highlights are white over the blue body, and the shadow on the table is blue light with caustics, never grey; (3) only whites and highlight cores bloom or clip, sky, grass and deep blue stay saturated, no haze over the frame; (4) neutral-white daylight, azure-to-cobalt blue (never aqua), real vivid grass; (5) no logos, lettering or people.

**Negative** (Stable Diffusion; drop entirely for FLUX; for Midjourney use `--no` with single words such as `--no paint, ceramic, frosted, chrome, haze, turquoise, text`):
> painted surface, flat color fill, opaque plastic, ceramic, acrylic paint, frosted glass, blue chrome, grey shadow, black contact shadow, golden hour, washed-out sky, haze, soft focus, turquoise, text

(The base negative comes from the dump's export. I added "opaque plastic", "ceramic", "acrylic paint", "blue chrome", "black contact shadow" and "soft focus" from the scoped anti-keywords to cover the vase case.)

---

## Check the next render against these (the dump's image checks)
- **k-img-depth-tint (must):** sample the thinnest wall and the thick base. The base should be about 25 L\* or more darker and more saturated, and every wall overlap darker than one wall alone. A uniform blue fails.
- **k-img-white-speculars (must):** highlight cores near-neutral and brighter than any blue in the body. No blue or metallic highlights.
- **k-img-light-lands (must):** the shadow on the table contains blue light. A neutral grey shadow fails.
- **k-img-luminous-whites (must):** clipped pixels about 1–10% of the frame, only at light sources and highlight cores. Deep-blue and grass areas keep HSV S of 60% or more. The table shows a pale-blue gradient, not a flat plateau.
- **k-img-whites-blue (must):** in regions above 85% lightness, the blue channel is at or above red, typically +8 to +40 (8-bit) near the vase. Any red-over-blue white fails.
- **k-img-material (must):** you can see into or through the vase, and it stays blue where it crosses the white table.
- With grass and sky in frame, also **k-img-sky** (top-third hue about 205–220, S 55% or more, no haze) and **k-img-grass** (hue 80–140, S 60% or more, real varied blades).

## How solid this advice is
- **Researched (cited in the dump):** thickness-dependent absorption and transmission depth, specular transmission, subsurface scattering, caustics.
- **Inferred:** the lighting, white-source, highlight and wording rules, including backlight, hard sun, Fresnel rim and grey-shadow avoidance.
- **Proposed starting points, not measured:** all hex ramps, the 25 L\* contrast, the 1–10% clip budget, the bloom radius, the transmission-depth multiplier and the lens choice. Tune these by eye.
- **My own additions, not in the dump:** how the hollow-vessel thickness rule applies to a vase with a solid base; the camera-height trade-off for seeing the table shadow; the extra negatives listed above.
- Your subject (a vase on a white table) is one of the dump's open choices [q-ml-subject]. Its default subjects are simple slabs, spheres and rings in the grass-and-sky scene, so I applied the rules to the vase form rather than finding vase-specific entries.

## Write-back candidates (for the main loop, not written by this run)
- An `inferred`, tier-3 entry for hollow vessels with solid bases (vase, bottle, cup): walls deepest at the silhouette, base deepest overall, flat versus tapered rim behavior.
- A route or entry for studio or indoor setups beyond the one line in [lt-ml-hard-sun], since a studio is where the grey-white failure is most likely.

cites: inv-ml-depth-tint, us-inside-material, us-blue-acrylic-vinyl, us-blue-tinted-whites, us-grass-sky, inv-ml-luminous-whites, ak-painted-on, opt-thickness-absorption, opt-transmission, opt-subsurface, opt-caustics, opt-edge-glow, opt-overlap-deepening, opt-specular-highlights, opt-fresnel-rim, opt-tinted-shadow, p-ml-ior, p-ml-transmission-depth, p-ml-depth-contrast, p-ml-clip, p-ml-bloom, b-ml-overexposed, wh-bloom, wh-rolloff, wh-blue-source, wh-luminous-vs-blown, lt-ml-backlight, lt-ml-hard-sun, lt-ml-white-receiver, cam-ml-lens-angle, cam-ml-diffusion, rv-ml-render-vocab, mat-cast-acrylic, mat-blue-glass, inv-ml-light-lands, inv-ml-white-speculars, inv-ml-see-into, pal-material-blue, pal-white-ramp, ak-acrylic-paint, ak-plastic-toy, ak-clear-glass-blue-backdrop, ak-ml-grey-shadows, ak-ml-tinted-highlights, ak-ml-warm-halation, ak-pe-warm-light, ak-pe-washed-sky, ak-pe-aqua-drift, ak-global-haze, ak-chromecore, d-ml-luminous, d-ml-ethereal, q-ml-subject, exports.image.generic, k-img-*.
