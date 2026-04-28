# YouTube Automation - Diagnostic Guide
# Date: 2026-04-28
# Repository: golamdastagirnahid-blip/youtube-automation

## What's New

I've created a **diagnostic workflow** that will help us identify exactly what's failing.

### New Files

1. **`.github/workflows/automation-diagnostic.yml`** - A diagnostic workflow that tests each component separately
2. **`test_download.py`** - A standalone test script for testing download methods

---

## How to Use the Diagnostic Workflow

### Step 1: Run the Diagnostic Workflow

1. Go to GitHub Actions tab
2. Select "Video Upload (Diagnostic)" workflow
3. Click "Run workflow"
4. Enter the following:
   - video_id: `YXJC6YKaQXE`
   - video_url: `https://www.youtube.com/watch?v=YXJC6YKaQXE`
   - video_title: `Heavy Rain Deep Sleep`
5. Click "Run workflow"

### Step 2: Review the Output

The diagnostic workflow will test each component separately:

1. **Environment Diagnostic** - Checks Python, FFmpeg, Node.js, pip, and installed packages
2. **Install/Upgrade Dependencies** - Installs or upgrades all required packages
3. **yt-dlp Diagnostic** - Tests yt-dlp import and info extraction
4. **pytube Diagnostic** - Tests pytube import and info extraction
5. **Validate Secrets** - Checks that all required secrets are set
6. **Test Download (Detailed)** - Tests each download method separately with detailed output
7. **Run Automation** - Runs the actual automation

### Step 3: Identify the Failure

Look at the output to see which step is failing:

- If **Environment Diagnostic** fails → Python or FFmpeg not installed
- If **Install/Upgrade Dependencies** fails → Package installation issue
- If **yt-dlp Diagnostic** fails → yt-dlp not working
- If **pytube Diagnostic** fails → pytube not working
- If **Validate Secrets** fails → Missing secrets
- If **Test Download** fails → Download method not working
- If **Run Automation** fails → Full automation issue

---

## Common Issues and Solutions

### Issue 1: Python Not Found

**Error:** `ERROR: Python not found`

**Solution:**
- Install Python on the self-hosted runner
- Add Python to PATH
- Restart the runner

### Issue 2: FFmpeg Not Found

**Error:** `WARNING: FFmpeg not found`

**Solution:**
- Install FFmpeg on the self-hosted runner
- Add FFmpeg to PATH
- Restart the runner

### Issue 3: yt-dlp Not Working

**Error:** `✗ yt-dlp info extraction failed`

**Solution:**
- Update yt-dlp: `python -m pip install --upgrade yt-dlp`
- Check network connectivity
- Try a different video URL
- Use cookies (add COOKIES_TXT secret)

### Issue 4: pytube Not Working

**Error:** `✗ pytube info extraction failed`

**Solution:**
- Update pytube: `python -m pip install --upgrade pytube`
- Check network connectivity
- Try a different video URL

### Issue 5: Secrets Not Set

**Error:** `ERROR: CLIENT_SECRETS secret not set`

**Solution:**
- Go to repository Settings → Secrets and variables → Actions
- Add the missing secret:
  - `CLIENT_SECRETS` - Google OAuth client secrets
  - `YOUTUBE_TOKEN` - YouTube OAuth token

### Issue 6: Download Fails

**Error:** `✗ yt-dlp download test failed`

**Solution:**
- Check network connectivity
- Try a different video URL
- Use cookies (add COOKIES_TXT secret)
- Try pytube or youtube-dl as fallback

---

## Local Testing

You can also test locally using the test script:

```bash
# Set environment variables
export VIDEO_ID="YXJC6YKaQXE"
export VIDEO_URL="https://www.youtube.com/watch?v=YXJC6YKaQXE"

# Run the test script
python test_download.py
```

This will test:
- Python installation
- FFmpeg installation
- yt-dlp installation
- pytube installation
- youtube-dl installation
- yt-dlp info extraction
- pytube info extraction
- yt-dlp download

---

## Expected Output

### Successful Run

```
=== ENVIRONMENT DIAGNOSTIC ===

--- Python ---
Python found: C:\Python312\python.exe
Python 3.12.0

--- FFmpeg ---
FFmpeg found: C:\Python312\ffmpeg.exe
ffmpeg version 8.1-essentials_build-www.gyan.dev

--- Node.js ---
Node.js found: C:\nodejs\node.exe
v22.15.0

--- pip ---
pip 24.0

--- Installed Packages ---
yt-dlp               2026.3.17
pytube               15.0.0
youtube-dl           2024.5.27
google-api-python-client 2.194.0
requests             2.33.1

=== ENVIRONMENT DIAGNOSTIC COMPLETE ===

=== INSTALLING DEPENDENCIES ===

Upgrading pip...
Installing yt-dlp...
Installing pytube...
Installing youtube-dl...
Installing requirements.txt...

=== DEPENDENCIES INSTALLED ===

=== YT-DLP DIAGNOSTIC ===

Testing yt-dlp import...
yt-dlp imported successfully
Version: 2026.3.17

Testing yt-dlp with video...
Title: Heavy Rain Deep Sleep
Duration: 14400 seconds

=== YT-DLP DIAGNOSTIC COMPLETE ===

=== PYTUBE DIAGNOSTIC ===

Testing pytube import...
pytube imported successfully

Testing pytube with video...
Title: Heavy Rain Deep Sleep
Duration: 14400 seconds

=== PYTUBE DIAGNOSTIC COMPLETE ===

=== VALIDATING SECRETS ===

All secrets validated

=== DETAILED DOWNLOAD TEST ===

Video URL: https://www.youtube.com/watch?v=YXJC6YKaQXE
Video ID: YXJC6YKaQXE

--- Test 1: yt-dlp info extraction ---
✓ yt-dlp info extraction successful
Title: Heavy Rain Deep Sleep
Duration: 14400

--- Test 2: pytube info extraction ---
✓ pytube info extraction successful
Title: Heavy Rain Deep Sleep
Duration: 14400

--- Test 3: yt-dlp download test ---
✓ yt-dlp download test successful
Downloaded: 45.2 MB

=== DETAILED DOWNLOAD TEST COMPLETE ===

=== STARTING AUTOMATION ===

[Automation output...]

=== AUTOMATION COMPLETE ===
```

---

## Next Steps

1. **Run the diagnostic workflow** and review the output
2. **Identify which step is failing**
3. **Apply the appropriate solution** from the Common Issues section
4. **Re-run the diagnostic workflow** to verify the fix
5. **Run the full automation** once all diagnostics pass

---

## Status

✅ **Diagnostic workflow implemented and pushed**

**Commit:** 9a601d1
**Branch:** main
**Repository:** https://github.com/golamdastagirnahid-blip/youtube-automation

---

## What This Will Tell Us

The diagnostic workflow will tell us:

1. **Is Python installed and working?**
2. **Is FFmpeg installed and working?**
3. **Are all required packages installed?**
4. **Is yt-dlp working?**
5. **Is pytube working?**
6. **Are all secrets set?**
7. **Can we extract video info?**
8. **Can we download videos?**

Once we know exactly what's failing, we can fix it!

---

## Please Run the Diagnostic Workflow

**Go to GitHub Actions → "Video Upload (Diagnostic)" → "Run workflow"**

Then share the output with me so I can see exactly what's failing!
