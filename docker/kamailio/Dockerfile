FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install Kamailio
RUN apt-get update && apt-get install -y \
    kamailio \
    kamailio-mysql-modules \
    kamailio-tls-modules \
    kamailio-websocket-modules \
    kamailio-json-modules \
    kamailio-utils-modules \
    mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /etc/kamailio /var/run/kamailio

# Copy configuration
COPY kamailio.cfg /etc/kamailio/
COPY kamctlrc /etc/kamailio/

# Expose ports
EXPOSE 5080/udp 5080/tcp

# Start Kamailio
CMD ["kamailio", "-DD", "-E", "-f", "/etc/kamailio/kamailio.cfg"]
