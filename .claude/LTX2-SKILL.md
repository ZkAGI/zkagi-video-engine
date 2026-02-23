# LTX-2 Video Generation Skill — ComfyUI Integration

## Overview
LTX-2 is a 19B parameter audio-video foundation model by Lightricks. It generates synchronized video AND audio in a single pass. Running on RTX 5090 (32GB VRAM) via ComfyUI Desktop.

**Connection:** `COMFY_URL="http://$(ip route show default | awk '{print $3}'):8001"`

## Capabilities
- **Text-to-video** — generate video from text prompt
- **Image-to-video** — animate a reference image (BEST QUALITY)
- **Audio-video sync** — generates matching audio with video
- **Video extension** — extend existing clips
- **Spatial upscale** — 2x resolution upscale with dedicated model
- **Distilled fast mode** — 8-step generation (vs 20-step normal)
- **LoRA support** — style/motion/likeness LoRAs
- **Up to 4K resolution, 50 FPS, 20 seconds per clip**

## Models Available on This System
```
checkpoints/      → ltx-2-19b-dev-fp8.safetensors
text_encoders/    → gemma_3_12B_it.safetensors (or gemma_3_12B_it_fp8_scaled.safetensors)
latent_upscale/   → ltx-2-spatial-upscaler-x2-1.0.safetensors (check if available)
loras/            → ltx-2-19b-distilled-lora-384.safetensors (check if available)
```

Always verify at runtime:
```bash
curl -s "$COMFY_URL/object_info/LTXAVTextEncoderLoader" | python3 -c "
import sys,json; d=json.load(sys.stdin)['LTXAVTextEncoderLoader']['input']['required']
print('Text encoders:', d.get('text_encoder', ['?'])[0])
print('Checkpoints:', d.get('ckpt_name', ['?'])[0])
"
```

## Recommended Settings

### Resolution (BEFORE upscale — actual output is 2x)
| Aspect | Width | Height | Output after 2x |
|--------|-------|--------|------------------|
| 3:2    | 768   | 512    | 1536×1024        |
| 16:9   | 768   | 432    | 1536×864         |
| 1:1    | 640   | 640    | 1280×1280        |
| 9:16   | 432   | 768    | 864×1536         |

**Width & height must be divisible by 32.**

### Frames & Duration
| Frames | Duration @25fps | Use case |
|--------|----------------|----------|
| 97     | 3.88s          | Quick cuts, transitions |
| 121    | 4.84s          | Standard scene clip |
| 161    | 6.44s          | Extended scene |
| 201    | 8.04s          | Long scene |
| 257    | 10.28s         | Maximum length (highest VRAM) |

**Frame count must be 8n+1 (97, 105, 113, 121, 129, ... 257).**

### Quality Settings
| Mode | Steps | CFG | LoRA | Speed | Quality |
|------|-------|-----|------|-------|---------|
| Full quality | 20 | 4.0 | none | Slow (~3min) | Best |
| Distilled fast | 8 | 1.0 | distilled-lora | Fast (~1min) | Great |
| Quick preview | 4 | 1.0 | distilled-lora | Very fast | Good |

**Recommendation: Use distilled-lora (8 steps) for ALL production use. Quality is comparable to 20 steps and much more stable.**

### FPS Guidelines
- **Motion-heavy** (action, transitions, particles): 25-30 FPS
- **Static/close-up** (face, object, slow pan): 15-24 FPS
- **Default: 25 FPS**

---

## PROMPTING GUIDE (CRITICAL)

LTX-2 responds to DESCRIPTIVE, NOVEL-LIKE prompts. Not keywords.

### Structure of a GOOD prompt:
```
[SCENE SETUP] + [SUBJECT DESCRIPTION] + [CAMERA MOVEMENT] + [MOTION/ACTION] + [ATMOSPHERE/MOOD] + [AUDIO DESCRIPTION]
```

### Examples:

**For a crypto/tech scene:**
"A close-up shot of a glowing digital vault slowly opening, revealing streams of golden light pouring out. The camera pushes forward through the vault door as holographic numbers and symbols float past. Particles of light drift upward like fireflies. The atmosphere is futuristic and mysterious, with deep blue and purple tones. A deep electronic hum builds as the vault opens, followed by a crystalline chime."

**For an action/reveal scene:**
"A dramatic wide shot of digital chains shattering in slow motion, each link exploding into fragments of light. The camera pulls back to reveal a figure standing free, surrounded by floating shards that catch the light. Sparks cascade downward. The mood shifts from dark and oppressive to bright and liberating. The sound of breaking glass echoes, followed by a rising orchestral swell."

**For a peaceful/trust scene:**
"A slow, sweeping aerial shot over a serene digital landscape, with rolling hills made of soft gradients and trees rendered in gentle geometric shapes. Soft clouds drift across the scene. The camera glides forward smoothly, descending toward a glowing structure in the distance. Warm golden light bathes everything. Gentle ambient music plays with soft piano notes and nature sounds."

### BAD prompt habits (AVOID):
- ❌ "crypto wallet security" — too vague, keyword-like
- ❌ "a shield" — no motion, no camera, no atmosphere
- ❌ "neon city" — static description
- ❌ Short prompts under 20 words — LTX-2 needs detail

### Motion keywords to weave into prompts:
**Camera:** "slowly pushing forward", "dolly shot", "orbiting around", "pulling back to reveal", "tracking shot following", "pan left", "crane up", "close-up transitioning to wide"
**Elements:** "particles drifting", "light rays sweeping", "energy pulsing", "waves rippling", "fragments floating", "sparks cascading"
**Transitions:** "shifting from dark to bright", "focus pulling", "morphing into", "dissolving away"

### Audio in prompts (LTX-2 generates audio too!):
Include audio descriptions at the end of prompts:
- "The sound of digital beeps and a low electronic hum"
- "A rising orchestral swell with deep bass"
- "Gentle ambient music with soft chimes"
- "The crackle of energy and a dramatic boom"

---

## PRODUCTION WORKFLOW: Image-to-Video with Hires.fix

This is the OPTIMAL pipeline. 3 stages:

### Stage 1: Generate base video from reference image
```python
workflow = {
    # Load model + text encoder
    "1": {
        "class_type": "LTXAVTextEncoderLoader",
        "inputs": {
            "text_encoder": "DISCOVERED_TEXT_ENCODER",
            "ckpt_name": "DISCOVERED_CHECKPOINT",
            "device": "cpu"
        }
    },
    # Load + preprocess reference image
    "2": {
        "class_type": "LoadImage",
        "inputs": {"image": "UPLOADED_IMAGE_NAME.png"}
    },
    "3": {
        "class_type": "LTXVPreprocess",
        "inputs": {"image": ["2", 0]}
    },
    # Positive prompt (MOTION-FOCUSED)
    "4": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "NOVEL-LIKE MOTION PROMPT WITH AUDIO DESCRIPTION",
            "clip": ["1", 1]
        }
    },
    # Negative prompt
    "5": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
            "clip": ["1", 1]
        }
    },
    # LTX conditioning with frame rate
    "6": {
        "class_type": "LTXVConditioning",
        "inputs": {
            "positive": ["4", 0],
            "negative": ["5", 0],
            "frame_rate": 25
        }
    },
    # Empty video latent
    "7": {
        "class_type": "EmptyLTXVLatentVideo",
        "inputs": {
            "width": 768,     # Half of final output (gets 2x upscaled)
            "height": 512,
            "length": 121,    # 4.84s at 25fps — adjust per scene
            "batch_size": 1
        }
    },
    # Empty audio latent
    "8": {
        "class_type": "LTXVEmptyLatentAudio",
        "inputs": {
            "length": 121     # Match video length
        }
    },
    # Combine video + audio latents
    "9": {
        "class_type": "LTXVConcatAVLatent",
        "inputs": {
            "a": ["7", 0],    # video latent
            "b": ["8", 0]     # audio latent
        }
    },
    # Insert reference image as first frame
    "10": {
        "class_type": "LTXVImgToVideo",
        "inputs": {
            "positive": ["6", 0],
            "negative": ["6", 1],
            "vae": ["1", 2],
            "image": ["3", 0],    # preprocessed image
            "width": 768,
            "height": 512,
            "length": 121,
            "batch_size": 1
        }
    },
    # LTX scheduler
    "11": {
        "class_type": "LTXVScheduler",
        "inputs": {
            "steps": 20,
            "max_shift": 2.05,
            "base_shift": 0.95,
            "stretch": True,
            "terminal": 0.1,
            "latent": ["10", 0]
        }
    },
    # Noise
    "12": {
        "class_type": "RandomNoise",
        "inputs": {"noise_seed": RANDOM_SEED}
    },
    # Guider
    "13": {
        "class_type": "CFGGuider",
        "inputs": {
            "model": ["1", 0],
            "positive": ["6", 0],
            "negative": ["6", 1],
            "cfg": 4.0
        }
    },
    # Sampler
    "14": {
        "class_type": "KSamplerSelect",
        "inputs": {"sampler_name": "euler"}
    },
    # Sample
    "15": {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
            "noise": ["12", 0],
            "guider": ["13", 0],
            "sampler": ["14", 0],
            "sigmas": ["11", 0],
            "latent_image": ["10", 0]
        }
    },
    # STAGE 2: HIRES.FIX — Spatial Upscale 2x (if upscaler model available)
    # Check: curl -s "$COMFY_URL/object_info/LTXVLatentUpsampler"
    # "16": {
    #     "class_type": "LTXVLatentUpsampler",
    #     "inputs": {
    #         "upscale_model": "ltx-2-spatial-upscaler-x2-1.0.safetensors",
    #         "samples": ["15", 0]  # output from sampler
    #     }
    # },
    # STAGE 3: DECODE — Separate and decode video + audio
    "16": {
        "class_type": "LTXVSeparateAVLatent",
        "inputs": {"samples": ["15", 0]}
    },
    "17": {
        "class_type": "VAEDecode",
        "inputs": {
            "samples": ["16", 0],   # video latent
            "vae": ["1", 2]
        }
    },
    # Save video with audio
    "18": {
        "class_type": "SaveVideo",
        "inputs": {
            "filename_prefix": "scene_INDEX",
            "images": ["17", 0],
            "fps": 25
        }
    }
}
```

### Using Distilled LoRA for Speed (RECOMMENDED)
If `ltx-2-19b-distilled-lora-384.safetensors` is available:
- Add LoRA loader node after model load
- Change steps from 20 → 8
- Change CFG from 4.0 → 1.0
- Change scheduler to "Simple" (or keep LTXVScheduler but adjust)
- This produces FASTER generation with comparable quality

### Audio Decode (if LTXVAudioVAELoader + LTXVAudioVAEDecode available)
```python
# Add these nodes to also extract generated audio
"19": {
    "class_type": "LTXVAudioVAELoader",
    "inputs": {}
},
"20": {
    "class_type": "LTXVAudioVAEDecode",
    "inputs": {
        "samples": ["16", 1],  # audio latent from SeparateAVLatent
        "vae": ["19", 0]
    }
}
# The generated audio includes scene-appropriate sounds!
```

---

## SUBMITTING & POLLING WORKFLOWS

### Submit
```bash
PROMPT_ID=$(curl -s -X POST "$COMFY_URL/prompt" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": $WORKFLOW_JSON}" | python3 -c "import sys,json; print(json.load(sys.stdin)['prompt_id'])")
echo "Submitted: $PROMPT_ID"
```

### Poll for completion
```bash
while true; do
  STATUS=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if '$PROMPT_ID' in d:
  s = d['$PROMPT_ID'].get('status',{}).get('status_str','')
  outputs = d['$PROMPT_ID'].get('outputs', {})
  if s == 'error': print('ERROR')
  elif outputs: print('DONE')
  else: print('RUNNING')
else: print('WAITING')
")
  echo "Status: $STATUS"
  if [ "$STATUS" = "DONE" ] || [ "$STATUS" = "ERROR" ]; then break; fi
  sleep 3
done
```

### Download output
```bash
FILENAME=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)['$PROMPT_ID']['outputs']
for nid, out in d.items():
  for key in ['gifs','videos','images']:
    if key in out:
      for item in out[key]:
        fn = item.get('filename','')
        if fn.endswith('.mp4') or fn.endswith('.webm'):
          print(fn); exit()
")
curl -s "$COMFY_URL/view?filename=$FILENAME&type=output" --output public/scenes/scene-{i}-a.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 public/scenes/scene-{i}-a.mp4
```

---

## FILLING SCENE DURATION (CRITICAL)

Each LTX-2 clip is 4-10 seconds. TTS audio is 8-15 seconds per scene.

**Generate MULTIPLE clips per scene with DIFFERENT motion prompts:**

Example: 12-second scene about "wallet security"
```
Sub-clip A (0-5s):   LTX-2 image-to-video — "camera pushing into glowing vault, particles rising, dramatic reveal, electronic hum building"
Sub-clip B (5-9s):   LTX-2 image-to-video — "keys splitting into glowing fragments orbiting around center, camera slowly orbiting, crystalline chimes"  
Sub-clip C (9-12s):  LTX-2 image-to-video — "shield materializing with rippling energy, camera pulling back, triumphant orchestral swell"
```

**Rules:**
- NEVER loop a single clip
- NEVER use static images with Ken Burns as filler — generate MORE video clips
- Each sub-clip gets a DIFFERENT motion prompt (different camera angle, different action)
- Generate the reference image for each sub-clip from the image gen API with a different angle/moment
- Crossfade between sub-clips in Remotion (10-15 frames)
- Total sub-clip durations must >= audio duration

**File naming:**
```
public/scenes/
├── scene-0-a.mp4     ← first clip
├── scene-0-b.mp4     ← second clip  
├── scene-0-c.mp4     ← third clip (if needed)
├── scene-1-a.mp4
├── scene-1-b.mp4
└── ...
```

---

## VIDEO QUALITY TIPS

1. **Image-to-video >> Text-to-video** — Always provide a reference image
2. **LTXVPreprocess the image** — Intentionally degrades to look like video compression, preventing quality mismatch between input image and generated frames
3. **Use Hires.fix** — 2x spatial upscale with LTXVLatentUpsampler if available
4. **Distilled LoRA** — Use 8-step distilled for stable, fast results
5. **Longer prompts = better** — Describe like a novel, not keywords
6. **Include audio in prompt** — LTX-2 generates matching sound effects
7. **Frame count 121-161** — Best quality/speed balance on 32GB VRAM
8. **Width/height divisible by 32** — Required by model architecture
9. **Frame count = 8n+1** — Required (97, 105, 113, 121, 129, 137, 145, 153, 161, 169, ... 257)
10. **Motion LoRAs** — If video barely moves, a motion LoRA helps (check custom_nodes for IC-LoRA)