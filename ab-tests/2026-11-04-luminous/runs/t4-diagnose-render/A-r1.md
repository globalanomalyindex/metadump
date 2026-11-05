# Fixing the flat blue vase: prompt and lighting changes, in priority order

## What's going wrong

Two separate failures.

1. **The blue sits on the surface.** The vase is shaded like an opaque object with a blue base color. Light bounces off it, so it reads as paint. The aesthetic needs the opposite: light goes *into* the acrylic, gets tinted as it travels, and comes back out. Thick parts should be deep and saturated, thin parts pale and glowing, and the shadow should be blue *light*, not grey darkness.
2. **The whites are exposed as midtones.** A white table under neutral, average exposure with a filmic tone curve comes out light grey. The aesthetic wants whites that are overexposed and *blue-tinted*, close to clipping, with no neutral grey anywhere.

The fixes below are ordered by how much each one moves the image. Items 1 to 4 do roughly 80% of the work.

---

## Priority list

### 1. Put the color in the volume, not the surface (biggest single fix)
**Render/material:**
- Make the vase fully transmissive: transmission 1.0, roughness 0.0 to 0.05, IOR about **1.49** (acrylic/PMMA).
- Make the surface/base color white or almost white. Get the blue from **absorption over distance** (Beer-Lambert), not from albedo:
  - Blender Cycles: Principled BSDF with transmission 1, base color white, then a **Volume Absorption** node in the Volume output. Color is a saturated cobalt-cyan, around `#0A6CFF`. Adjust density until a 4 to 6 mm wall reads pale aqua and a 2 to 3 cm base reads deep electric blue.
  - Arnold/Standard Surface: transmission color blue, plus **transmission depth** set close to the object's thickness. Without depth the tint stays surface-only.
  - V-Ray: fog color plus fog multiplier. Redshift and Octane: an absorption medium on the refraction.
- Test: the color should change *across the object* with thickness. If the blue is the same everywhere, it's still paint.

**Prompt:** Replace "blue plastic vase" with "**transparent blue-tinted cast acrylic** vase, color suspended inside the material, deep cobalt in the thick base fading to pale aqua at the thin rim, light passing through it." The word "plastic" by itself pulls toward opaque injection-molded toys. Add "acrylic", "resin" or "translucent vinyl", and a reference such as "Bondi Blue translucent Y2K electronics."

### 2. Move the key light behind the vase
Translucency only shows when light passes through the object toward the camera. Front light turns any tinted transparent object into a flat colored shape.

**Lighting:**
- Put the main light **behind the vase, 130 to 160 degrees from the camera**, raised 20 to 35 degrees. Make it 2 to 4 times stronger than anything in front.
- Keep the front fill weak, and use a large white bounce card instead of a second key light.
- Add one or two rim or strip lights from the side to trace the silhouette.

**Prompt:** "**backlit**, light shining through the vase toward the camera, glowing from within, rim light." Remove "studio lighting" if it's there, because it defaults to a front key.

### 3. Turn on caustics so the shadow is blue light
For "color exists inside the material," the most convincing evidence is the tinted pool of light the vase throws onto the white table.

**Render:**
- Enable caustics: in Cycles, turn on shadow caustics on the light, the caster and the receiver. Or use a renderer that handles caustics well (Octane, LuxCore, Redshift with caustic photons).
- Caustics need a **small, hard source**, such as a sun lamp with an angle of about 0.5 to 2 degrees, coming from behind. Use it alongside the large soft light that blows out the background.
- The shadow core should come out light and tinted, around `#9FCBF7`, with a bright focused hotspot near `#D8F6FF`. A grey shadow (`#A0A0A0`) means transmission isn't working.
- Turn off ambient occlusion or reduce it a lot. AO adds the grey, dirty contact shadows you're seeing.

**Prompt:** "luminous electric-blue **caustics** projected across the white table, tinted translucent shadow, refracted light patterns."

### 4. Overexpose on purpose and fix the tone mapping (main fix for grey whites)
**Camera/color management:**
- Raise exposure by **+1 to +2 EV** compared with a "correct" exposure. Expose for the vase's blue and let the whites clip.
- Under Filmic or AgX, a white diffuse surface at scene value 1.0 displays as roughly 80% grey. That is exactly the dull-white symptom. You have two options:
  - switch to **Standard** and control clipping yourself, or
  - stay on AgX/Filmic, raise exposure, and use a lower-contrast look so the whites reach display white.
- Set the table albedo to 0.85 to 0.9, not 0.7 to 0.8. Make the background a white cyc or an emissive plane at **1.2 to 2.0** strength so it blows out to pure white.

**Prompt:** "**high-key, overexposed**, blown-out white background, bright airy daylight, bleached highlights."

### 5. Tint the whites blue and remove every neutral grey
"Overexposed blue-tinted whites" means the whites lean blue. Neutral is wrong.

**Lighting/grade:**
- Set the lights cool, around **7500 to 9000 K**, or warm the camera white balance about 1500 K below the lights' temperature so the scene shifts cool.
- Grade: in highlights, the blue channel should be the highest, so whites land around `#EEF6FF` to `#FFFFFF`. Push shadows toward cyan or blue, never toward neutral or warm.
- Target values: table in light RGB about 238/246/255. Table in shade about 200/222/245. No pixel in the frame should have R = G = B except clipped white.

**Prompt:** "cool blue-tinted white light, icy pale-blue highlights, airy cyan-white atmosphere."

### 6. Give the vase a bright, colorful world to refract
A transparent object is mostly made of what it refracts. A grey or empty environment produces a grey, dull vase.

**Scene:**
- Use an HDRI or environment with a **saturated blue sky and electric green grass**, the aesthetic's own palette. Its reflections and refractions then put cyan-green and sky-blue gradients *inside* the walls.
- Put something behind or inside the vase so the refraction is visible: the table edge or horizon line, or a few hyper-green grass blades or stems in water inside the vase. Seen through blue acrylic, the green turns teal, which shows directly that the color lives in the material.

**Prompt:** "saturated blue sky and vivid electric-green grass refracted and distorted through the vase walls, green stems visible through the blue acrylic."

### 7. Sharp white speculars and glowing edges
**Material/lighting:**
- Keep the outer surface very glossy. A clearcoat helps. The speculars must be **pure white, not blue**. White highlights on top of a tinted body are what separate tinted acrylic from painted plastic.
- Use long strip lights or a softbox with hard edges for crisp, curved, Frutiger-Aero-style glossy streaks.
- Let the edges glow brighter and more saturated, the "edge-lit acrylic" light-piping effect. This happens naturally once you have real thickness, absorption and enough bounce depth.
- Raise transmission and glossy bounces to **12 or more** so internal reflections don't go black.

**Prompt:** "glossy wet-look surface, crisp white specular highlights, brightly glowing light-piped edges, Frutiger Aero glossy sheen."

### 8. Give the geometry real thickness
**Model:**
- Single-sided or very thin shells can't show an absorption gradient. Use solid walls of 3 to 8 mm, a thick solid base of 2 to 4 cm, and beveled rims to catch light.
- Make sure the normals are correct and the mesh is closed. A broken mesh makes refraction look muddy or dark.

### 9. Finish with bloom and halation
**Post:**
- Add bloom or glare on values above 1.0 (Blender: Glare node set to Bloom or Fog Glow, threshold about 1.0, kept subtle), plus a faint blue halation around clipped highlights.
- Optionally add slight chromatic aberration on the brightest edges for the Y2K-render feel.
- Don't lift the blacks or add haze over the whole frame. That brings the grey back.

**Prompt:** "soft bloom, gentle halation glow around highlights, luminous."

### 10. Restructure the prompt
- **Order:** light and material first, object second. Image models give more weight to early tokens.
- **Describe evidence of transparency, not just the word "transparent":** caustics, refraction distortion, color that varies with thickness, things visible through the walls.
- **Add a negative prompt** to block the failure modes you're seeing.

---

## Rewritten prompt (drop-in)

> Backlit transparent blue-tinted cast acrylic vase on a glossy white table, light shining through the vase and throwing luminous electric-blue caustics across the overexposed white surface, color suspended inside the material: deep saturated cobalt in the thick solid base fading to pale glowing aqua at the thin rim, light-piped glowing edges, crisp pure-white specular streaks, saturated blue sky and hyperreal electric-green grass refracted through the walls, high-key overexposed blue-tinted whites, cool icy daylight, soft bloom and halation, Frutiger Aero, Y2K translucent tech aesthetic, Bondi Blue translucency, clean product photograph, 85mm

**Negative prompt:**

> opaque, painted, solid color, matte plastic, satin finish, toy plastic, uniform blue, grey whites, dull, muddy, underexposed, neutral grey shadows, black shadows, dark shadow, flat front lighting, ambient occlusion grime, desaturated, hazy low contrast, warm white balance

(Stable Diffusion-style tools: weight the core terms, e.g. `(transparent tinted acrylic:1.3)`, `(backlit:1.2)`, `(caustics:1.2)`, `(overexposed high-key:1.2)`.)

---

## Checks for the next render (sample these pixels)

| Region | Target | Failure means |
|---|---|---|
| Table / background whites | `#EEF6FF` to `#FFFFFF`, blue channel highest | Grey or neutral: raise exposure, cool the light (items 4, 5) |
| Shadow under vase | Light tinted blue, about `#9FCBF7`, with a brighter caustic hotspot | Grey: transmission/caustics off, key not behind (items 1 to 3) |
| Vase thin wall vs thick base | Pale aqua vs deep cobalt, clearly different | Same blue everywhere: surface tint, no volume absorption (item 1) |
| Darkest part of vase | Saturated blue, never navy or black | Bounce depth too low, or environment too dark (items 6, 7) |
| Specular highlights | Pure white, sharp | Blue or soft highlights: roughness too high, base color too saturated (item 7) |
