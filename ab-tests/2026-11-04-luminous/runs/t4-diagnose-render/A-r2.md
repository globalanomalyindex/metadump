# Fixing the "painted blue plastic" vase and grey whites

## Diagnosis

Two separate failures:

1. **The vase looks painted** because its blue sits on the surface as a uniform tint, and light reaches it from the front. Translucency only shows up when light travels *through* the material toward the camera, and when the colour gets deeper with thickness. Without both, a renderer (or an image model) draws a coloured shell, and that reads as opaque plastic.
2. **The whites look grey** because the image is exposed and tone-mapped like a neutral studio shot. The aesthetic calls for "overexposed blue-tinted whites": white surfaces that sit at or past clipping with a cool cast. A white table at 75-85% brightness under neutral light will always look like grey card.

Each fix below has a prompt version and a scene/lighting version. They're ordered by how much each one changes the result.

---

## Prioritized changes

### 1. Put the blue inside the material, not on it (biggest single fix)

**Scene/material:**
- Set transmission to 1.0. Use IOR about 1.49 for acrylic (PMMA) and about 1.5-1.55 for clear vinyl. Keep roughness low (0.02-0.08) for polished acrylic, or 0.15-0.25 on one surface only if you want a slightly frosted vinyl feel.
- Keep the **surface colour near white**. Put the blue into **volume absorption**, which darkens with depth (Beer-Lambert), instead of a base or transmission tint, which applies the same amount at every surface crossing. Thin parts then read pale cyan, almost clear, and thick parts read deep electric blue. That gradient is what "colour inside the material" means.
  - Blender: Principled BSDF with Transmission 1 and a very pale Base Color. Plug a Volume Absorption node (blue colour) into the Material Output's Volume socket, and tune density for your scene scale until a 3-5 mm wall looks pale and a 2-3 cm base looks saturated.
  - Other renderers: use "absorption colour / absorption distance", "transmission depth", or "medium" settings, not the diffuse colour.
- **Give the mesh real thickness.** Model the walls as solid (solidify, 3-5 mm) with a thick, heavy base and a rounded lip, and consider some variation in wall thickness. A single-sided or "thin-walled" mesh can't show depth-based colour and will always look painted.
- Don't use emission or a strong subsurface setting to make the blue. Subsurface makes it look milky and opaque.
- Target colours: thin rim/walls about `#BFE6FF`, mid-body about `#5DB8FF`, thick base about `#0A6CFF` to `#0050E6`.

**Prompt:** replace "blue plastic vase" with "vase of clear blue-tinted cast acrylic, glass-like transparency, the blue concentrated deep in the thick base and fading to pale cyan at the thin rim". Drop "plastic" on its own: image models read it as opaque injection-moulded toy plastic. Use "acrylic", "PMMA", "tinted resin" or "transparent vinyl".

### 2. Backlight it and remove the front key light

**Lighting:**
- Move the main light **behind** the vase, 130-160 degrees from the camera axis and raised 20-35 degrees, so it shines through the vase toward the lens. A large soft source (big area light, or a sun with some angular size) works best. This light should be the strongest one in the scene.
- **No direct front key.** Front light shows the outer surface, and the outer surface is the "plastic" look. If the front face goes muddy, add a large white bounce card or a very weak fill, at most a quarter of the back light's intensity.
- Add one tall strip softbox to the side for a clean vertical specular streak down the body. That streak is the glossy Y2K/Aero highlight.

**Prompt:** "backlit by bright sunlight from behind, light passing through the vase, the vase glowing from within". Remove "studio lighting", "softbox lighting", "even lighting" and "soft light". Those terms produce front-lit catalogue shots with grey seamless backgrounds.

### 3. Overexpose on purpose, cool the white balance, and stop the tone-mapper greying highlights

**Render/camera:**
- Raise exposure by about +1 to +1.5 stops. Expose for the vase and let the table go to 92-100% display brightness, with the brightest patches (caustic hotspots, speculars, the area around the vase base) clipping to pure white.
- Aim for whites around `#EEF6FF` to `#F7FBFF`: bright with a faint blue/cyan cast. Not neutral `#FFFFFF` everywhere, and never `#D0D0D0`-style grey.
- **White balance:** make the lights cooler than the camera's white point. For example, run lights at 7000-9000 K against a 6500 K camera, or set the camera WB lower (about 4800-5200 K) under daylight-balanced lights. Either way, every white picks up the blue cast.
- **Tone mapping:** filmic-style curves at base/medium contrast (Blender Filmic or AgX Base, ACES default) compress highlights and flatten them toward grey when the scene is underexposed. Fix exposure first, then use a punchier look (in Blender AgX, "Punchy" or "High Contrast"). Keep the curve's highlight roll-off: it lets the saturated blue fade to white-cyan in the hottest areas, which is the overexposed luminous look you want.
- **Shadows:** lift and tint them blue (around `#A9CCFF` on the table), never grey or black. Nothing in this aesthetic should go darker than the thickest part of the vase.

**Prompt:** "high-key, overexposed, blown-out highlights, cool white balance, blue-tinted whites, bright clear daylight". Add negatives: "grey, dull, muted, underexposed, overcast, neutral white balance, warm tones, beige".

### 4. Make the white table glow instead of reflecting dimly

**Scene:**
- Raise the table's albedo to 0.85-0.95. Many "white" materials default to 0.7-0.8, which renders as grey.
- Make it **glossy white acrylic or laminate** (roughness about 0.05-0.15), so it reflects blue from the sky and the vase.
- Strongest option: make the tabletop a **lightbox**, either translucent white acrylic with a light underneath or a faint emissive layer. The white then really glows, and the vase gets lit from below through its base. This is the classic Y2K translucent product-shot setup, and it fixes the grey whites and the flat vase together.

**Prompt:** "on a glowing glossy white acrylic table", "light-table glow", "luminous white surface".

### 5. Give the refraction something saturated to bend

**Scene:**
- A transparent object in a white void has nothing to refract, so it only shows its own tint, which looks flat. Use the rest of the aesthetic as the environment: a **saturated blue sky** HDRI or gradient dome (zenith about `#2A8CFF`, horizon about `#CDEBFF`) and an **electric green grass** plane or horizon line behind the vase (about `#39E639` to `#4CFF3A`). Push saturation so it reads hyperreal.
- Keep the grass and sky out of focus behind the vase but visible *through* it. Distorted, magnified green and blue bands inside the vase body read as colour that lives inside the material.
- Fresnel reflections of the blue sky along the vase's grazing edges add a second, reflected layer of colour on top of the transmitted one.

**Prompt:** "refraction showing a distorted saturated blue sky and electric green grass through the vase", "hyperreal green lawn and vivid blue sky in soft focus behind".

### 6. Caustics and coloured shadows

**Scene:**
- A real tinted acrylic vase throws **bright cyan caustics** and a **translucent blue shadow** with a hot focus point. A grey opaque shadow is enough on its own to make the vase read as solid plastic.
- Cycles: turn on shadow caustics. Mark the vase as a caustics caster, the table as a caustics receiver, and enable shadow caustics on the back light. Elsewhere, enable caustics or photon mapping, or fake them with a projected caustic texture (gobo) in blue/cyan.
- Make sure shadows from transmissive objects are coloured or transmissive, not opaque.

**Prompt:** "projecting bright cyan caustics and a luminous translucent blue shadow onto the table".

### 7. Edges and speculars: the light-piping cue

**Scene:**
- Polished acrylic edges glow brighter than the faces because of total internal reflection. Keep a **clean, bevelled rim** (small bevel, 2-3 segments) so the edge catches and carries light. Sharp 90-degree edges with no bevel kill this effect.
- Speculars should be **hot and clipped**: small, sharp, pure white. Dim, broad speculars read as satin plastic.
- An optional clearcoat layer (low roughness) gives the double-gloss "wet" Frutiger Aero sheen.

**Prompt:** "glowing light-piped edges, crisp blown-out specular highlights, wet glossy sheen".

### 8. Render settings that quietly turn transparency grey

- **Too few light bounces** make the inside of transmissive objects go dark or grey. In Cycles, use Transmission and Glossy bounces of 12 or more and Total bounces of 16 or more for a thick-walled vase.
- In Eevee, turn on raytraced/screen-space refraction for the material and the scene. Otherwise the vase renders as a tinted shell with no visible refraction, which is a common cause of the flat painted look.
- Denoisers can smear caustics into grey mush. Render enough samples that the caustic hotspots come out clean before denoising.

### 9. Post: bloom, halation, highlight grading

- Add a **soft bloom/glare** on highlights above about 0.9, with a slight cyan tint, so the overexposed areas visibly glow.
- Grade **highlights toward cyan-blue** and **shadows toward blue**. Keep the vase and grass saturated in the midtones, and let the highest values go to white-cyan.
- Optionally add a very small amount of chromatic dispersion on the vase (Blender 4.2+ has a Dispersion input on Principled/Glass BSDF) for faint rainbow fringes at the edges. A little is enough: too much reads as a lens flaw.
- Don't add global vignetting or a contrast curve that crushes highlights. Both put grey back into the whites.

---

## Rewritten prompt (for image models, or as the brief for a 3D shot)

> Product photograph of a vase made of clear blue-tinted cast acrylic, glass-like transparency, the blue concentrated deep inside the thick heavy base and fading to pale cyan at the thin rim, backlit by bright sunlight from behind so light passes through the vase and it glows from within, bright cyan caustics and a luminous translucent blue shadow on a glowing glossy white acrylic table, glowing light-piped edges, crisp blown-out specular highlights, refraction showing a distorted saturated blue sky and hyperreal electric green grass in soft focus behind, high-key overexposed blue-tinted whites, cool white balance, soft bloom and halation, frutiger aero, y2k translucent product aesthetic, hyperreal, crisp

**Negative prompt:** opaque, solid, painted, matte, ceramic, milky, frosted all over, flat shading, front-lit, on-camera flash, studio grey backdrop, grey, dull, muted, desaturated, underexposed, overcast, neutral or warm white balance, beige, dark shadows, black shadows, heavy vignette

---

## Checks for the next render

1. **Thickness test:** is the base noticeably deeper blue than the rim? If the blue is the same everywhere, it's still a surface tint (go back to #1).
2. **Show-through test:** can you see distorted sky or grass through the body? If not, add or brighten the environment (#5) and check refraction and bounces (#8).
3. **Shadow test:** is the shadow blue and luminous with a bright caustic? If it's grey, see #6. If it's dark, the key light is still in front (#2).
4. **White test:** sample the table with an eyedropper. It should be at least 92% brightness with blue slightly above red and green. If it reads 75-85% neutral, raise exposure or albedo and cool the WB (#3, #4).
5. **Glow test:** do the rim and the speculars clip to white and bloom slightly? If not, see #7 and #9.
