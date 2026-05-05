## Personal Music Streaming Server (Arch Linux)

   
### Create a Music directory to store all your songs

    mkdir ~/Music
---

### Project setup

    git clone https://github.com/kailasnv/Klyro.git
    cd Klyro/
 
### Install Dependencies

    sudo pacman -S python python-pip yt-dlp
    pip install flask 
---


### Run Server Manually

    cd ~/Klyro
    python app.py

Access locally on:
    
    http://localhost:5000
---

### Access from Same WiFi

Find IP using this command: 

        ip a

Then open in browser: 
        
        http://<your-ip>:5000
---

### Remote Access using Tailscale

Install tailscale:

    sudo pacman -S tailscale
    sudo systemctl enable --now tailscaled
    sudo tailscale up

Get IP: 

    tailscale ip -4

Access from anywhere: 

    http://<tailscale-ip>:5000

Install tailscale mobile app on your smartphone (it act as a vpn tunnel) and login with the same email you had given while doing the tailscale setup in your pc(server). And turn on connect and browse to the address: 
    
    http://<tailscale-ip>:5000

---

### Create systemd User Service

Create the directory and service file:

        mkdir -p ~/.config/systemd/user
        nano ~/.config/systemd/user/klyro.service

Paste this and save:

        [Unit]
        Description=Music Streaming Server
        After=network.target

        [Service]
        ExecStart=/usr/bin/python /home/YOUR_USERNAME/Klyro/app.py
        WorkingDirectory=/home/YOUR_USERNAME/Klyro
        Restart=always

        [Install]
        WantedBy=default.target

---

### Enable and Start Service

    systemctl --user daemon-reexec
    systemctl --user daemon-reload
    systemctl --user enable klyro
    systemctl --user start klyro

---

### Enable Run at Boot (Important)

    loginctl enable-linger $USER
---

### Check Service Status

    systemctl --user status klyro
---

### Stop / Restart Service

    systemctl --user stop klyro
    systemctl --user restart klyro
---

### View Logs

    journalctl --user -u klyro -f
---

### Result

* Music server runs automatically
* Streams from ~/Music
* Accessible on local network + anywhere via Tailscale
* Minimal web UI for playback

---
