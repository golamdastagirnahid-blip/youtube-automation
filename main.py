name: Video Upload

on:
  repository_dispatch:
    types: [new_video_detected]
  workflow_dispatch:
    inputs:
      video_id:
        description: 'YouTube Video ID'
        required: true
        default: ''
      video_url:
        description: 'YouTube Video URL'
        required: true
        default: ''
      video_title:
        description: 'Video Title'
        required: false
        default: 'Relaxing Video'
      video_privacy:
        description: 'Privacy (public/private/unlisted)'
        required: false
        default: 'public'

jobs:
  upload:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    permissions:
      contents: write

    steps:

      # ── Step 1: Checkout ────────────────────────
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          token:       ${{ secrets.GH_TOKEN }}
          clean:       true
          fetch-depth: 1
          ref:         main

      # ── Step 2: Show File Versions ───────────────
      - name: Show File Versions
        run: |
          echo "==============================="
          echo "=== main.py lines 80-95 ==="
          echo "==============================="
          sed -n '80,95p' main.py

          echo ""
          echo "==============================="
          echo "=== uploader.py lines 1-15 ==="
          echo "==============================="
          sed -n '1,15p' src/uploader.py

          echo ""
          echo "==============================="
          echo "=== Git log last 5 commits ==="
          echo "==============================="
          git log --oneline -5

      # ── Step 3: Setup Python ────────────────────
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # ── Step 4: Install FFmpeg ───────────────────
      - name: Install FFmpeg
        run: |
          sudo apt-get update -y
          sudo apt-get install -y ffmpeg
          echo "✅ FFmpeg: $(ffmpeg -version | head -1)"

      # ── Step 5: Install Dependencies ────────────
      - name: Install Dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -U yt-dlp
          echo "✅ yt-dlp: $(yt-dlp --version)"

      # ── Step 6: Restore Database ─────────────────
      - name: Restore Database
        uses: actions/cache@v4
        with:
          path: database.json
          key: db-v1
          restore-keys: db-v1

      # ── Step 7: Create Credentials ───────────────
      - name: Create Credentials
        run: |
          echo '${{ secrets.CLIENT_SECRETS }}' > client_secrets.json
          echo '${{ secrets.YOUTUBE_TOKEN }}'  > token.json
          printf '%s' '${{ secrets.COOKIES_TXT }}' > cookies.txt
          echo "✅ Credentials created"

      # ── Step 8: Verify Files ─────────────────────
      - name: Verify Files
        run: |
          echo "📁 Checking files..."
          if [ -f cookies.txt ]; then
            echo "✅ cookies.txt ($(wc -c < cookies.txt) bytes)"
          else
            echo "❌ cookies.txt missing"
          fi
          if [ -f client_secrets.json ]; then
            echo "✅ client_secrets.json found"
          else
            echo "❌ client_secrets.json missing"
          fi
          if [ -f token.json ]; then
            echo "✅ token.json found"
          else
            echo "❌ token.json missing"
          fi
          if [ -f database.json ]; then
            echo "✅ database.json found"
          else
            echo "⚠️ Creating database.json..."
            echo '{
              "uploaded_videos": [],
              "daily_counts": {},
              "statistics": {"total_uploads": 0},
              "queued": []
            }' > database.json
            echo "✅ database.json created"
          fi

      # ── Step 9: Set Variables ────────────────────
      - name: Set Variables
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            VIDEO_ID="${{ github.event.inputs.video_id }}"
            VIDEO_URL="${{ github.event.inputs.video_url }}"
            VIDEO_TITLE="${{ github.event.inputs.video_title }}"
            VIDEO_PRIVACY="${{ github.event.inputs.video_privacy }}"
          else
            VIDEO_ID="${{ github.event.client_payload.video_id }}"
            VIDEO_URL="${{ github.event.client_payload.video_url }}"
            VIDEO_TITLE="${{ github.event.client_payload.video_title }}"
            VIDEO_PRIVACY="${{ github.event.client_payload.video_privacy }}"
          fi

          [ -z "$VIDEO_PRIVACY" ] && VIDEO_PRIVACY="public"
          [ -z "$VIDEO_TITLE"   ] && VIDEO_TITLE="Relaxing Video"

          echo "VIDEO_ID=$VIDEO_ID"           >> $GITHUB_ENV
          echo "VIDEO_URL=$VIDEO_URL"         >> $GITHUB_ENV
          echo "VIDEO_TITLE=$VIDEO_TITLE"     >> $GITHUB_ENV
          echo "VIDEO_PRIVACY=$VIDEO_PRIVACY" >> $GITHUB_ENV

      # ── Step 10: Show Video Info ─────────────────
      - name: Show Video Info
        run: |
          echo "============================================"
          echo "🎬 Video Information"
          echo "   ID      : ${{ env.VIDEO_ID }}"
          echo "   URL     : ${{ env.VIDEO_URL }}"
          echo "   Title   : ${{ env.VIDEO_TITLE }}"
          echo "   Privacy : ${{ env.VIDEO_PRIVACY }}"
          echo "============================================"

      # ── Step 11: Check Disk Space ────────────────
      - name: Check Disk Space
        run: |
          echo "💾 Disk space:"
          df -h
          echo "📦 RAM:"
          free -h

      # ── Step 12: Force Verify Source Files ───────
      - name: Force Verify Source Files
        run: |
          echo "==============================="
          echo "=== src/uploader.py FULL ==="
          echo "==============================="
          cat src/uploader.py
          echo ""
          echo "==============================="
          echo "=== src/downloader.py line 1-10 ==="
          echo "==============================="
          sed -n '1,10p' src/downloader.py

      # ── Step 13: Run Automation ──────────────────
      - name: Run Automation
        run: python main.py run
        env:
          VIDEO_ID:           ${{ env.VIDEO_ID }}
          VIDEO_URL:          ${{ env.VIDEO_URL }}
          VIDEO_TITLE:        ${{ env.VIDEO_TITLE }}
          VIDEO_PRIVACY:      ${{ env.VIDEO_PRIVACY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}

      # ── Step 14: Save Database ───────────────────
      - name: Save Database
        if: always()
        run: |
          git config user.name  "automation-bot"
          git config user.email "bot@github.com"
          git add database.json || true
          git diff --staged --quiet || \
            git commit -m "Update DB [skip ci]"
          git push || true

      # ── Step 15: Cleanup ─────────────────────────
      - name: Cleanup
        if: always()
        run: |
          echo "🧹 Cleaning up..."
          rm -rf downloads/  || true
          rm -rf processed/  || true
          rm -rf thumbnails/ || true
          rm -f  cookies.txt || true
          rm -f  token.json  || true
          rm -f  client_secrets.json || true
          echo "✅ Cleanup done"
