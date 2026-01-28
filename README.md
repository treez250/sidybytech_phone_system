# Real-Time Translation Phone System

A production-ready VoIP platform with GPU-accelerated real-time translation built on FreePBX and Asterisk.

## Features

- **Real-Time Translation** - GPU-powered speech translation during live calls
- **Multi-Language Support** - English ↔ Spanish (more languages coming)
- **GPU Acceleration** - NVIDIA RTX 5080 for fast processing
- **Production Ready** - FreePBX 15 + Asterisk 17 on Docker
- SIP trunk management and call routing
- CDR (Call Detail Records) with billing integration
- Security hardening and fraud prevention
- Real-time monitoring with Prometheus + Grafana

## Architecture

**FreePBX Server** (192.168.1.180)
- FreePBX 15.0.38 (web management)
- Asterisk 17 (PBX engine with ExternalMedia support)
- MariaDB (embedded database)
- Redis (caching)
- Prometheus + Grafana (monitoring)

**Translation Server** (192.168.1.178)
- NVIDIA RTX 5080 GPU (16GB VRAM)
- Whisper (speech-to-text)
- MarianMT (neural translation)
- RTP audio processing
- Python 3.12 + PyTorch + CUDA 13.0

## Quick Start

### 1. Start FreePBX (on 192.168.1.180)
```bash
cd ~/sidybytech_phone_system
sudo docker-compose up -d
```

### 2. Start Translation Service (on 192.168.1.178)
```bash
cd ~/sidybytech_phone_system
./scripts/start-translation-service.sh
```

### 3. Configure FreePBX
See `docs/FREEPBX-TRANSLATION-SETUP.md` for step-by-step setup.

### 4. Test Translation
- Dial **8888** for echo test
- Dial **8XXX** to call extension XXX with translation
- Dial **9XXX** to call extension XXX directly (no translation)

## Documentation

- **[Quick Start](docs/FREEPBX-TRANSLATION-SETUP.md)** - Get translation working in 20 minutes
- **[Translation Integration](docs/TRANSLATION-INTEGRATION.md)** - Full technical details
- **[Current State](docs/CURRENT-STATE.md)** - System status and configuration
- **[Installation](docs/INSTALLATION.md)** - Full installation guide
- **[Incident Reports](docs/INCIDENT-REPORTS.md)** - What we learned the hard way
- **[Security](docs/SECURITY.md)** - Security hardening guide

## How Translation Works

```
Extension 100 → Dial 8101 → FreePBX ExternalMedia
                                ↓
                    Translation Service (GPU)
                    - Whisper: Speech → Text
                    - MarianMT: English → Spanish
                    - TTS: Text → Speech (coming soon)
                                ↓
Extension 101 ← Translated Audio ←
```

## Current Status

✅ FreePBX running with embedded database
✅ GPU translation service operational
✅ Whisper + MarianMT models loaded
✅ RTP audio processing working
⏳ TTS integration (next step)
⏳ Bidirectional translation
⏳ Multiple concurrent calls

## Configuration

## Security

- Change all default passwords in `.env`
- Configure firewall rules
- Enable fail2ban
- Set up SSL certificates
- Review security hardening checklist

## License

Proprietary - All rights reserved
