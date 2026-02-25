# LTX-2 Motion Prompt Craft Skill

## Core Principle: EVERYTHING MOVES

LTX-2 generates video from a reference image + text prompt. The image already defines what the scene LOOKS like. Your motion prompt must describe **what CHANGES, what MOVES, what HAPPENS** — never what it looks like.

**STATIC = DEATH.** A static prompt produces a frozen, lifeless video. Every prompt must contain at least 3 motion elements.

---

## Novel-Like Descriptive Prompt Structure

Write prompts like the opening paragraph of a novel — vivid, cinematic, flowing prose that describes action unfolding in time.

### Template:
```
[CAMERA starts/is POSITION]. [SUBJECT performs PRIMARY ACTION], [SECONDARY MOTION happening simultaneously]. [ENVIRONMENTAL ELEMENTS doing THEIR THING]. [LIGHTING/ATMOSPHERE shifting or moving]. [CAMERA then MOVES to REVEAL/FOLLOW].
```

### Example:
> "Camera slowly dollies forward through morning fog. A cartoon tiger nervously glances left and right, clutching a golden key tighter as cracks spider across its surface. Dust particles drift lazily in a shaft of warm light from above. Shadows on the walls lengthen and shift. Camera continues pushing in as the key begins to glow brighter, illuminating the tiger's widening eyes."

### Key Writing Principles:
1. **Use present tense.** "The character walks" not "the character walked."
2. **Describe motion in sequence.** What happens first, then next, then after.
3. **Layer simultaneous motions.** Character moves + environment moves + camera moves.
4. **Include timing cues.** "Slowly," "suddenly," "gradually," "then."
5. **Be specific about direction.** "Drifts upward to the left" not just "moves."

---

## Camera Movement Vocabulary

### Linear Movements
| Term | Description | Emotion/Use |
|------|-------------|-------------|
| **Dolly in / Push in** | Camera moves toward the subject | Increasing tension, focus, intimacy |
| **Dolly out / Pull back** | Camera moves away from subject | Reveal, context, isolation |
| **Truck left/right** | Camera slides horizontally | Following action, scanning a scene |
| **Pedestal up/down** | Camera moves vertically | Power dynamics, scale reveal |
| **Zoom in** | Lens zooms (different from dolly) | Sudden focus, comedic emphasis |
| **Zoom out** | Lens widens | Surprise reveal, "oh no" moment |

### Rotational Movements
| Term | Description | Emotion/Use |
|------|-------------|-------------|
| **Orbit / Arc** | Camera circles the subject | Hero moment, showcasing, awe |
| **Dutch tilt** | Camera rotates on the roll axis | Unease, disorientation, something wrong |
| **Pan left/right** | Camera rotates horizontally on axis | Surveying, following, transition |
| **Tilt up/down** | Camera rotates vertically on axis | Reveal height/scale, looking up/down |

### Complex Movements
| Term | Description | Emotion/Use |
|------|-------------|-------------|
| **Crane up** | Camera rises vertically + tilts down | Epic reveal, establishing, godlike view |
| **Crane down** | Camera descends + tilts up | Entering a scene, grounding, intimacy |
| **Tracking shot** | Camera follows subject in motion | Energy, chase, journey |
| **Whip pan** | Ultra-fast pan | Scene transition, shock, comedy |
| **Handheld / Shaky** | Slight natural camera wobble | Documentary feel, urgency, chaos |
| **Steadicam float** | Smooth gliding movement | Dream-like, elegant, cinematic |

### LTX-2 Specific Tips:
- Combine 1-2 camera moves per clip (too many = confused output)
- "Camera slowly orbits" works better than "camera rapidly spins"
- End state matters: describe where the camera ends up
- Pair camera movement with subject movement for dynamic footage

---

## Element Motion Vocabulary

### Character/Subject Motions
| Motion | Prompt Phrasing |
|--------|----------------|
| Looking around | "eyes darting left and right, head turning nervously" |
| Reacting in shock | "jaw dropping, eyes widening, leaning back in surprise" |
| Walking/approaching | "stepping forward confidently, coat billowing behind" |
| Interacting with object | "fingers tracing along the surface, picking it up gently" |
| Celebrating | "arms shooting up in triumph, jumping with excitement" |
| Transforming | "body gradually shifting, morphing from shadow into light" |

### Object/Prop Motions
| Motion | Prompt Phrasing |
|--------|----------------|
| Breaking/Shattering | "cracks spider across the surface, fragments exploding outward in slow motion" |
| Assembling | "pieces floating together from all directions, clicking into place one by one" |
| Glowing/Pulsing | "a warm glow intensifies from within, pulsing rhythmically like a heartbeat" |
| Floating/Levitating | "rising gently off the surface, bobbing slightly in mid-air" |
| Spinning/Rotating | "spinning slowly on its axis, light catching different facets" |
| Melting/Dissolving | "edges softening and dripping downward, pooling into liquid light" |
| Growing/Expanding | "swelling in size, pushing outward, filling the frame" |

### Environmental Motions
| Motion | Prompt Phrasing |
|--------|----------------|
| Particles | "tiny luminous particles drifting upward like fireflies" |
| Fog/Mist | "tendrils of fog creeping along the ground, swirling around ankles" |
| Light rays | "shafts of golden light sweeping across the scene" |
| Water/Liquid | "ripples spreading outward from the center, reflections shimmering" |
| Wind effects | "leaves and papers swirling in a sudden gust, hair whipping" |
| Fire/Embers | "sparks rising from below, embers dancing in the updraft" |
| Shadows | "shadows stretching and shifting across the walls as light moves" |
| Weather | "rain streaking diagonally, splashing on surfaces, running down glass" |
| Growth | "vines and roots creeping across the surface, flowers blooming rapidly" |

### Transition/Transformation Motions
| Motion | Prompt Phrasing |
|--------|----------------|
| Morphing | "smoothly transforming from one shape into another, edges flowing like liquid" |
| Rippling | "a ripple distortion spreading outward from the point of impact" |
| Pixelating | "breaking apart into digital pixels that scatter and reform" |
| Folding | "reality folding in on itself like origami, revealing new layers" |
| Portal opening | "a circular tear in space opening, edges crackling with energy" |
| Time-lapse | "the scene rapidly cycling through day and night, shadows wheeling" |

---

## Emotion-to-Motion Mapping

### Funny / Roast Scenes
**Motion character:** Chaotic, exaggerated, things going comically wrong.
```
- Exaggerated reactions (double-takes, jaw drops, flailing arms)
- Objects behaving unexpectedly (keys running away, vaults playing keep-away)
- Quick, snappy movements with sudden stops
- Camera: slight handheld wobble, comedic zoom-ins on reactions
- Physics: bouncy, springy, cartoon-like
```
**Example:** "The character reaches for the key but it sprouts tiny legs and scurries away. Character lunges, misses, crashes into a pile of papers that explode upward. Camera zooms into their defeated expression. Papers flutter down around them."

### Serious / Explainer Scenes
**Motion character:** Smooth, deliberate, controlled, elegant.
```
- Measured character gestures (pointing, presenting, nodding)
- Objects assembling or transforming gracefully
- Slow, confident camera movements (steady dolly, gentle orbit)
- Environmental: calm particles, soft ambient shifts
- Physics: realistic, grounded, purposeful
```
**Example:** "Camera slowly dollies in as three translucent key fragments float gently from different directions, rotating as they align. They click together with a soft pulse of light. The camera continues forward, passing through the completed key into the vault beyond, revealing a warm glow inside."

### Hype / CTA Scenes
**Motion character:** Explosive, energetic, triumphant, fast.
```
- Bold character actions (fist pumps, leaping, powerful strides)
- Energy bursts, light explosions, radial waves
- Fast camera moves (crane up, dramatic pull-back reveal)
- Environmental: fireworks, particle storms, light beams
- Physics: powerful, weighty impacts followed by energy releases
```
**Example:** "Character slams their hand on the surface, sending a shockwave of golden light radiating outward. Camera rapidly cranes upward as hundreds of glowing orbs rise from the ground like lanterns. The entire scene bathes in warm triumphant light, particles swirling in a vortex overhead."

### Tense / Problem Scenes
**Motion character:** Uncomfortable, building pressure, things closing in.
```
- Nervous tics (fidgeting, looking over shoulder, backing away)
- Shadows creeping, walls closing, objects cracking
- Camera: slow push-in creating claustrophobia, dutch tilt
- Environmental: flickering lights, smoke, darkening atmosphere
- Physics: heavy, oppressive, sticky
```
**Example:** "Camera slowly pushes in as cracks spread across the vault door, light leaking through in thin beams. Character steps backward, shadows from all directions stretching toward them. The single overhead light flickers, each flicker bringing the shadows closer. Dust falls from the ceiling."

### Hopeful / Solution Scenes
**Motion character:** Opening up, brightening, expanding, breathing.
```
- Characters relaxing, smiling, breathing deeply
- Light breaking through, spaces opening up
- Camera: smooth pull-back or crane-up reveal
- Environmental: clouds parting, sunrise, flowers blooming
- Physics: light, airy, floating
```
**Example:** "A crack of golden light splits the darkness in the center of frame, widening steadily. Camera pulls back as the light expands, washing over the character's face — their expression shifting from worry to wonder. Warm particles begin rising from the ground like pollen, the entire atmosphere transforming from cold blue to warm amber."

---

## Audio Description Templates (LTX-2 Audio Sync)

LTX-2 can generate synced audio. Add audio descriptions at the end of your prompt for richer output.

### Template:
```
[Motion prompt]. Audio: [description of sounds that match the visuals].
```

### Audio Description Examples:

**Mechanical/Tech:**
> "Audio: soft mechanical whirring and clicking, electronic hum that builds in pitch, a satisfying magnetic snap as pieces connect."

**Nature/Ambient:**
> "Audio: gentle wind rustling through leaves, distant birdsong, the soft creak of wooden structures, water trickling."

**Impact/Action:**
> "Audio: a deep resonant boom as the surface is struck, followed by a shimmering ring that fades slowly, crackling energy."

**Magical/Transformation:**
> "Audio: a rising crystalline chime, soft whooshing as particles move, a warm harmonic tone that swells and resolves."

**Comedic:**
> "Audio: a cartoonish boing as the character bounces, a slide whistle as they slip, a comedic thud on impact."

**Atmospheric/Mood:**
> "Audio: low ominous drone, distant echoing footsteps, a faint heartbeat-like pulse that grows louder."

---

## 5+ Cinematic Motion Prompt Examples

### 1. Wallet Security Hook (Funny/Tense)
**Scene:** Character realizes their single-key wallet is vulnerable.
```
Camera handheld, slight nervous wobble. A cartoon tiger clutches an oversized golden key, eyes darting frantically as shadowy hands emerge from every crack in the walls, reaching and grabbing. The key begins cracking down the middle, golden light leaking from the fractures. Tiger's grip tightens, knuckles whitening. One shadow hand gets close enough to touch the key and it shatters into a thousand glittering fragments that scatter outward. Camera quickly zooms into the tiger's horrified face as fragments rain down around it. Audio: creaking metal stress, a sharp crystalline shatter, fragments tinkling on the ground.
```

### 2. Three-Key Solution (Smooth/Confident)
**Scene:** PawPad's three-vault system explained visually.
```
Camera starts on a wide shot, then slowly dollies forward. Three translucent vault doors, each on a separate floating island, simultaneously swing open with a heavy mechanical motion. From inside each vault, a glowing key fragment rises and floats toward the center of the frame. The fragments rotate gently, aligning their edges, then snap together with a pulse of warm light that radiates outward. The camera slowly orbits the completed key as it hovers, light particles spiraling upward around it like a gentle tornado. The three vaults in the background begin glowing with the same warm light. Audio: three distinct heavy locks clicking open, a rising harmonic tone as fragments meet, a deep satisfying resonance on connection.
```

### 3. Phone Lost Recovery (Emotional/Hopeful)
**Scene:** Phone breaks but crypto is safe.
```
Camera tracking downward following a phone as it tumbles in slow motion toward wet concrete. It hits the ground — screen shatters, cracks radiating in a spiderweb pattern, fragments of glass bouncing upward catching the light. Camera pauses on the broken phone, rain drops splashing around it. Then, a warm golden light begins seeping up through the cracks, growing brighter. A holographic phoenix shape rises from the broken screen, spreading luminous wings, carrying a small glowing key upward. Camera cranes up following the phoenix as it soars, the rain drops around it turning to golden sparks. Audio: the dull crack of impact, glass tinkling, silence — then a warm rising tone as the phoenix emerges, wings creating a soft whooshing sound.
```

### 4. AI Trading Bot at Work (Funny/Split Energy)
**Scene:** Bot trades while user sleeps.
```
Camera slowly trucks right across a split scene. Left side: a person in pajamas sleeping peacefully, blanket rising and falling with gentle breaths, a nightlight casting warm amber glow, a cat curled at their feet shifting slightly. Right side: through a doorway, a small robot in a comically tiny suit frantically working — arms blurring across multiple holographic screens, charts and numbers flying, coffee cup rattling on the desk. Green arrows shoot upward on the screens. The robot slams a button triumphantly and confetti explodes from nowhere. Camera keeps trucking right, leaving the sleeping person behind, pushing into the robot's chaotic workspace. Audio: soft snoring from the left, increasingly frantic typing and beeping from the right, a satisfying cha-ching as the trade lands.
```

### 5. CTA Finale — Hype Energy (Explosive/Triumphant)
**Scene:** Final call to action with maximum energy.
```
Camera holds on a medium shot as the character plants their feet and raises a glowing card above their head. Energy crackles around the card, arcs of light connecting to the ground. Character brings the card down sharply — BOOM — a radial shockwave of golden light erupts from the point of impact, rushing outward in all directions. Camera rapidly cranes upward, revealing the shockwave spreading across an entire cityscape below, lighting up every building. Hundreds of tiny glowing orbs rise from the city like floating lanterns. The camera keeps rising until the orbs fill the sky, swirling into a massive glowing pattern overhead. Everything bathes in warm triumphant light. Audio: building electrical charge, a massive satisfying bass impact, rushing wind of the shockwave, then a triumphant swell of warm harmonic tones.
```

### 6. Data Privacy Metaphor (Mysterious/Elegant)
**Scene:** Data entering an encrypted vault, processed without being seen.
```
Camera starts close on a stream of glowing data symbols flowing like a river. Camera follows the stream as it enters a massive crystalline structure — the data passes through the outer wall and immediately transforms into unreadable scrambled light. Inside, mechanical arms sort and process the scrambled light, never unscrambling it. A clean, simple result emerges from the other side — a small glowing answer floating gently outward. Camera orbits slowly around the crystal structure, showing data entering from many directions but only clean answers exiting. The crystal pulses with a gentle inner light like breathing. Audio: soft digital chimes as data flows, a deep resonant hum from the crystal, a clear bell tone as each answer emerges.
```

---

## Critical Rules

1. **NEVER write static descriptions.** "A secure digital vault" generates a frozen image. ALWAYS describe what MOVES, CHANGES, SHIFTS, TRANSFORMS.

2. **Minimum 3 motion layers per prompt:**
   - Layer 1: Subject/character motion
   - Layer 2: Environmental/particle motion
   - Layer 3: Camera motion
   Without all three, the video feels flat.

3. **NEVER repeat the image prompt.** The reference image already defines the visual. Your motion prompt adds TIME — what happens NEXT.

4. **Use temporal language.** "Then," "as," "while," "suddenly," "gradually" — these words create sequence and movement.

5. **Match motion intensity to emotion.** Funny = chaotic. Serious = smooth. Hype = explosive. Tense = slow-building. Hopeful = opening/expanding.

6. **Describe the JOURNEY, not the destination.** Don't say "the key is assembled." Say "fragments float together, rotate to align, and snap into place with a pulse of light."

7. **End with a visual punch.** The last moment of the clip should be the most dynamic — a reveal, an explosion, a transformation, a reaction.

8. **Keep prompts 40-80 words.** Too short = not enough direction. Too long = LTX-2 gets confused and tries to do everything at once.

9. **Each sub-clip gets a UNIQUE motion prompt.** Even for the same scene, sub-clip A and sub-clip B should describe different actions, angles, and moments. Never reuse the same prompt.

10. **Include audio descriptions** when the scene has distinctive sounds. LTX-2 generates better synced video when it understands the audio landscape.
