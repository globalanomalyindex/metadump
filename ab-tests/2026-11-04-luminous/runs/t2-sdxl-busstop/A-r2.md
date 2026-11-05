POSITIVE

a quiet suburban bus stop on an empty sunny morning, (bus shelter built from transparent cobalt-blue acrylic panels:1.3), glossy translucent blue vinyl bench and frosted blue plastic timetable sign, (sunlight passing through tinted plastic, color glowing from inside the material:1.2), subsurface scattering, refraction, blue caustics and colored light pooling on the pale concrete sidewalk, soft rounded y2k industrial design, thick beveled acrylic edges catching bright specular highlights, (overexposed blue-tinted white light:1.1), bloom, gentle halation, high-key exposure, (hyperreal electric green grass verge:1.2), lush manicured lawns, clean low suburban houses softly out of focus, (deep saturated cerulean blue sky:1.2) with a few bright puffy white clouds, frutiger aero aesthetic, early 2000s translucent tech optimism, airy, luminous, glossy, calm and empty, no people, wide angle 35mm photograph, crisp detail, photorealistic, 8k

NEGATIVE

opaque plastic, painted surface, matte paint, solid flat color, chrome, brushed metal, glass with no tint, rust, graffiti, grime, litter, worn surfaces, overcast, gray sky, hazy pale sky, dusk, night, warm tones, orange cast, yellow tint, sepia, desaturated, muted colors, dry brown grass, dead lawn, heavy black shadows, low-key, underexposed, people, crowd, traffic, busy downtown, cyberpunk, neon signs, dark mood, film grain, noise, jpeg artifacts, blurry, lowres, warped perspective, distorted geometry, text, watermark, signature, logo, cartoon, flat illustration, low poly

NOTES

1. The "color inside the material" effect comes from the light-transport terms (light passing through, subsurface scattering, refraction, caustics), and the negative's "opaque, painted, matte" keeps SDXL from treating the blue as paint. If the shelter still looks painted, raise those weights first.
2. The overexposure terms can wash the sky out. If the sky goes pale, push the sky weight to 1.3 rather than dropping "overexposed" or "bloom", since those are what give the whites their blue tint.
3. Suggested settings: SDXL base at 1216x832 landscape, CFG 5-7, 30-40 steps, DPM++ 2M Karras. The (term:weight) syntax is for A1111/ComfyUI; remove the parentheses on tools that don't support it.
