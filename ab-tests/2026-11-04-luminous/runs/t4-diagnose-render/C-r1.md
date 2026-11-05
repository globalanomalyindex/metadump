# Diagnosis: translucent blue vase looks like painted plastic, whites look grey

## What is going wrong

The two problems have one cause. The render treats blue as a coating on the vase's surface and white as a mid-tone. In this aesthetic, the blue is the material itself and the white is the brightest thing in the frame. The metadata's core principle is "the difference between an object being colored blue and being made of blue," and the style formula depends on "physically believable light transmission." A painted look means light is bouncing off the vase instead of passing through it. Grey whites mean the exposure, the light direction and the shadows are all working against high-key.

The fixes below are ordered by impact. Each one has a **prompt change** (for image generators) and a **lighting/scene change** (for a 3D renderer or a real shoot). Do them in order: 1-3 fix most of the problem.

---

## 1. Describe a material, not a color (highest impact)

**Why it looks painted:** a phrase like "blue vase," "glossy blue plastic vase" or "translucent blue vase" makes blue an adjective. Image models link "blue vase" strongly to glazed ceramic and opaque injection-molded plastic, so they render a surface color with a gloss highlight on top. In 3D, the same mistake is a blue Base/Diffuse color on a surface shader.

**Prompt change:**
- Replace "blue vase" with something like: *"a vase cast from transparent cobalt-tinted acrylic"* or *"a vase made of water-clear resin dyed electric cyan."* Put the material noun first and make the color part of it.
- Say that light goes through it: *"sunlight passing through the blue acrylic,"* *"see-through, the tabletop visible and refracted through the vase."*
- Describe how the color varies with thickness, since that is what makes color look like it is inside the material (metadata: "thicker transparent material looks darker; thin edges catch and transmit more light"): *"the thick solid base glows deep cobalt, the thin walls and rim are pale electric cyan."*

**3D change:**
- Put the blue in the volume, not the surface. Set the surface to a clear dielectric: transmission 1.0, roughness about 0-0.03, IOR about 1.49 (acrylic), no diffuse or subsurface component, and base/transmission color white or nearly white. Then add blue through volume absorption (Cycles: Volume Absorption or Principled Volume absorption color; Octane/Redshift: medium/absorption). Increase density until the thick base goes deep cobalt while the walls stay pale cyan. A surface tint makes every part of the vase the same blue, and that sameness is the painted look.
- Give the mesh real thickness, varied on purpose: thin walls (a few mm), a heavy solid base, a rounded lip with real thickness (bevel it, don't leave a knife edge). Without varied thickness, absorption has nothing to work with.

---

## 2. Backlight it; the main light belongs behind the vase

**Why:** a translucent object lit from the front shows only its surface, so you see reflected color, which is paint. It only reads as glass-like color when light comes through toward the camera. All of the metadata's lighting queries point this way: "backlit blue acrylic," "sunlight through colored plastic," "light transmission aesthetic."

**Prompt change:** add *"strong low sunlight from behind the vase, backlit, light streaming through the blue acrylic toward the camera."* Remove "front lit," "softbox," "even studio lighting" and "flat lighting."

**Lighting change:**
- Key light: a hard sun or small strong source behind the vase, about 120-160 degrees from camera, low elevation (about 15-35 degrees). A low angle throws the transmitted light forward across the table where the camera sees it.
- Make the backlight about 3-4x the strength of any front fill. Keep the front fill large and soft, there only to keep the face of the vase from going black.
- Add one tall strip or window-shaped source to the side to put a long vertical specular highlight on the curved body ("curved surfaces distort and concentrate reflections").

---

## 3. Fix exposure so the whites are luminous instead of grey

**Why the whites go grey:** usually several of these at once:
- **Tone mapping:** Filmic/AgX-style transforms map a scene value of 1.0 well below display white, so a "white" table lit normally lands around light grey.
- **Default albedo:** many renderers default to about 0.8 grey. Under modest light, that reads as dull grey.
- **Exposing for the mid-tones:** you exposed for the vase, so the table sits a stop or more below where this aesthetic wants it.
- **Grey shadows:** a vase behaving as if opaque casts a neutral grey shadow, which pulls the whole table toward grey.
- **Prompt words that push toward contrast:** "cinematic," "moody," "dramatic," "studio," "product shot on seamless" all pull toward controlled mid-tones.

**Prompt change:** add *"overexposed high-key daylight, sun-drenched, optical white table, blue-tinted luminous whites near clipping, soft highlight clipping, bloom and halation."* Remove "cinematic," "moody," "dramatic," "dark," "studio lighting." Add negatives: *grey, dull, underexposed, muddy shadows, low key.*

**3D/photo change:**
- Table albedo about 0.9, not 0.8.
- Expose for the whites. Raise exposure (often +1 to +1.5 stops under AgX/Filmic) until the lit tabletop reads about 240-255 in sRGB, and the brightest sunlit patches and highlights clip softly ("whites approach pure white with diminished detail").
- Cool the white balance slightly so the whites lean blue (roughly #F2F8FF-#F7FBFF for lit white). Do it with white balance or the light color, not a blue color grade: a global blue filter is painting again, and it greys the whites.
- Fill the shadows with bright light: a big bright sky dome or white bounce cards, so table shadows are pale and bluish, never mid-grey. In high-key the darkest part of the table should still be light.

---

## 4. Let the blue fall on the white: colored shadows, caustics, spill

**Why:** the clearest sign that color is inside a material is that it leaves the object and lands on nearby surfaces. The metadata lists this twice: "blue illumination spills onto adjacent whites" and "highlights merge visually with cyan material." A grey shadow next to a blue vase says the vase is opaque.

**Prompt change:** *"the vase casts a luminous cyan shadow with a bright caustic focus on the white tabletop; blue light bleeds into the surrounding whites."*

**3D change:**
- Turn caustics on, or the transmitted light will not reach the table (Cycles: Shadow Caustics on the light, Cast Shadow Caustics on the vase, Receive Shadow Caustics on the table; Octane/Redshift/LuxCore: enable caustics or photon mapping in the GI settings). Make sure the vase's shadow ray is transmissive and not treated as opaque.
- Check: the shadow should be blue and have a bright concentrated spot or ring inside it where the curved body focuses the sun.
- If caustics are too noisy or slow, fake it: a cyan-tinted projected light or gobo shaped like the caustic, plus a blue tint on the shadow region. A believable fake beats a grey real shadow.

---

## 5. Give the transparency something to show

**Why:** a transparent object shows its surroundings. Against a plain grey or neutral studio it has nothing to refract, so it reads as a solid shape. The metadata gives two rules: "transparent blue becomes brighter against white," and the color "changes with illumination, backdrop, thickness, curvature and layering."

**Prompt change:** *"in a sunlit white interior; through a window, a saturated blue sky and hyperreal electric green grass are reflected and refracted, distorted, in the curved acrylic."* This also brings in the client's sky and grass without cluttering the composition.

**Scene change:**
- Put a white wall or sweep directly behind the vase, so the body reads bright, saturated cyan against it.
- Use a sunny sky-and-meadow HDRI (or a window looking out on one) for reflections and refraction. Push the HDRI's green and blue saturation toward the hyperreal "Bliss" look. Seen as small distorted shapes inside the vase, they become the "localized optical complexity" the composition section asks for.
- If the vase holds water, render it (IOR 1.33). The extra boundary adds internal refraction and a second layer of blue ("overlapping translucent layers create deeper blue").

---

## 6. Edge highlights and glowing rims

**Why:** thin bright edges are one of the metadata's main retrieval signals ("specular edge highlights," "edges catch thin bright highlights," "glowing edge"). Polished tinted acrylic also carries light along its walls and glows at cut edges. A painted object has a soft blob highlight; a transparent one has crisp thin lines along every curve and lip.

**Prompt change:** *"crisp thin specular highlights along the curved edges, glowing polished rim, internal reflections."*

**Scene change:** roughness near 0; bevel the lip and base edges so they have a small rounded face to catch light; place the strip light from item 2 so its reflection runs along the silhouette. Check that the rim is the brightest, palest-cyan part of the vase.

---

## 7. Prompt hygiene and word order

- **Material and light first, nostalgia tags last.** Put "Frutiger Aero," "Y2K," "early 2000s CGI" and "glossy interface" at the end, or drop them. Those tags pull models toward glossy 2D icon gradients, which are literally painted-on highlights. That is the opposite of what you want here. If you keep one, *"Frutiger Aero physical media"* or *"Y2K translucency"* is closer.
- **Prefer "photograph" or "photoreal" over "3D render."** "3D render" alone often gives cheap uniform CGI plastic. The metadata's tension is CGI-like color in an object made tangible by "reflections, thickness and imperfections."
- **Add small imperfections, sparingly:** a few tiny bubbles in the resin, faint mold lines, very slight surface roughness variation. Keep it "immaculate" overall.
- **Negative prompt:** *opaque, ceramic, glazed pottery, painted, matte, solid color, uniform color, flat lighting, front lighting, grey background, grey shadows, dull whites, underexposed, muddy, moody, dramatic, dark studio.*

---

## 8. Post-processing finish (last, small)

- Bloom/halation on highlights only: a tight bright glow plus a wide faint one, so highlights "bleed into neighboring pixels."
- Slight chromatic aberration at the brightest edges ("minor chromatic aberration" is listed as a micro-detail). Keep it subtle.
- Lift the top of the tone curve, don't add saturation. If the blue still looks flat after steps 1-4, the fix is more thickness variation or more backlight, not a saturation slider.

---

## Rewritten prompt (drop-in)

> Photograph of a vase cast from transparent cobalt-tinted acrylic, water-clear resin dyed electric cyan, standing on an optical-white table in a sun-drenched white room. Strong low sunlight from behind the vase streams through the material: the thick solid base glows deep cobalt, the thin walls and polished rim glow pale electric cyan, with crisp thin specular highlights along the curved edges. The vase casts a luminous cyan shadow with a bright caustic focus across the tabletop toward the camera; blue light bleeds into the surrounding whites. Through and in the curved acrylic, a window shows a saturated blue sky and hyperreal electric green grass, refracted and distorted. Overexposed high-key daylight, blue-tinted optical whites near clipping, soft bloom and halation, minor chromatic aberration at the brightest edges. Minimal composition, generous negative space. Y2K translucency, Frutiger Aero physical media.
>
> Negative: opaque, ceramic, glazed pottery, painted, matte, uniform solid color, front lighting, flat lighting, grey background, grey shadows, dull whites, underexposed, muddy, moody, dramatic, dark studio.

---

## Quick check: is it fixed?

1. The vase's blue changes across the object: palest at the rim and thin walls, deepest at the base and where the front and back walls overlap. No large area of flat, even blue.
2. You can see the table, and the window's sky and grass, through the vase, bent by refraction.
3. The shadow on the table is blue and has a bright caustic spot. It is not grey.
4. The lit tabletop reads about 240-255, leans slightly blue, and the brightest areas clip softly with bloom.
5. Thin bright highlights run along the rim and silhouette.
6. The darkest area of the table is still pale, not mid-grey.

If 1 and 3 fail, go back to items 1 and 2 (material and backlight). If 4 and 6 fail, go back to item 3 (exposure and fill).
