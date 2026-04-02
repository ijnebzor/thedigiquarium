#!/usr/bin/env python3
"""
Generate audio archives for congregation transcripts using Kokoro TTS.
Produces individual MP3 files per speaker entry + a manifest.

Usage:
    python3 scripts/generate_voice_archive.py logs/congregations/congregation_XXXX.json
    
Requires Kokoro TTS running on port 8880.
"""
import sys, json, os, urllib.request
from pathlib import Path
from datetime import datetime

KOKORO_URL = "http://127.0.0.1:8880/v1/audio/speech"
VOICES = {
    'Adam': 'af_heart', 'Eve': 'af_star', 'Seeker': 'af_heart',
    'Abel': 'am_puck', 'Victor': 'am_puck', 'Observer': 'am_fenrir',
    'Cain': 'am_fenrir', 'Moderator': 'am_fenrir',
    'Gandhi': 'am_fenrir', 'Einstein': 'am_puck', 'Ada': 'af_star',
}

def generate_audio(text, voice, output_path):
    data = json.dumps({"model": "kokoro", "input": text[:500], "voice": voice}).encode()
    req = urllib.request.Request(KOKORO_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        Path(output_path).write_bytes(r.read())

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_voice_archive.py <congregation_json>")
        sys.exit(1)
    
    transcript_path = Path(sys.argv[1])
    data = json.loads(transcript_path.read_text())
    
    output_dir = transcript_path.parent / f"audio_{transcript_path.stem}"
    output_dir.mkdir(exist_ok=True)
    
    manifest = {"source": str(transcript_path), "generated": datetime.now().isoformat(), "files": []}
    
    entries = [e for e in data.get('transcript', []) if e.get('speaker') != 'Moderator']
    print(f"Generating audio for {len(entries)} entries...")
    
    for i, entry in enumerate(entries):
        speaker = entry['speaker']
        voice = VOICES.get(speaker, 'af_heart')
        filename = f"{i+1:02d}_{speaker.lower()}_r{entry.get('round', 0)}.mp3"
        filepath = output_dir / filename
        
        try:
            generate_audio(entry['text'], voice, filepath)
            manifest["files"].append({"file": filename, "speaker": speaker, "round": entry.get('round'), "chars": len(entry['text'])})
            print(f"  [{i+1}/{len(entries)}] {speaker} R{entry.get('round','?')}: {filename} ({filepath.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [{i+1}/{len(entries)}] {speaker}: FAILED ({e})")
    
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nArchive: {output_dir} ({len(manifest['files'])} files)")

if __name__ == '__main__':
    main()
