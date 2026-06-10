#!/bin/bash
# MathViz — One-time GCE VM setup script
# Run this after SSH-ing into the VM for the first time.
# Usage: bash /opt/mathviz/deploy/setup_vm.sh

set -e

echo "=== [1/5] Installing system dependencies ==="
sudo apt-get update -q
sudo apt-get install -y \
  software-properties-common \
  ffmpeg \
  libcairo2-dev \
  libpango1.0-dev \
  pkg-config \
  python3-dev \
  build-essential \
  git

# Python 3.13 (Ubuntu 22.04 ships 3.10 by default)
echo "=== [2/5] Installing Python 3.13 ==="
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -q
sudo apt-get install -y python3.13 python3.13-venv python3.13-dev

echo "=== [3/5] Creating virtualenv and installing Python deps ==="
cd /opt/mathviz
python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/5] Creating output directories ==="
mkdir -p outputs/animations outputs/solutions
chmod 755 outputs outputs/animations outputs/solutions

echo "=== [5/5] Creating mathviz system user (if not exists) ==="
id -u mathviz &>/dev/null || sudo useradd -r -s /bin/false -d /opt/mathviz mathviz
sudo chown -R mathviz:mathviz /opt/mathviz

echo ""
echo "Setup complete!"
echo "Next steps:"
echo "  1. Create /opt/mathviz/.env with your secrets (see deploy/README_DEPLOYMENT.md)"
echo "  2. sudo cp deploy/mathviz-api.service /etc/systemd/system/"
echo "  3. sudo cp deploy/mathviz-ui.service  /etc/systemd/system/"
echo "  4. sudo systemctl daemon-reload"
echo "  5. sudo systemctl enable --now mathviz-api mathviz-ui"
