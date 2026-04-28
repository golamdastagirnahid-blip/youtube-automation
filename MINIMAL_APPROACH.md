# YouTube Automation - Minimal Approach
# Date: 2026-04-28
# Repository: golamdastagirnahid-blip/youtube-automation

## Problem

The previous workflows were failing because:
1. Complex setup with many dependencies
2. Hardcoded paths that don't match the self-hosted runner
3. Complex imports that may fail in different environments
4. Encoding issues with special characters

## Solution

I've created a **minimal approach** that:
1. Uses only basic dependencies (yt-dlp, Pillow)
2. Auto-detects Python command (python, python3, py)
3. Auto-installs missing dependencies
4. Uses subprocess calls instead of complex imports
5. Has minimal setup steps

---

## New Files

### 1. `main_minimal.py`

A minimal main script that:
- Uses only basic dependencies
- Uses subprocess calls for yt-dlp and FFmpeg
- Has simple database management
- Has simple thumbnail generation
- Has placeholder for YouTube upload

### 2. `.github/workflows/automation-minimal.yml`

A minimal workflow that:
- Checks environment (Python, yt-dlp, FFmpeg, Pillow)
- Auto-installs missing dependencies
- Uses detected Python command
- Has minimal setup steps

---

## How It Works

### Environment Check

The workflow checks for:
1. Python (tries python, python3, py)
2. yt-dlp (installs if missing)
3. FFmpeg (warns if missing)
4. Pillow (installs if missing)

### Download

Uses yt-dlp with subprocess:
```python
cmd = ['yt-dlp', '-f', 'bestaudio', '-o', output_path, video_url]
subprocess.run(cmd)
```

### Processing

Uses FFmpeg with subprocess:
```python
cmd = ['ffmpeg', '-i', audio_file, '-c:a', 'aac', output]
subprocess.run(cmd)
```

### Upload

Currently a placeholder - needs OAuth2 authentication.

---

## How to Test

### Test 1: Run the Minimal Workflow

1. Go to GitHub Actions tab
2. Select "Video Upload (Minimal)" workflow
3. Click "Run workflow"
4. Enter the following:
   - video_id: `YXJC6YKaQXE`
   - video_url: `https://www.youtube.com/watch?v=YXJC6YKaQXE`
   - video_title: `Heavy Rain Deep Sleep`
5. Click "Run workflow"

### Test 2: Local Testing

```bash
# Set environment variables
export VIDEO_ID="YXJC6YKaQXE"
export VIDEO_URL="https://www.youtube.com/watch?v=YXJC6YKaQXE"
export VIDEO_TITLE="Heavy Rain Deep Sleep"

# Run the minimal script
python main_minimal.py run
```

---

## Expected Behavior

### Successful Run

1. ✅ Environment check passes
2. ✅ Dependencies installed (yt-dlp, Pillow)
3. ✅ Secrets validated
4. ✅ Credentials created
5. ✅ Database created/verified
6. ✅ Variables set
7. ✅ Test download passes
8. ✅ Download succeeds
9. ✅ Audio processing completes
10. ✅ Video creation completes
11. ✅ Upload placeholder runs
12. ✅ Database saved
13. ✅ Cleanup completes

---

## Why This Should Work

1. **Auto-detection**: Detects Python command automatically
2. **Auto-installation**: Installs missing dependencies
3. **Minimal dependencies**: Only requires yt-dlp and Pillow
4. **Subprocess calls**: Uses subprocess instead of complex imports
5. **Simple setup**: Minimal setup steps

---

## Commits Pushed

```
8f137d7 feat: add minimal workflow and main script
```

---

## Status

✅ **Minimal approach implemented and pushed**

**Commit:** 8f137d7
**Branch:** main
**Repository:** https://github.com/golamdastagirnahid-blip/youtube-automation

---

## Next Steps

1. **Test the minimal workflow** with the provided video
2. **Monitor the output** to see if it works
3. **Check if download succeeds**
4. **Check if video creation succeeds**
5. **Implement actual YouTube upload** if needed

---

## What Changed

### Before
- Complex setup with many dependencies
- Hardcoded paths
- Complex imports
- Many points of failure

### After
- Minimal setup with basic dependencies
- Auto-detection of Python command
- Auto-installation of missing dependencies
- Subprocess calls instead of complex imports
- Fewer points of failure

---

## Conclusion

The minimal approach should work even if the self-hosted runner environment is different. By auto-detecting the Python command and auto-installing missing dependencies, the workflow should be more robust.

**Please test with the minimal workflow and let me know the results!**
