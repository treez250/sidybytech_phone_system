#!/bin/bash
# FreePBX Bare Metal Installation on Debian 12
# This installs FreePBX directly on the system (no Docker)

set -e

echo "=== FreePBX Bare Metal Installation ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root"
    exit 1
fi

echo "⚠️  WARNING: This will install FreePBX directly on this system"
echo "⚠️  This is a clean installation - existing Docker containers will remain but won't be used"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "📦 Installing system dependencies..."
apt update
apt install -y \
    build-essential \
    linux-headers-$(uname -r) \
    openssh-server \
    apache2 \
    mariadb-server \
    mariadb-client \
    bison \
    flex \
    php \
    php-curl \
    php-cli \
    php-mysql \
    php-pdo \
    php-gd \
    php-mbstring \
    php-intl \
    php-bcmath \
    php-xml \
    php-zip \
    php-ldap \
    curl \
    wget \
    subversion \
    git \
    unixodbc \
    uuid \
    uuid-dev \
    libasound2-dev \
    libedit-dev \
    libjansson-dev \
    libsqlite3-dev \
    libssl-dev \
    libxml2-dev \
    sqlite3 \
    xmlstarlet \
    sox \
    libncurses5-dev \
    libspeex-dev \
    libspeexdsp-dev \
    libsrtp2-dev \
    libgsm1-dev \
    libogg-dev \
    libvorbis-dev \
    libopus-dev \
    libcurl4-openssl-dev \
    libical-dev \
    libneon27-dev \
    libiksemel-dev \
    libresample1-dev \
    libgmime-3.0-dev \
    libcorosync-common-dev \
    libcfg-dev \
    libpopt-dev \
    libsnmp-dev \
    libiksemel-dev \
    libcap-dev \
    libnewt-dev \
    libpq-dev \
    libradcli-dev \
    libreadline-dev \
    libsrtp2-dev \
    libtool-bin \
    libunbound-dev \
    libvpb-dev \
    portaudio19-dev \
    python3-dev \
    unixodbc-dev \
    uuid-dev

echo ""
echo "📦 Configuring MariaDB..."
systemctl start mariadb
systemctl enable mariadb

# Secure MariaDB installation (automated)
mysql -e "DELETE FROM mysql.user WHERE User='';"
mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -e "DROP DATABASE IF EXISTS test;"
mysql -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
mysql -e "FLUSH PRIVILEGES;"

echo ""
echo "📦 Downloading and installing Asterisk 18..."
cd /usr/src
wget https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-18-current.tar.gz
tar xvf asterisk-18-current.tar.gz
cd asterisk-18*/

# Install prerequisites
contrib/scripts/install_prereq install

# Configure Asterisk
./configure --with-jansson-bundled --with-pjproject-bundled

# Select modules (use defaults)
make menuselect.makeopts
menuselect/menuselect \
    --enable app_macro \
    --enable CORE-SOUNDS-EN-WAV \
    --enable MOH-OPSOUND-WAV \
    menuselect.makeopts

# Compile and install
echo ""
echo "🔨 Compiling Asterisk (this takes 10-15 minutes)..."
make -j$(nproc)
make install
make samples
make config

# Create Asterisk user
useradd -r -d /var/lib/asterisk -s /sbin/nologin asterisk 2>/dev/null || true
chown -R asterisk:asterisk /var/lib/asterisk
chown -R asterisk:asterisk /var/spool/asterisk
chown -R asterisk:asterisk /var/log/asterisk
chown -R asterisk:asterisk /var/run/asterisk
chown -R asterisk:asterisk /etc/asterisk

# Configure Asterisk to run as asterisk user
sed -i 's/#AST_USER="asterisk"/AST_USER="asterisk"/' /etc/default/asterisk
sed -i 's/#AST_GROUP="asterisk"/AST_GROUP="asterisk"/' /etc/default/asterisk

echo ""
echo "📦 Installing FreePBX 16..."
cd /usr/src
wget http://mirror.freepbx.org/modules/packages/freepbx/freepbx-16.0-latest.tgz
tar xvf freepbx-16.0-latest.tgz
cd freepbx

# Install FreePBX
./install -n

echo ""
echo "🔧 Configuring Apache..."
a2enmod rewrite
sed -i 's/\(^upload_max_filesize = \).*/\120M/' /etc/php/*/apache2/php.ini
sed -i 's/\(^memory_limit = \).*/\1256M/' /etc/php/*/apache2/php.ini
systemctl restart apache2

echo ""
echo "🔧 Configuring firewall..."
# Allow SIP and RTP
ufw allow 5060/udp comment 'SIP'
ufw allow 10000:20000/udp comment 'RTP'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

echo ""
echo "🚀 Starting services..."
systemctl enable asterisk
systemctl start asterisk
systemctl enable apache2
systemctl start apache2

echo ""
echo "✅ FreePBX Bare Metal Installation Complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Access FreePBX web interface:"
echo "   http://$(hostname -I | awk '{print $1}')"
echo ""
echo "2. Complete initial setup wizard"
echo ""
echo "3. Configure PJSIP settings (see docs/FREEPBX-BARE-METAL-SETUP.md):"
echo "   - Direct Media: No"
echo "   - RTP Symmetric: Yes"
echo "   - RTP Port Range: 10000-20000"
echo "   - Codec: PCMU only"
echo ""
echo "4. Validate RTP:"
echo "   ss -lunp | grep asterisk"
echo "   tcpdump -n -i any udp and portrange 10000-20000"
echo ""
echo "5. Test phone-to-phone audio"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: (set during wizard)"
echo ""
