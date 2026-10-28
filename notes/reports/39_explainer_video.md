# Report 39 — 5-minute explainer video

1. **Goal:** "Make the video … use the docs … 5 min only and proper."
2. **What was built:**
   - `brag-output/brag.mp4` — the 5:00 video (1920×1080, 30 fps, captions + music).
   - `brag-output/brag.jpg` — poster (title card), baked as frame 0.
   - `brag-output/share-copy.txt` — 2-sentence post text.
   - `brag-output/brag-plan.md` — plan and storyboard.
   - `brag-output/work/render.py` — frame renderer, soundtrack generator, segment encoder and mux.
   - `environment.yml` — `imageio-ffmpeg==0.5.1`; `.gitignore` — `brag-output*/`.
3. **How verified:**
   - Stills of all 22 scenes + a mid-transition frame inspected; 6 layout issues fixed.
   - ffmpeg probe: duration 00:05:00.00, 9000 frames, H.264 + AAC; volumedetect mean −21.2 dB, max −7.0 dB.
   - Frames at 0 s and 160 s extracted from the final file and checked.
4. **Results:** 19.3 MB file; render ~2 min on 10 workers.
5. **Acceptance:** 5 minutes — PASSED; built from the script document — PASSED (timings and captions parsed from `writeup/video_script.md`); real figures, quotes and code — PASSED; no overlaps in checked stills — PASSED; voiceover — NOT DONE (captions instead, by design).
6. **Deviations:** no spoken narration (no TTS used); the script's voiceover appears as captions.
7. **Open:** record a human voiceover; the per-pair bars in scene 15 are an illustration (labelled).
8. **Next task:** voiceover recording, or a 20-second teaser cut.
9. **Commit:** Commit: feat: add the 5-minute explainer video renderer and its plan
