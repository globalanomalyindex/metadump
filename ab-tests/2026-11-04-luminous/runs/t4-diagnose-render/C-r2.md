# Fixing the "painted plastic" vase: prioritized changes

## Diagnosis

You have two separate problems, and they have separate causes.

1. **The blue sits on the surface instead of inside the material.** The metadata states the principle directly: the "difference between an object being colored blue and being made of blue." You get a painted look when the blue is stored as surface or diffuse color. That makes the hue the same everywhere, lets no light through, and puts no blue on the table. In this aesthetic, blue is supposed to change with "illumination, backdrop, thickness, curvature and layering."
2. **The whites are grey because they are underexposed, neutral in color and lit without bloom.** The metadata describes white as "blue-tinted, luminous, diffused and often near overexposure." If you expose for the midtones under neutral light, a white table comes out a flat light grey.

Notes on sources: text in quotation marks comes from the metadata file. Numeric values are my suggested starting points, not values taken from the metadata.

---

## Priority 1: Put the blue in the volume, not on the surface (biggest single fix)

**In the prompt**
- Describe the material, not the color. Replace phrases like "blue plastic vase", "glossy blue vase" or "blue-colored vase" with **"a vase made of transparent blue acrylic"** or **"a vase cast from water-clear blue-tinted resin."**
- Drop the word "plastic" on its own, and drop "painted", "colored" and "glossy blue" when nothing in the prompt says it is transparent. Image models read those words as opaque toy plastic.
- Describe how the color behaves, not only what hue it is: **"thick base is deep translucent cobalt, thin rim glows electric cyan."** This comes from the metadata's "Thicker transparent material looks darker / Thin edges catch and transmit more light."

**In a 3D render (Blender/Cycles terms; other engines have equivalents)**
- Principled BSDF settings: Base Color white or nearly white, Transmission 1.0, Roughness 0.0 to 0.05, IOR about 1.49 (acrylic).
- Put the saturated blue in a **Volume Absorption** node plugged into Material Output > Volume. Absorption makes the color depend on how much material the light passes through. Raise the density until the base reads deep cobalt while the rim stays pale cyan.
- Do **not** put saturated blue in Base Color or Transmission Color. That tints every surface crossing by the same amount, and that is exactly what produces the flat painted look.
- Geometry: the vase needs real wall thickness (model it or use a Solidify modifier), ideally a thick solid base and a thin lip, with smooth shading. A single-sided shell cannot show a thickness gradient.

## Priority 2: Backlight it so the light travels through the material

The metadata's lighting language is "backlighting", "backlit blue acrylic", "sunlight through colored plastic" and "edge illumination." A transparent object lit from the front looks opaque.

**Lighting setup**
- **Key light:** a strong, hard sun placed *behind* the vase, 20 to 40 degrees above the table and a little off the camera axis, so the light comes through the vase toward the lens.
- **Fill:** a large, soft white area light or bounce card on the camera side at low intensity. Its only job is to keep the front face from going dark.
- **Remove any frontal key light.** It makes the surface reflection dominate and hides the transmission.

**Prompt language:** "backlit by strong sunlight, light shining through the vase, glowing edges, rim light."

## Priority 3: Make blue light land on the white table (caustics and color spill)

Blue on the table proves that the color lives inside the material. The metadata says "Blue illumination spills onto adjacent whites" and lists "caustics" and "color bleeding."

**Prompt language:** "blue caustics pooling on the white table, cyan light patterns cast through the vase, translucent blue shadow."

**3D**
- In Cycles, turn on Refractive (and Reflective) caustics, set Filter Glossy between 0 and 0.3, raise Transmission bounces to 12 or more, and raise Total bounces to 16 or more.
- Or use MNEE shadow caustics (Blender 3.2+): enable Shadow Caustics on the light, Cast Shadow Caustics on the vase, and Receive Shadow Caustics on the table.
- In other engines, enable caustics or photon mapping.
- A sun with a small angular size gives sharper caustics.
- The vase's shadow should be a **translucent blue pool, not a grey patch.** A grey shadow alone tells the viewer the object is opaque.

## Priority 4: Expose for the whites and push them to the edge of clipping

Most of your grey-white problem comes from here.

- Raise exposure by about +0.5 to +1.5 stops, until the brightest parts of the table sit at roughly 95 to 100% luminance. Allow "soft clipping": the metadata says whites "approach pure white with diminished detail."
- **Table material:** set the albedo to about 0.9 to 0.95. Blender's default base color of 0.8 looks grey under neutral light. Give the surface a slight gloss, like white lacquer or white acrylic, so it picks up highlights and the blue caustics.
- **View transform:** AgX and Filmic compress highlights and lower their saturation, which pushes whites toward grey. Either raise exposure under AgX and use a higher-contrast look (Punchy or High Contrast), or use Standard carefully. Standard clips harder and can oversaturate the blue, so check the vase after switching.
- **Prompt language:** "high-key lighting, overexposed bright airy daylight, luminous optical white."

## Priority 5: Tint the whites blue (cool balance and a blue environment)

Neutral white reads as dull in this aesthetic, because its whites lean blue.

- **Environment:** swap any grey studio HDRI for a **bright, clear blue-sky HDRI.** Its blue then reaches the fill light and the vase's reflections, and the table turns blue-white. Reflections of a grey studio are a large part of why the vase looks like ordinary plastic.
- **Color balance:** cool it slightly with a compositor Color Balance node or a cooler white-balance setting, so the blue channel leads in the whites. Keep the sun near neutral or slightly warm so the blue doesn't turn muddy.
- **Target values (my suggestion):** lit whites around #F4FAFF to #FFFFFF. Shadows on the white table should be pale cyan (about #CFE6FF), not grey (#B0B0B0).
- **Prompt language:** "blue-tinted whites, cool color temperature, milky optical white."

## Priority 6: Add bloom and halation to the highlights only

The metadata says "Highlights bleed into neighboring pixels" and "Highlights merge visually with cyan material," and lists bloom, halation and "specular bloom."

- **3D/post:** use a compositor Glare node (Fog Glow, or Bloom in newer Blender) with the threshold around 0.9 to 1.0 and a low mix. Only the clipped speculars, the rim glow and the brightest parts of the table should bleed. Add a faint cyan halation around the rim highlights.
- **Prompt language:** "soft bloom, halation, glowing specular highlights."
- Don't haze the whole frame. A global glow lowers contrast and brings the grey back.

## Priority 7: Add details that make the thickness believable

- **Layering:** where the front wall overlaps the back wall, the blue should double in depth, per "Overlapping translucent layers create deeper blue." You can also fill the vase with water to add another refractive layer, which reads as "shallow tropical water in sunlight."
- **Curvature:** the curved walls should bend and compress the background and the reflections ("Curved surfaces distort and concentrate reflections"). That only works if there is something bright behind the vase for it to refract.
- **Edge highlights:** aim for thin, bright speculars along the lip and the silhouette. A large softbox, or a window reflected in the glass, produces them.
- **Dispersion:** keep it slight ("minor chromatic aberration"). Blender 4.2+ has a Dispersion input on the Principled BSDF; you can also add a small Lens Distortion dispersion in post.
- **Imperfections:** add faint micro-scratches or slight variation in roughness. The metadata says CGI-like color stays tangible because "reflections, thickness and imperfections make objects tangible."

## Priority 8: Keep the composition minimal

"Materials are visually complex while compositions remain simple."

- Stick to the vase, the white table and a lot of negative space, with no props.
- Optionally, place an out-of-focus window behind the vase showing saturated blue sky and electric green grass. That adds the Frutiger Aero / Windows XP Bliss elements, and it gives the vase something bright and colored to refract and transmit.

---

## Rewritten prompt (example)

> A vase made of transparent blue acrylic standing on a glossy white table, backlit by strong sunlight. Light passes through the material: the thick base is deep translucent cobalt, the thin rim glows electric cyan, and where the front and back walls overlap the blue deepens. Blue caustics and cyan color spill pool across the table. High-key, near-overexposed blue-tinted whites with soft bloom and halation, crisp specular edge highlights, subtle chromatic dispersion. Minimal composition with large negative space, bright airy daylight, Y2K translucency, Frutiger Aero, early 2000s glossy optimism.

**Negative prompt:** opaque, solid color, painted, matte, flat shading, ceramic, toy plastic, grey, dull, muddy, underexposed, low contrast, grey shadow, neutral grey background, dark studio.

---

## How to check the next render

1. Is the rim lighter and more cyan than the base? (thickness is working)
2. Is there blue light or caustics on the table, and is the shadow blue? (transmission is working)
3. Can you see the background through the vase, distorted? (it reads as transparent rather than painted)
4. Do the brightest whites sit at or near 255, with blue at least as high as red, and are the shadows on white pale cyan rather than grey? (the white fix is working)
5. Do the speculars and the rim glow softly into nearby pixels without the whole frame looking hazy? (bloom is right)

## Watch for overcorrection

- **Absorption density too high:** the vase becomes a navy blob. The rim must stay pale cyan.
- **Whites hard-clipped everywhere:** you lose the edge of the table and the caustic pattern. Aim for soft clipping in the brightest areas only.
- **Bloom too strong or too wide:** contrast drops and the frame goes grey again.
- **Blue in both the surface color and the volume:** the vase flattens again. Keep the surface near white and let the volume carry the blue.
