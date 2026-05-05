# 🎵 Personal Music Streaming Server (Arch Linux) — Notes


## 📁 1. Project Setup

    mkdir ~/music-server
    cd ~/music-server
    mkdir templates 
---

## 🐍 2. Install Dependencies

    sudo pacman -S python python-pip

### (Optional but recommended: virtual environment)

    cd ~/music-server
    python -m venv venv
    source venv/bin/activate
    pip install flask
---


## ▶️ 3. Run Server Manually


cd ~/music-server
python app.py

Access locally on : http://localhost:5000

---

## 🌐 4. Access from Same WiFi

Find IP using: ip a

Then open in browser: 
        
        http://<your-ip>:5000
---

## 🌍 5. Remote Access using Tailscale

Install tailscale:

    sudo pacman -S tailscale
    sudo systemctl enable --now tailscaled
    sudo tailscale up

Get IP: 
    tailscale ip -4

Access from anywhere: 
    http://<tailscale-ip>:5000
---

## ⚙️ 6. Create systemd User Service

Create directory: 
        mkdir -p ~/.config/systemd/user

Create service file: 
        nano ~/.config/systemd/user/music-server.service

Paste this:

        [Unit]
        Description=Music Streaming Server
        After=network.target

        [Service]
        ExecStart=/usr/bin/python /home/YOUR_USERNAME/music-server/app.py
        WorkingDirectory=/home/YOUR_USERNAME/music-server
        Restart=always

        [Install]
        WantedBy=default.target

---

## 🔄 7. Enable and Start Service

    systemctl --user daemon-reexec
    systemctl --user daemon-reload
    systemctl --user enable music-server
    systemctl --user start music-server

---

## 🔓 8. Enable Run at Boot (Important)


    loginctl enable-linger $USER
---

## 📊 9. Check Service Status

    systemctl --user status music-server
---

## 🛑 10. Stop / Restart Service

    systemctl --user stop music-server
    systemctl --user restart music-server
---

## 📜 11. View Logs

    journalctl --user -u music-server -f
---

# ✅ Result

* Music server runs automatically
* Streams from ~/Music
* Accessible on local network + anywhere via Tailscale
* Minimal web UI for playback

---
