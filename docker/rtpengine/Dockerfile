FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install RTPEngine
RUN apt-get update && apt-get install -y \
    ngcp-rtpengine-daemon \
    ngcp-rtpengine-kernel-dkms \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Create config directory
RUN mkdir -p /etc/rtpengine

# Copy configuration
COPY rtpengine.conf /etc/rtpengine/

# Expose ports
EXPOSE 12222/udp 20000-30000/udp

CMD ["rtpengine", "--config-file=/etc/rtpengine/rtpengine.conf"]
