#!/usr/bin/env python3
"""
GPU-Based Real-Time Translation Service for Asterisk
Receives RTP from Asterisk, translates using local GPU models, sends back RTP
"""

import os
import socket
import struct
import threading
import queue
import logging
import numpy as np
import torch
from transformers import pipeline
import whisper

# Configuration
RTP_LISTEN_IP = os.getenv('RTP_LISTEN_IP', '0.0.0.0')
RTP_LISTEN_PORT = int(os.getenv('RTP_LISTEN_PORT', '4000'))
RTP_SEND_PORT = int(os.getenv('RTP_SEND_PORT', '4001'))
SOURCE_LANGUAGE = os.getenv('SOURCE_LANGUAGE', 'en')
TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'es')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RTPPacket:
    """Parse and create RTP packets"""
    
    def __init__(self, data=None):
        if data:
            self.parse(data)
    
    def parse(self, data):
        """Parse RTP packet"""
        if len(data) < 12:
            raise ValueError("RTP packet too short")
        
        header = struct.unpack('!BBHII', data[:12])
        self.version = (header[0] >> 6) & 0x03
        self.padding = (header[0] >> 5) & 0x01
        self.extension = (header[0] >> 4) & 0x01
        self.csrc_count = header[0] & 0x0F
        self.marker = (header[1] >> 7) & 0x01
        self.payload_type = header[1] & 0x7F
        self.sequence = header[2]
        self.timestamp = header[3]
        self.ssrc = header[4]
        self.payload = data[12:]
    
    @staticmethod
    def create(payload, sequence, timestamp, ssrc=12345, payload_type=0):
        """Create RTP packet"""
        header = struct.pack(
            '!BBHII',
            0x80,
            payload_type,
            sequence,
            timestamp,
            ssrc
        )
        return header + payload


class GPUTranslationService:
    """GPU-based real-time translation service"""
    
    def __init__(self):
        self.running = False
        self.audio_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        
        # RTP state
        self.sequence = 0
        self.timestamp = 0
        self.ssrc = 12345
        
        # Sockets
        self.listen_socket = None
        self.send_socket = None
        self.asterisk_addr = None
        
        # Load models
        logger.info("Loading GPU models...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Whisper for speech-to-text
        self.whisper_model = whisper.load_model("base", device=device)
        
        # Translation model - use MarianMT directly
        from transformers import MarianMTModel, MarianTokenizer
        model_name = f"Helsinki-NLP/opus-mt-{SOURCE_LANGUAGE}-{TARGET_LANGUAGE}"
        logger.info(f"Loading translation model: {model_name}")
        self.translation_tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.translation_model = MarianMTModel.from_pretrained(model_name)
        if device == "cuda":
            self.translation_model = self.translation_model.to("cuda")
        
        # TTS - TODO: Add later
        self.tts = None
        
        logger.info("Models loaded successfully")
    
    def start(self):
        """Start the translation service"""
        logger.info("Starting GPU Translation Service")
        logger.info(f"Listening on {RTP_LISTEN_IP}:{RTP_LISTEN_PORT}")
        logger.info(f"Translation: {SOURCE_LANGUAGE} → {TARGET_LANGUAGE}")
        
        self.running = True
        
        # Create sockets
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind((RTP_LISTEN_IP, RTP_LISTEN_PORT))
        
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Start threads
        threading.Thread(target=self.receive_rtp, daemon=True).start()
        threading.Thread(target=self.process_audio, daemon=True).start()
        threading.Thread(target=self.send_translated_rtp, daemon=True).start()
        
        logger.info("GPU Translation Service running")
        
        try:
            while self.running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False
    
    def receive_rtp(self):
        """Receive RTP packets from Asterisk"""
        logger.info("RTP receiver started")
        
        while self.running:
            try:
                data, addr = self.listen_socket.recvfrom(2048)
                
                if not self.asterisk_addr:
                    self.asterisk_addr = addr
                    logger.info(f"Asterisk connected from {addr}")
                
                try:
                    packet = RTPPacket(data)
                    self.audio_queue.put(packet.payload)
                except Exception as e:
                    logger.error(f"RTP parse error: {e}")
                
            except Exception as e:
                logger.error(f"RTP receive error: {e}")
    
    def pcmu_to_linear(self, pcmu_data):
        """Convert PCMU (G.711 μ-law) to linear PCM"""
        # μ-law decompression table
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
        """Convert linear PCM to PCMU (G.711 μ-law)"""
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
    
    def process_audio(self):
        """Process audio with GPU models"""
        logger.info("Audio processor started")
        
        audio_buffer = bytearray()
        
        while self.running:
            try:
                if not self.audio_queue.empty():
                    payload = self.audio_queue.get(timeout=0.1)
                    audio_buffer.extend(payload)
                    
                    # Process every 2 seconds of audio
                    if len(audio_buffer) >= 16000:  # 2 seconds at 8kHz
                        # Convert PCMU to linear PCM
                        linear_audio = self.pcmu_to_linear(bytes(audio_buffer))
                        
                        # Resample to 16kHz for Whisper
                        # Simple upsampling (proper resampling would use librosa)
                        audio_16k = np.repeat(linear_audio, 2)
                        
                        # Speech-to-text with Whisper
                        result = self.whisper_model.transcribe(audio_16k, language=SOURCE_LANGUAGE)
                        text = result["text"]
                        logger.info(f"Recognized: {text}")
                        
                        if text.strip():
                            # Translate using model directly
                            inputs = self.translation_tokenizer(text, return_tensors="pt", padding=True)
                            device = "cuda" if torch.cuda.is_available() else "cpu"
                            if device == "cuda":
                                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                            
                            translated_ids = self.translation_model.generate(**inputs)
                            translated = self.translation_tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]
                            logger.info(f"Translated: {translated}")
                            
                            # Text-to-speech
                            # For now, echo back original audio (TTS integration needed)
                            # TODO: Implement proper TTS
                            self.translation_queue.put(bytes(audio_buffer))
                        
                        audio_buffer.clear()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Audio processing error: {e}")
    
    def send_translated_rtp(self):
        """Send translated audio back to Asterisk as RTP"""
        logger.info("RTP sender started")
        
        while self.running:
            try:
                if not self.translation_queue.empty() and self.asterisk_addr:
                    audio_data = self.translation_queue.get(timeout=0.1)
                    
                    # Split into RTP packets (160 bytes = 20ms)
                    chunk_size = 160
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i+chunk_size]
                        
                        rtp_packet = RTPPacket.create(
                            chunk,
                            self.sequence,
                            self.timestamp,
                            self.ssrc,
                            payload_type=0
                        )
                        
                        self.send_socket.sendto(
                            rtp_packet,
                            (self.asterisk_addr[0], RTP_SEND_PORT)
                        )
                        
                        self.sequence = (self.sequence + 1) % 65536
                        self.timestamp += 160
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"RTP send error: {e}")


def main():
    """Main entry point"""
    logger.info("=== GPU-Based Real-Time Translation Service ===")
    
    service = GPUTranslationService()
    service.start()


if __name__ == "__main__":
    main()
