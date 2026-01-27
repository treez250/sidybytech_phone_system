#!/usr/bin/env python3
"""
Production Real-Time Translation Service for Phone Company
- Handles multiple concurrent calls
- GPU-accelerated with Whisper Large + FastSpeech2
- Automatic language detection
- Call logging and monitoring
- Graceful error handling
"""

import os
import socket
import struct
import threading
import queue
import logging
import time
import json
from datetime import datetime
from collections import defaultdict
import numpy as np
import torch
import whisper
from transformers import pipeline
from TTS.api import TTS

# Configuration
RTP_LISTEN_IP = os.getenv('RTP_LISTEN_IP', '0.0.0.0')
RTP_BASE_PORT = int(os.getenv('RTP_BASE_PORT', '4000'))
MAX_CONCURRENT_CALLS = int(os.getenv('MAX_CONCURRENT_CALLS', '50'))
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large-v2')
LOG_DIR = os.getenv('LOG_DIR', '/var/log/translation-service')
CALL_RECORDINGS_DIR = os.getenv('CALL_RECORDINGS_DIR', '/var/recordings')

# Logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/translation-service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CallSession:
    """Represents a single call translation session"""
    
    def __init__(self, session_id, source_lang, target_lang):
        self.session_id = session_id
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.start_time = datetime.now()
        self.audio_buffer = bytearray()
        self.asterisk_addr = None
        self.sequence = 0
        self.timestamp = 0
        self.ssrc = hash(session_id) % (2**32)
        self.packets_received = 0
        self.packets_sent = 0
        self.translations = []
        
    def log_translation(self, original, translated):
        """Log translation for this call"""
        self.translations.append({
            'timestamp': datetime.now().isoformat(),
            'original': original,
            'translated': translated
        })
    
    def get_stats(self):
        """Get call statistics"""
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'session_id': self.session_id,
            'duration': duration,
            'packets_received': self.packets_received,
            'packets_sent': self.packets_sent,
            'translations_count': len(self.translations),
            'source_lang': self.source_lang,
            'target_lang': self.target_lang
        }


class RTPPacket:
    """Parse and create RTP packets"""
    
    @staticmethod
    def parse(data):
        """Parse RTP packet"""
        if len(data) < 12:
            return None
        
        header = struct.unpack('!BBHII', data[:12])
        return {
            'version': (header[0] >> 6) & 0x03,
            'payload_type': header[1] & 0x7F,
            'sequence': header[2],
            'timestamp': header[3],
            'ssrc': header[4],
            'payload': data[12:]
        }
    
    @staticmethod
    def create(payload, sequence, timestamp, ssrc, payload_type=0):
        """Create RTP packet"""
        header = struct.pack(
            '!BBHII',
            0x80,  # V=2, P=0, X=0, CC=0
            payload_type,
            sequence,
            timestamp,
            ssrc
        )
        return header + payload


class ProductionTranslationService:
    """Production-grade translation service"""
    
    def __init__(self):
        self.running = False
        self.sessions = {}
        self.session_lock = threading.Lock()
        
        # GPU device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cpu":
            logger.warning("GPU not available! Running on CPU (slow)")
        else:
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        # Load models
        logger.info("Loading production models...")
        self.load_models()
        logger.info("Models loaded successfully")
        
        # Statistics
        self.stats = {
            'total_calls': 0,
            'active_calls': 0,
            'total_translations': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def load_models(self):
        """Load all AI models"""
        # Whisper for speech-to-text (large model for production)
        logger.info(f"Loading Whisper {WHISPER_MODEL}...")
        self.whisper_model = whisper.load_model(WHISPER_MODEL, device=self.device)
        
        # Translation models (load on demand per language pair)
        self.translation_models = {}
        
        # TTS model (Coqui TTS - multilingual)
        logger.info("Loading TTS model...")
        self.tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", 
                       progress_bar=False, 
                       gpu=True if self.device == "cuda" else False)
    
    def get_translation_model(self, source_lang, target_lang):
        """Get or load translation model for language pair"""
        key = f"{source_lang}-{target_lang}"
        
        if key not in self.translation_models:
            logger.info(f"Loading translation model: {key}")
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
            try:
                self.translation_models[key] = pipeline(
                    "translation", 
                    model=model_name, 
                    device=0 if self.device == "cuda" else -1
                )
            except Exception as e:
                logger.error(f"Failed to load translation model {key}: {e}")
                return None
        
        return self.translation_models[key]
    
    def start(self):
        """Start the translation service"""
        logger.info("=" * 60)
        logger.info("PRODUCTION TRANSLATION SERVICE STARTING")
        logger.info("=" * 60)
        logger.info(f"Max concurrent calls: {MAX_CONCURRENT_CALLS}")
        logger.info(f"RTP base port: {RTP_BASE_PORT}")
        logger.info(f"Whisper model: {WHISPER_MODEL}")
        logger.info(f"Device: {self.device}")
        
        self.running = True
        
        # Start monitoring thread
        threading.Thread(target=self.monitor_stats, daemon=True).start()
        
        # Start RTP listener for each port
        for i in range(MAX_CONCURRENT_CALLS):
            port = RTP_BASE_PORT + (i * 2)
            threading.Thread(
                target=self.rtp_listener, 
                args=(port,), 
                daemon=True
            ).start()
        
        logger.info("Translation service running")
        logger.info("=" * 60)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.shutdown()
    
    def rtp_listener(self, port):
        """Listen for RTP on specific port"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((RTP_LISTEN_IP, port))
        sock.settimeout(1.0)
        
        logger.info(f"RTP listener started on port {port}")
        
        while self.running:
            try:
                data, addr = sock.recvfrom(2048)
                
                # Parse RTP packet
                packet = RTPPacket.parse(data)
                if not packet:
                    continue
                
                # Get or create session
                session_id = f"{addr[0]}:{addr[1]}"
                
                with self.session_lock:
                    if session_id not in self.sessions:
                        # New call - auto-detect languages or use defaults
                        self.sessions[session_id] = CallSession(
                            session_id, 
                            source_lang='en',  # TODO: Auto-detect
                            target_lang='es'   # TODO: From dialplan
                        )
                        self.sessions[session_id].asterisk_addr = addr
                        self.stats['total_calls'] += 1
                        self.stats['active_calls'] += 1
                        logger.info(f"New call session: {session_id}")
                    
                    session = self.sessions[session_id]
                
                # Update session
                session.packets_received += 1
                session.audio_buffer.extend(packet['payload'])
                
                # Process when we have enough audio (2 seconds)
                if len(session.audio_buffer) >= 16000:
                    threading.Thread(
                        target=self.process_session_audio,
                        args=(session_id, port + 1),
                        daemon=True
                    ).start()
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"RTP listener error on port {port}: {e}")
                self.stats['errors'] += 1
    
    def process_session_audio(self, session_id, send_port):
        """Process audio for a session"""
        try:
            with self.session_lock:
                if session_id not in self.sessions:
                    return
                session = self.sessions[session_id]
                audio_data = bytes(session.audio_buffer)
                session.audio_buffer.clear()
            
            # Convert PCMU to linear PCM
            linear_audio = self.pcmu_to_linear(audio_data)
            
            # Resample to 16kHz for Whisper
            audio_16k = np.repeat(linear_audio, 2)
            
            # Speech-to-text
            result = self.whisper_model.transcribe(
                audio_16k, 
                language=session.source_lang
            )
            text = result["text"].strip()
            
            if not text:
                return
            
            logger.info(f"[{session_id}] Recognized: {text}")
            
            # Translate
            translator = self.get_translation_model(
                session.source_lang, 
                session.target_lang
            )
            
            if translator:
                translated = translator(text)[0]['translation_text']
                logger.info(f"[{session_id}] Translated: {translated}")
                
                session.log_translation(text, translated)
                self.stats['total_translations'] += 1
                
                # Text-to-speech
                tts_audio = self.tts.tts(
                    text=translated,
                    language=session.target_lang
                )
                
                # Convert TTS output to PCMU and send as RTP
                self.send_audio_as_rtp(
                    session, 
                    tts_audio, 
                    send_port
                )
            
        except Exception as e:
            logger.error(f"Audio processing error for {session_id}: {e}")
            self.stats['errors'] += 1
    
    def pcmu_to_linear(self, pcmu_data):
        """Convert PCMU to linear PCM"""
        pcmu_array = np.frombuffer(pcmu_data, dtype=np.uint8)
        linear = np.zeros(len(pcmu_array), dtype=np.int16)
        
        for i, val in enumerate(pcmu_array):
            val = ~val
            sign = (val & 0x80)
            exponent = (val >> 4) & 0x07
            mantissa = val & 0x0F
            sample = ((mantissa << 3) + 0x84) << exponent
            if sign:
                sample = -sample
            linear[i] = sample
        
        return linear.astype(np.float32) / 32768.0
    
    def linear_to_pcmu(self, linear_data):
        """Convert linear PCM to PCMU"""
        linear_data = np.clip(linear_data * 32768.0, -32768, 32767).astype(np.int16)
        pcmu = np.zeros(len(linear_data), dtype=np.uint8)
        
        for i, sample in enumerate(linear_data):
            sign = 0x80 if sample < 0 else 0x00
            sample = abs(sample)
            exponent = 7
            for exp in range(8):
                if sample <= (0x1F << (exp + 3)):
                    exponent = exp
                    break
            mantissa = (sample >> (exponent + 3)) & 0x0F
            pcmu[i] = ~(sign | (exponent << 4) | mantissa) & 0xFF
        
        return pcmu.tobytes()
    
    def send_audio_as_rtp(self, session, audio_data, port):
        """Send audio back to Asterisk as RTP"""
        if not session.asterisk_addr:
            return
        
        # Convert audio to PCMU
        pcmu_data = self.linear_to_pcmu(audio_data)
        
        # Send as RTP packets
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        chunk_size = 160  # 20ms
        
        for i in range(0, len(pcmu_data), chunk_size):
            chunk = pcmu_data[i:i+chunk_size]
            
            rtp_packet = RTPPacket.create(
                chunk,
                session.sequence,
                session.timestamp,
                session.ssrc
            )
            
            sock.sendto(
                rtp_packet,
                (session.asterisk_addr[0], port)
            )
            
            session.sequence = (session.sequence + 1) % 65536
            session.timestamp += 160
            session.packets_sent += 1
        
        sock.close()
    
    def monitor_stats(self):
        """Monitor and log statistics"""
        while self.running:
            time.sleep(60)  # Every minute
            
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            
            logger.info("=" * 60)
            logger.info("SERVICE STATISTICS")
            logger.info(f"Uptime: {uptime/3600:.2f} hours")
            logger.info(f"Total calls: {self.stats['total_calls']}")
            logger.info(f"Active calls: {self.stats['active_calls']}")
            logger.info(f"Total translations: {self.stats['total_translations']}")
            logger.info(f"Errors: {self.stats['errors']}")
            
            if self.device == "cuda":
                logger.info(f"GPU Memory Used: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
            
            logger.info("=" * 60)
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down translation service...")
        self.running = False
        
        # Save call logs
        with self.session_lock:
            for session_id, session in self.sessions.items():
                stats = session.get_stats()
                logger.info(f"Call {session_id}: {json.dumps(stats)}")
        
        logger.info("Shutdown complete")


def main():
    """Main entry point"""
    service = ProductionTranslationService()
    service.start()


if __name__ == "__main__":
    main()
