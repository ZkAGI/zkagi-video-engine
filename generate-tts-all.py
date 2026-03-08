import requests, os, sys, concurrent.futures

TTS_URL = "https://avatar.zkagi.ai/v1/clone-tts"
AUDIO_DIR = "/home/aten/zkagi-video-engine/public/audio"
VOICES_DIR = "/home/aten/zkagi-video-engine/voices"
os.makedirs(AUDIO_DIR, exist_ok=True)

SCENES = [
    {"idx": 0, "voice": "paw", "text": "Meet Raj. Raj runs a two million dollar company. Headcount? Zero. His entire staff fits inside a laptop."},
    {"idx": 1, "voice": "paw", "text": "HR? An AI agent. Marketing? Zynapse generates his ads, images, even videos. His finance department is a DeFi trading bot that never sleeps."},
    {"idx": 2, "voice": "pad", "text": "The only water cooler talk in Raj's office is with a chatbot. Honestly? Better advice than his last three employees combined."},
    {"idx": 3, "voice": "pad", "text": "ZkAGI's APIs handle everything. Image gen. Video production. On-chain trading. All running twenty four seven while Raj hits the beach."},
    {"idx": 4, "voice": "paw", "text": "My best employee never asks for a raise. Because it's an API. zkagi dot ai."},
]

VOICE_CFG = {
    "paw": {
        "ref_audio": os.path.join(VOICES_DIR, "paw.wav"),
        "ref_text": "ZM folks, here is your July 24th 2025 crypto update. Bitcoin is trading around 118520 US dollars.",
        "cfg_value": "2.0",
        "steps": "15",
    },
    "pad": {
        "ref_audio": os.path.join(VOICES_DIR, "pad.wav"),
        "ref_text": "Today, software handles our money, our health, our work.",
        "cfg_value": "2.0",
        "steps": "15",
    },
}

def generate_tts(scene):
    idx = scene["idx"]
    voice = VOICE_CFG[scene["voice"]]
    out_path = os.path.join(AUDIO_DIR, f"scene-{idx}.wav")
    
    with open(voice["ref_audio"], "rb") as f:
        files = {"ref_audio": ("ref.wav", f, "audio/wav")}
        data = {
            "ref_text": voice["ref_text"],
            "text": scene["text"],
            "cfg_value": voice["cfg_value"],
            "steps": voice["steps"],
        }
        resp = requests.post(TTS_URL, files=files, data=data, timeout=60)
    
    if resp.status_code == 200 and len(resp.content) > 1000:
        with open(out_path, "wb") as f:
            f.write(resp.content)
        # Get duration
        import wave
        with wave.open(out_path, "rb") as w:
            dur = w.getnframes() / w.getframerate()
        print(f"  Scene {idx}: {dur:.2f}s ({len(resp.content)} bytes)")
        return idx, dur
    else:
        print(f"  Scene {idx}: FAILED ({resp.status_code}, {len(resp.content)} bytes)")
        return idx, None

print("Generating TTS audio for all scenes...")
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(generate_tts, s): s for s in SCENES}
    results = {}
    for future in concurrent.futures.as_completed(futures):
        idx, dur = future.result()
        results[idx] = dur

print("\n=== TTS Results ===")
for idx in sorted(results.keys()):
    print(f"Scene {idx}: {results[idx]}s" if results[idx] else f"Scene {idx}: FAILED")
