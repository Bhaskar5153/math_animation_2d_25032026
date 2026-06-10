# MathViz — Google Compute Engine Deployment

## Why GCE (not Streamlit Community Cloud)

This app needs **two running processes** simultaneously:
- FastAPI backend on port 8000 (handles AI agents + Manim rendering)
- Streamlit UI on port 8501 (the browser interface)

Streamlit Community Cloud only supports a single Streamlit process, so GCE is required.

---

## Step 1 — Push your code to GitHub

Make sure your repo is on GitHub (private is fine).
The `.env` file is in `.gitignore` — do NOT commit it.

---

## Step 2 — Create the VM

Run this from your local machine (or GCP Cloud Shell):

```bash
gcloud compute instances create mathviz-vm \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --zone=us-central1-a \
  --tags=mathviz-server \
  --scopes=cloud-platform
```

**Why e2-standard-4?** Manim rendering needs ~4 GB RAM. 4 vCPU keeps render times reasonable.
**Why 50GB disk?** Each animation MP4 is ~5–15 MB; this gives room for ~2000+ animations.

---

## Step 3 — Open firewall port for Streamlit

```bash
gcloud compute firewall-rules create allow-streamlit \
  --allow tcp:8501 \
  --target-tags mathviz-server \
  --description "MathViz Streamlit UI"
```

Port 8000 (FastAPI) stays internal — Streamlit talks to it via localhost inside the VM.

---

## Step 4 — SSH into the VM and clone the repo

```bash
gcloud compute ssh mathviz-vm --zone=us-central1-a

# On the VM:
sudo mkdir -p /opt/mathviz
sudo chown $USER:$USER /opt/mathviz
git clone https://github.com/YOUR_ORG/YOUR_REPO.git /opt/mathviz
```

---

## Step 5 — Run the setup script

```bash
bash /opt/mathviz/deploy/setup_vm.sh
```

This installs: Python 3.13, ffmpeg, Cairo, Pango (all Manim deps), then creates the virtualenv and installs all Python packages.

---

## Step 6 — Create the secrets file

```bash
cat > /opt/mathviz/.env << 'EOF'
PROJECT_ID=ai-ml-solutions-492011
GOOGLE_CLOUD_LOCATION=us-central1
VERTEXAI=True
GOOGLE_API_KEY=your_api_key_here
EOF
chmod 600 /opt/mathviz/.env   # only owner can read
```

This replaces the Streamlit secrets panel — the `.env` file is read by `python-dotenv` in `config.py`.

---

## Step 7 — Install and start services

```bash
sudo cp /opt/mathviz/deploy/mathviz-api.service /etc/systemd/system/
sudo cp /opt/mathviz/deploy/mathviz-ui.service  /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mathviz-api mathviz-ui
sudo systemctl start  mathviz-api mathviz-ui
```

---

## Step 8 — Verify it's running

```bash
# Check both services are active
sudo systemctl status mathviz-api
sudo systemctl status mathviz-ui

# Tail live logs
sudo journalctl -u mathviz-api -f    # FastAPI logs
sudo journalctl -u mathviz-ui -f     # Streamlit logs
```

Get your VM's external IP:
```bash
gcloud compute instances describe mathviz-vm \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Open in browser: **http://EXTERNAL_IP:8501**

---

## Updating the app (after code changes)

```bash
gcloud compute ssh mathviz-vm --zone=us-central1-a

cd /opt/mathviz
git pull
source venv/bin/activate
pip install -r requirements.txt   # only needed if deps changed

sudo systemctl restart mathviz-api mathviz-ui
```

---

## Cost estimate

| Component | Spec | ~Monthly cost |
|-----------|------|---------------|
| e2-standard-4 VM | 4 vCPU, 16 GB | ~$97/month |
| 50 GB persistent disk | SSD | ~$8.50/month |
| Egress (video downloads) | ~10 GB/month | ~$1.20/month |
| **Total** | | **~$107/month** |

To save costs when not in use: `gcloud compute instances stop mathviz-vm --zone=us-central1-a`
Stopped VMs only charge for disk (~$8.50/month).
