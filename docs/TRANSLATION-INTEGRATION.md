# Translation Service Integration Guide

## Current Status

✅ **Translation Service Running** on 192.168.1.178:4000 (linux-gpu-01)
- Whisper (base model) loaded on GPU
- MarianMT (en→es) loaded on GPU  
- Listening for RTP audio on port 4000
- Processing and translating audio successfully
- ⚠️ TTS not implemented yet (echoes back original audio)

✅ **FreePBX Running** on 192.168.1.180 (gpu-trans-01)
- Version 15.0.38 with embedded database
- Asterisk 17 ready for ExternalMedia
- Bridge network mode (working)

## What You Need to Do

### Step 1: Add Translation Dialplan to FreePBX

The dialplan is already created in `config/asterisk/extensions_translation.conf`. You need to include it in FreePBX:

**Option A: Via FreePBX Web UI (Recommended)**
1. Log into FreePBX at http://192.168.1.180
2. Go to **Admin → Config Edit**
3. Open `/etc/asterisk/extensions_custom.conf`
4. Add this line at the top:
   ```
   #include extensions_translation.conf
   ```
5. Click **Save**
6. Go to **Admin → Asterisk CLI** and run:
   ```
   dialplan reload
   ```

**Option B: Via Docker Exec**
```bash
sudo docker exec -it pbx-freepbx bash
echo '#include extensions_translation.conf' >> /etc/asterisk/extensions_custom.conf
asterisk -rx "dialplan reload"
exit
```

### Step 2: Test the Translation Service

**Test 1: Translation Service Echo Test**
1. Create two extensions in FreePBX (100 and 101)
2. From extension 100, dial **8888**
3. You should hear "hello world" then your voice echoed back
4. Check translation service logs on linux-gpu-01:
   ```bash
   # On 192.168.1.178
   cd ~/sidybytech_phone_system/services
   source translation-venv/bin/activate
   python3 translation-service-gpu.py
   ```

**Test 2: Call with Translation**
1. From extension 100, dial **8101** (calls extension 101 with translation)
2. Speak in English
3. Extension 101 should hear Spanish (once TTS is added)
4. Currently: Extension 101 will hear your original audio echoed back

**Test 3: Direct Call (No Translation)**
1. From extension 100, dial **9101** (calls extension 101 directly)
2. This bypasses translation for comparison

### Step 3: Configure Extensions for Translation

For each extension that needs translation:

1. Go to **Applications → Extensions**
2. Edit the extension
3. Under **Advanced** tab:
   - Set **Codecs:** PCMU (ulaw) only
   - Set **Direct Media:** No
   - Set **RTP Symmetric:** Yes
4. Click **Submit** and **Apply Config**

### Step 4: Monitor Translation Service

On the GPU server (192.168.1.178):
```bash
cd ~/sidybytech_phone_system/services
source translation-venv/bin/activate
python3 translation-service-gpu.py
```

You should see:
```
2026-01-27 23:30:57 - INFO - Loading GPU models...
2026-01-27 23:30:57 - INFO - Using device: cuda
2026-01-27 23:30:59 - INFO - Models loaded successfully
2026-01-27 23:31:00 - INFO - RTP receiver started
2026-01-27 23:31:00 - INFO - Audio processor started
2026-01-27 23:31:00 - INFO - RTP sender started
```

When a call comes in:
```
2026-01-27 23:35:12 - INFO - Asterisk connected from ('192.168.1.180', 10000)
2026-01-27 23:35:14 - INFO - Recognized: Hello, how are you today?
2026-01-27 23:35:14 - INFO - Translated: Hola, ¿cómo estás hoy?
```

## Dialplan Reference

### Translation Prefix: 8XXX
- **8100** → Calls extension 100 with translation
- **8101** → Calls extension 101 with translation
- **8888** → Translation test (plays hello-world, echoes back)

### Direct Call Prefix: 9XXX
- **9100** → Calls extension 100 directly (no translation)
- **9101** → Calls extension 101 directly (no translation)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FreePBX (192.168.1.180)                                     │
│                                                              │
│  Extension 100 ──► Dial 8101 ──► ExternalMedia             │
│                                    │                         │
│                                    │ RTP Audio               │
│                                    ▼                         │
│                          Translation Service                 │
│                          (192.168.1.178:4000)               │
│                                    │                         │
│                                    │ Translated RTP          │
│                                    ▼                         │
│  Extension 101 ◄────────────────────                        │
└─────────────────────────────────────────────────────────────┘
```

## What's Missing (Next Steps)

### 1. Add TTS (Text-to-Speech)
Currently the service echoes back original audio. Need to add:
- Coqui TTS or similar
- Convert translated text to speech
- Send synthesized audio back as RTP

### 2. Bidirectional Translation
Current flow is one-way. For full conversation:
- Need to handle both directions (A→B and B→A)
- Separate translation contexts per direction
- Language detection or configuration

### 3. Production Hardening
- Multiple concurrent calls (currently single-threaded)
- Error handling and recovery
- Call logging and monitoring
- Systemd service for auto-start
- Resource limits and scaling

### 4. Language Pair Configuration
- Currently hardcoded to en→es
- Add configuration per extension or trunk
- Support multiple language pairs
- Auto-detection of source language

## Troubleshooting

### Translation service not receiving audio
1. Check FreePBX can reach 192.168.1.178:
   ```bash
   sudo docker exec pbx-freepbx ping 192.168.1.178
   ```
2. Check firewall on linux-gpu-01:
   ```bash
   sudo ufw status
   sudo ufw allow 4000/udp
   sudo ufw allow 4001/udp
   ```

### ExternalMedia not working
1. Verify Asterisk version supports ExternalMedia (17+)
2. Check dialplan loaded:
   ```bash
   sudo docker exec pbx-freepbx asterisk -rx "dialplan show translation-context"
   ```

### GPU not being used
1. Check CUDA available:
   ```bash
   nvidia-smi
   ```
2. Verify PyTorch sees GPU:
   ```bash
   python3 -c "import torch; print(torch.cuda.is_available())"
   ```

### Audio quality issues
1. Ensure PCMU codec only (no transcoding)
2. Check RTP packet loss
3. Verify network latency between servers

## Files Modified

- `config/asterisk/extensions_translation.conf` - Translation dialplan
- `services/translation-service-gpu.py` - GPU translation service
- `services/requirements-production.txt` - Python dependencies

## Trunk Configuration

**You DO NOT need to modify your trunk** for this to work. The translation happens at the dialplan level using ExternalMedia, not at the trunk level. Your existing trunk configuration is fine.

The dialplan intercepts calls with the 8XXX prefix and routes them through the translation service before connecting to the destination extension.
