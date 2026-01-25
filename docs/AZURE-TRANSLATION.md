# Real-Time Call Translation with Azure Speech Services

## THE CORRECT ARCHITECTURE (PRODUCTION-READY)

```
Caller A ─┐
          │
          ▼
     Asterisk (VM, no Docker)
          │
          ├─ RTP (raw audio) ──▶ Translation Service (Azure Speech)
          │                         - Speech → Text
          │                         - Translate
          │                         - Text → Speech
          │
          ◀─ RTP (translated audio)
          │
Caller B ─┘
```

**Key Principles:**
- Asterisk remains the media authority
- Azure is a media processor, not a call controller
- ExternalMedia() forks RTP without breaking the call
- No Docker in the media path
- Direct NIC, static IP, deterministic RTP

## WHY EXTERNALMEDIA() IS THE RIGHT TOOL

ExternalMedia():
- Forks RTP without breaking the call
- Supports bidirectional RTP
- Works with PCMU / PCMA / L16 cleanly
- Keeps SIP logic inside Asterisk
- Is stable and deterministic

This is how you do live translation properly.

## IMPLEMENTATION PHASES

### PHASE 1 — Foundation (Must Be Perfect)

FreePBX / Asterisk runs on a VM:
- ✅ No Docker
- ✅ Direct NIC
- ✅ Static IP
- ✅ Local audio works (Phone ↔ Phone)
- ✅ RTP visible in tcpdump
- ✅ PCMU or L16 codec confirmed

**If this isn't boringly perfect, you do not proceed.**

### PHASE 2 — Media Fork (ExternalMedia)

In your dialplan (custom context):

```
exten => _*88X.,1,NoOp(Start translated call)
  same => n,Set(TARGET_EXTEN=${EXTEN:3})
  same => n,Answer()
  same => n,ExternalMedia(
      rtp,
      127.0.0.1:4000,
      sdp,
      ulaw
  )
  same => n,Dial(PJSIP/${TARGET_EXTEN},30)
  same => n,Hangup()
```

This:
- Forks live RTP
- Sends it to your translation service (port 4000)
- Keeps the call alive

### PHASE 3 — Translation Service (Azure)

Your translation service does exactly this:

1. Receive RTP (PCMU or L16)
2. Decode audio
3. Send audio stream to Azure Speech SDK
4. Receive transcription
5. Translate text
6. Generate speech (TTS)
7. Encode back to RTP
8. Send RTP back to Asterisk

Azure already proved it works. You're just changing the input source from WAV to RTP.

### PHASE 4 — Media Injection

Asterisk receives translated RTP and:
- Replaces one leg's audio
- Or injects into a bridge
- Or plays as a whisper stream

This is controlled, predictable, and scalable.

## WHAT YOU WILL NOT DO

❌ AudioSocket as the main path
❌ AGI audio manipulation
❌ Conference-room hacks
❌ Docker in the media path
❌ Guessing codec behavior
❌ Letting Azure control SIP

## WHY THIS SCALES TO A REAL COMPANY

- RTP is deterministic
- Azure scales horizontally
- Asterisk remains the call brain
- You can add: recording, compliance, analytics, sentiment, QA playback
- All without rewriting the system

## CURRENT STATUS

Your system is already at **PHASE 1 COMPLETE**:
- ✅ FreePBX/Asterisk running on VM (192.168.1.105)
- ✅ Extensions 100 and 101 working
- ✅ Local audio confirmed (extension 100)
- ✅ RTP flowing correctly
- ✅ PCMU codec working

## IMPLEMENTATION GUIDE

### Step 1: Azure Setup

1. Go to Azure Portal (portal.azure.com)
2. Create "Speech Services" resource
3. Get your API key and region
4. Note them down - you'll need them

### Step 2: Install Translation Service

On your FreePBX server:

```bash
cd /root/sidybytech_phone_system

# Install Python dependencies
pip3 install --break-system-packages -r services/requirements-translation.txt

# Configure translation service
cp services/translation-service.env.example services/translation-service.env
nano services/translation-service.env
```

Fill in your Azure credentials:
```bash
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=eastus
SOURCE_LANGUAGE=en-US
TARGET_LANGUAGE=es-ES
```

### Step 3: Add Dialplan to Asterisk

```bash
# Copy translation dialplan to FreePBX
docker exec -it pbx-freepbx bash
cp /config/asterisk/extensions_translation.conf /etc/asterisk/
echo "#include extensions_translation.conf" >> /etc/asterisk/extensions_custom.conf
asterisk -rx "dialplan reload"
exit
```

### Step 4: Start Translation Service

```bash
cd /root/sidybytech_phone_system
source services/translation-service.env
python3 services/translation-service.py
```

You should see:
```
INFO - Starting Translation Service
INFO - Listening on 127.0.0.1:4000
INFO - Translation: en-US → es-ES
INFO - Translation Service running
```

### Step 5: Test It

1. From extension 100, dial `*88101`
2. This calls extension 101 with translation enabled
3. Speak in English - extension 101 hears Spanish
4. Extension 101 speaks Spanish - you hear English

### Step 6: Run as Service (Production)

Create systemd service:

```bash
cat > /etc/systemd/system/translation-service.service << 'EOF'
[Unit]
Description=Asterisk Translation Service
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/sidybytech_phone_system
EnvironmentFile=/root/sidybytech_phone_system/services/translation-service.env
ExecStart=/usr/bin/python3 /root/sidybytech_phone_system/services/translation-service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable translation-service
systemctl start translation-service
systemctl status translation-service
```

## COST ESTIMATE (Azure)

- Speech-to-Text: $1/hour
- Translation: Free (included)
- Text-to-Speech: $16/1M characters (~$1/hour of speech)

**Total: ~$2/hour of translated calls**

## THE PROFESSIONAL PATH

Asterisk ExternalMedia() + Azure Speech on a VM, with direct RTP.

That is the professional path.
That is the stable path.
That is the sellable path.
