# Report 41 — Male voiceover

1. **Goal:** add a spoken, male voiceover explaining the video.
2. **What was built:** `brag-output/work/voice.py` (Kokoro, voice am_michael); `render.py` mix step + voice-timed captions; tightened narration in `writeup/video_script.md`; re-rendered `brag-output/brag.mp4` and `assets/explainer_video.mp4`; `environment.yml` deps.
3. **How verified:** per-scene fit printout (all lines play in full, speed 1.00–1.15); ffprobe: 00:05:00.00, 9000 frames, H.264 + AAC; volumedetect mean −19.9 dB, max −0.6 dB; per-second loudness check at 60–80 s shows continuous speech; frame at 98 s shows the caption matching the spoken line; number audit on the script: 0 missing.
4. **Results:** 22 narrated scenes; 17 lines tightened; 18.99 MB video.
5. **Acceptance:** male voiceover — PASSED; 5 minutes — PASSED; no truncated speech — PASSED; captions in sync — PASSED (spot-checked).
6. **Deviations:** narration text shortened to fit 5:00 at a natural pace.
7. **Open:** human voiceover if preferred.
8. **Next task:** push and check the README video link.
9. **Commit:** Commit: feat: add a male voiceover to the explainer video
