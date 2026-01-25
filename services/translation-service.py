#!/usr/bin/env python3
"""
Real-Time Translation Service for Asterisk
Receives RTP from Asterisk ExternalMedia(), translates via Azure, sends back RTP
"""

import os
import socket
import struct
import threading
import queue
import logging
from datetime import datetime

# Azure Speech SDK
try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    print("ERROR: Azure Speech SDK not installed")
    print("Install with: pip3 install azure-cognitiveservices-speech")
    exit(1)

# Configuration
RTP_LISTEN_IP = os.getenv('RTP_LISTEN_IP', '127.0.0.1')
RTP_LISTEN_PORT = int(os.getenv('RTP_LISTEN_PORT', '4000'))
RTP_SEND_PORT = int(os.getenv('RTP_SEND_PORT', '4001'))

AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
SOURCE_LANGUAGE = os.getenv('SOURCE_LANGUAGE', 'en-US')
TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'es-ES')

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
        
        # RTP header (12 bytes minimum)
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
        
        # Payload starts after header
        self.payload = data[12:]
    
    @staticmethod
    def create(payload, sequence, timestamp, ssrc=12345, payload_type=0):
        """Create RTP packet"""
        # RTP header
        header = struct.pack(
            '!BBHII',
            0x80,  # V=2, P=0, X=0, CC=0
            payload_type,  # M=0, PT=0 (PCMU)
            sequence,
            timestamp,
            ssrc
        )
        return header + payload


class TranslationService:
    """Real-time translation service"""
    
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
        
        # Azure Speech Config
        if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
            logger.error("Azure credentials not set!")
            logger.error("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION")
            exit(1)
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )
        self.speech_config.speech_recognition_language = SOURCE_LANGUAGE
        self.speech_config.speech_synthesis_language = TARGET_LANGUAGE
    
    def start(self):
        """Start the translation service"""
        logger.info("Starting Translation Service")
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
        
        logger.info("Translation Service running")
        
        # Keep running
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
                
                # Store Asterisk address for sending back
                if not self.asterisk_addr:
                    self.asterisk_addr = addr
                    logger.info(f"Asterisk connected from {addr}")
                
                # Parse RTP packet
                try:
                    packet = RTPPacket(data)
                    
                    # Queue audio payload for processing
                    self.audio_queue.put(packet.payload)
                    
                except Exception as e:
                    logger.error(f"RTP parse error: {e}")
                
            except Exception as e:
                logger.error(f"RTP receive error: {e}")
    
    def process_audio(self):
        """Process audio with Azure Speech"""
        logger.info("Audio processor started")
        
        # This is a simplified version
        # In production, you'd use Azure's streaming recognition
        
        audio_buffer = bytearray()
        
        while self.running:
            try:
                # Get audio from queue
                if not self.audio_queue.empty():
                    payload = self.audio_queue.get(timeout=0.1)
                    audio_buffer.extend(payload)
                    
                    # Process when we have enough audio (e.g., 1 second)
                    # PCMU is 8000 samples/sec, 1 byte per sample
                    if len(audio_buffer) >= 8000:
                        # TODO: Send to Azure Speech-to-Text
                        # TODO: Translate text
                        # TODO: Convert to speech with TTS
                        # TODO: Queue translated audio
                        
                        # For now, just echo back (placeholder)
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
                    
                    # Split into RTP packets (160 bytes = 20ms of PCMU audio)
                    chunk_size = 160
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i+chunk_size]
                        
                        # Create RTP packet
                        rtp_packet = RTPPacket.create(
                            chunk,
                            self.sequence,
                            self.timestamp,
                            self.ssrc,
                            payload_type=0  # PCMU
                        )
                        
                        # Send to Asterisk
                        self.send_socket.sendto(
                            rtp_packet,
                            (self.asterisk_addr[0], RTP_SEND_PORT)
                        )
                        
                        # Update RTP state
                        self.sequence = (self.sequence + 1) % 65536
                        self.timestamp += 160
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"RTP send error: {e}")


def main():
    """Main entry point"""
    logger.info("=== Asterisk Real-Time Translation Service ===")
    
    service = TranslationService()
    service.start()


if __name__ == "__main__":
    main()
