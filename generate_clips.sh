#!/bin/bash
# LTX-2 Video Generation Script — 12 clips for PawPad video
# Uses distilled LoRA (8 steps) for speed

COMFY_URL="http://$(ip route show default | awk '{print $3}'):8001"
echo "ComfyUI URL: $COMFY_URL"

# Image names as uploaded to ComfyUI
declare -A IMAGES
IMAGES[0-a]="scene-0-a (1).png"
IMAGES[0-b]="scene-0-b.png"
IMAGES[0-c]="scene-0-c (1).png"
IMAGES[1-a]="scene-1-a (1).png"
IMAGES[1-b]="scene-1-b.png"
IMAGES[1-c]="scene-1-c (1).png"
IMAGES[2-a]="scene-2-a.png"
IMAGES[2-b]="scene-2-b.png"
IMAGES[2-c]="scene-2-c.png"
IMAGES[3-a]="scene-3-a.png"
IMAGES[3-b]="scene-3-b.png"
IMAGES[3-c]="scene-3-c.png"

# Motion prompts for each clip
declare -A PROMPTS
PROMPTS[0-a]="Camera slowly pushing into a messy open drawer overflowing with crumpled papers and napkins. A hand frantically rummaging through the contents, tossing papers aside. Warm lamplight creates dramatic shadows as loose papers flutter upward into the air. The atmosphere is chaotic and desperate. Rustling paper sounds with a frustrated sigh."
PROMPTS[0-b]="Close-up of a wrinkled coffee-stained napkin resting on a dark wooden table. The camera slowly orbits around it as the coffee stain appears to spread and darken across the paper surface. A dramatic spotlight from above creates long moody shadows. The sound of paper crinkling softly with a low dramatic hum."
PROMPTS[0-c]="A person in silhouette slowly bringing their hand to their face in a dramatic facepalm gesture. Red and orange light pulses rhythmically around them as the camera pulls back to reveal their defeated posture. Particles of warm light drift upward like embers. A deep dramatic sigh echoes through the space."
PROMPTS[1-a]="A single golden digital key slowly rotating in a dark void. The camera orbits smoothly around it as neon blue and purple particles drift past like snowflakes. The key glows but appears fragile, with tiny cracks of light pulsing along its surface. Ominous low electronic hum with subtle warning tones."
PROMPTS[1-b]="A golden digital key suddenly cracks down the center and shatters outward in spectacular slow motion. Bright orange sparks and fragments explode in all directions as the camera pushes toward the explosion. Red warning light flashes in the background. Dramatic glass shattering sound with heavy bass impact."
PROMPTS[1-c]="A coffee cup tipping over in extreme slow motion, brown liquid arcing gracefully through the air toward a glowing smartphone on a desk. Macro shot captures individual droplets suspended mid-air catching the warm office light. The splash of liquid meeting electronics with a dramatic gasp sound."
PROMPTS[2-a]="A golden key gracefully splitting into five glowing fragments that begin orbiting around a central point like planets around a sun. Bright blue energy beams connect each fragment. The camera slowly pulls back to reveal the full orbital pattern. Particles swirl around the formation. A crystalline chime with a rising electronic tone."
PROMPTS[2-b]="Three modern devices, a smartphone, laptop, and tablet, floating in dark space. Glowing teal energy beams shoot between them forming a protective triangle. A holographic shield materializes around the formation as the camera slowly orbits the setup. Teal energy pulses confidently. A gentle electronic hum building to a confident chord."
PROMPTS[2-c]="A hexagonal energy shield dome materializing from bottom to top around floating golden coins and digital assets. The shield surface ripples with protective energy as the camera pushes forward slowly. Teal and blue light reflects off every surface creating a fortress of light. Protective energy hum with a rising orchestral swell."
PROMPTS[3-a]="A hand lifting up a glowing smartphone with a vibrant purple wallet interface. The screen casts dramatic purple and gold light across the hand and surrounding dark space. The camera slowly pushes in toward the glowing screen. Golden sparkle particles radiate outward from the phone. A triumphant electronic fanfare plays."
PROMPTS[3-b]="Golden confetti and glowing particles rain down from above in beautiful slow motion. Purple and gold spotlights sweep dramatically across the scene. The camera tilts upward through the falling confetti as streamers curl through the air. Epic celebration atmosphere. Celebration horns and distant cheering crowd."
PROMPTS[3-c]="A glowing purple button floating in dark space, pulsing with intense energy. Energy waves radiate outward like ripples on water. Golden sparkles cascade around the button as the camera slowly pushes toward it with building intensity. A powerful bass pulse echoes followed by a rising energy whoosh."

# Clip order
CLIPS=("0-a" "0-b" "0-c" "1-a" "1-b" "1-c" "2-a" "2-b" "2-c" "3-a" "3-b" "3-c")

generate_clip() {
  local CLIP_ID=$1
  local IMAGE_NAME="${IMAGES[$CLIP_ID]}"
  local MOTION_PROMPT="${PROMPTS[$CLIP_ID]}"
  local SEED=$((RANDOM * RANDOM))
  local OUTPUT_PREFIX="scene_${CLIP_ID//-/_}"

  echo ""
  echo "================================================================"
  echo "  Generating clip: $CLIP_ID (image: $IMAGE_NAME)"
  echo "================================================================"

  # Build workflow JSON
  local WORKFLOW=$(cat <<WEOF
{
  "1": {
    "class_type": "LTXAVTextEncoderLoader",
    "inputs": {
      "text_encoder": "gemma_3_12B_it.safetensors",
      "ckpt_name": "ltx-2-19b-dev-fp8.safetensors",
      "device": "cpu"
    }
  },
  "2": {
    "class_type": "LoraLoaderModelOnly",
    "inputs": {
      "model": ["1", 0],
      "lora_name": "ltx-2-19b-distilled-lora-384.safetensors",
      "strength_model": 1.0
    }
  },
  "3": {
    "class_type": "LoadImage",
    "inputs": {"image": "$IMAGE_NAME"}
  },
  "4": {
    "class_type": "LTXVPreprocess",
    "inputs": {"image": ["3", 0]}
  },
  "5": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": $(python3 -c "import json; print(json.dumps('''$MOTION_PROMPT'''))"),
      "clip": ["1", 1]
    }
  },
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "static, frozen, no motion, blurry, low quality, distorted, text, watermark, jittery, flickering, ugly, deformed",
      "clip": ["1", 1]
    }
  },
  "7": {
    "class_type": "LTXVConditioning",
    "inputs": {
      "positive": ["5", 0],
      "negative": ["6", 0],
      "frame_rate": 25
    }
  },
  "8": {
    "class_type": "EmptyLTXVLatentVideo",
    "inputs": {
      "width": 768,
      "height": 512,
      "length": 97,
      "batch_size": 1
    }
  },
  "9": {
    "class_type": "LTXVImgToVideo",
    "inputs": {
      "positive": ["7", 0],
      "negative": ["7", 1],
      "vae": ["1", 2],
      "image": ["4", 0],
      "width": 768,
      "height": 512,
      "length": 97,
      "batch_size": 1
    }
  },
  "10": {
    "class_type": "LTXVScheduler",
    "inputs": {
      "steps": 8,
      "max_shift": 2.05,
      "base_shift": 0.95,
      "stretch": true,
      "terminal": 0.1,
      "latent": ["9", 0]
    }
  },
  "11": {
    "class_type": "RandomNoise",
    "inputs": {"noise_seed": $SEED}
  },
  "12": {
    "class_type": "CFGGuider",
    "inputs": {
      "model": ["2", 0],
      "positive": ["7", 0],
      "negative": ["7", 1],
      "cfg": 1.0
    }
  },
  "13": {
    "class_type": "KSamplerSelect",
    "inputs": {"sampler_name": "euler"}
  },
  "14": {
    "class_type": "SamplerCustomAdvanced",
    "inputs": {
      "noise": ["11", 0],
      "guider": ["12", 0],
      "sampler": ["13", 0],
      "sigmas": ["10", 0],
      "latent_image": ["9", 0]
    }
  },
  "15": {
    "class_type": "LTXVSeparateAVLatent",
    "inputs": {"samples": ["14", 0]}
  },
  "16": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["15", 0],
      "vae": ["1", 2]
    }
  },
  "17": {
    "class_type": "CreateVideo",
    "inputs": {
      "images": ["16", 0],
      "fps": 25
    }
  },
  "18": {
    "class_type": "SaveVideo",
    "inputs": {
      "video": ["17", 0],
      "filename_prefix": "$OUTPUT_PREFIX",
      "format": "mp4",
      "codec": "h264"
    }
  }
}
WEOF
)

  # Submit workflow
  local PROMPT_ID=$(curl -s -X POST "$COMFY_URL/prompt" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": $WORKFLOW}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prompt_id','ERROR: '+str(d)))")

  if [[ "$PROMPT_ID" == ERROR* ]]; then
    echo "FAILED to submit $CLIP_ID: $PROMPT_ID"
    return 1
  fi

  echo "Submitted $CLIP_ID: prompt_id=$PROMPT_ID"

  # Poll for completion
  local START_TIME=$(date +%s)
  while true; do
    local STATUS=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if '$PROMPT_ID' in d:
  s = d['$PROMPT_ID'].get('status',{}).get('status_str','')
  outputs = d['$PROMPT_ID'].get('outputs', {})
  if s == 'error':
    msgs = d['$PROMPT_ID'].get('status',{}).get('messages',[])
    print('ERROR: ' + str(msgs[-1]) if msgs else 'ERROR')
  elif outputs: print('DONE')
  else: print('RUNNING')
else: print('WAITING')
")
    local ELAPSED=$(($(date +%s) - START_TIME))

    if [[ "$STATUS" == DONE ]]; then
      echo "  Completed $CLIP_ID in ${ELAPSED}s"
      break
    elif [[ "$STATUS" == ERROR* ]]; then
      echo "  FAILED $CLIP_ID after ${ELAPSED}s: $STATUS"
      return 1
    fi

    if [ $ELAPSED -gt 300 ]; then
      echo "  TIMEOUT $CLIP_ID after ${ELAPSED}s"
      return 1
    fi

    sleep 5
  done

  # Download output
  local FILENAME=$(curl -s "$COMFY_URL/history/$PROMPT_ID" | python3 -c "
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

  if [ -z "$FILENAME" ]; then
    echo "  No video output found for $CLIP_ID!"
    return 1
  fi

  local OUTFILE="public/scenes/scene-${CLIP_ID}.mp4"
  curl -s "$COMFY_URL/view?filename=$FILENAME&type=output" --output "$OUTFILE"
  local DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUTFILE")
  local FSIZE=$(stat -c%s "$OUTFILE")
  echo "  Saved: $OUTFILE (${FSIZE}B, ${DUR}s)"
}

# Generate all clips
TOTAL=${#CLIPS[@]}
COUNT=0
FAILED=0

for CLIP_ID in "${CLIPS[@]}"; do
  COUNT=$((COUNT + 1))
  echo ""
  echo "[$COUNT/$TOTAL] Processing clip $CLIP_ID..."

  if generate_clip "$CLIP_ID"; then
    echo "  [OK] $CLIP_ID done"
  else
    echo "  [FAIL] $CLIP_ID failed"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "================================================================"
echo "  SUMMARY: $((TOTAL - FAILED))/$TOTAL clips generated"
echo "================================================================"

# List all generated clips
echo ""
echo "Generated video clips:"
for f in public/scenes/scene-*-*.mp4; do
  if [ -f "$f" ]; then
    DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
    SIZE=$(stat -c%s "$f")
    echo "  $f: ${SIZE}B, ${DUR}s"
  fi
done
