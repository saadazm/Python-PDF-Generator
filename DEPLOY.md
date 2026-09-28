# Deploying to a Hostinger VPS

These are the steps to run this API on your own VPS. Nobody but you has
the login for that box, so this is a runbook to follow yourself, not
something that gets applied for you.

## 0. Before you start

- A domain (or subdomain) pointed at the VPS's IP address (an A record).
- SSH access to the VPS as a sudo-capable user.
- Python 3.10+ on the VPS (`python3 --version`). Hostinger's Ubuntu/AlmaLinux
  templates ship this already; if not, install via your distro's package
  manager.

## 1. Get the code onto the VPS

```bash
sudo mkdir -p /opt/pdf-generator
sudo chown "$USER" /opt/pdf-generator
git clone <your-repo-url> /opt/pdf-generator
cd /opt/pdf-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Replace the demo API keys

`api/api_keys.json` ships with `demo-free-key` / `demo-pro-key` for local
testing. Before exposing this publicly, generate real keys and delete the
demo ones:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edit `api/api_keys.json` with the generated key(s) as JSON object keys, and
lock down file permissions since it holds your customers' quota state:

```bash
chmod 600 api/api_keys.json
```

**Concurrency note**: the key store is a single JSON file with a
read-modify-write on every request (see `api/auth.py`). That's fine with a
single uvicorn worker. If you later add `--workers N` with N > 1 for
throughput, multiple processes will race on that file and can under-charge
or over-charge quota. Either keep `--workers 1` until you outgrow it, or
migrate the store to SQLite (with `BEGIN IMMEDIATE` transactions) first.

## 3. Run it as a systemd service

Create `/etc/systemd/system/pdf-generator.service`:

```ini
[Unit]
Description=Styled PDF Generator API
After=network.target

[Service]
User=<your-vps-user>
WorkingDirectory=/opt/pdf-generator
ExecStart=/opt/pdf-generator/.venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pdf-generator
sudo systemctl status pdf-generator
journalctl -u pdf-generator -f   # tail logs
```

Note it's bound to `127.0.0.1`, not `0.0.0.0` — it's only reachable through
the nginx reverse proxy in the next step, never directly from the internet.

## 4. Put nginx in front of it (with HTTPS)

Install nginx and certbot if not already present, then create
`/etc/nginx/sites-available/pdf-generator`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/pdf-generator /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com   # issues HTTPS cert, rewrites the block above to redirect :80 -> :443
```

## 5. Lock down the firewall

Only 80/443 (and your SSH port) should be reachable from the internet; the
API itself should never be:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 6. Verify

```bash
curl https://your-domain.com/healthz
curl -X POST https://your-domain.com/v1/generate \
  -H "Content-Type: application/json" -H "X-API-Key: <your-real-key>" \
  -d '{"text_lines": ["it works"]}' -o test.pdf
```

Visit `https://your-domain.com/` in a browser to confirm the no-code
builder UI loads.

## 7. Deploying updates

```bash
cd /opt/pdf-generator
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart pdf-generator
```
