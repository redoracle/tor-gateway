import os
import signal
import socket
import subprocess
import threading
import time
import requests  # type: ignore
from flask import Flask, render_template, request, jsonify  # type: ignore
from stem.control import Controller  # Requires stem installed

password = os.environ.get("TOR_ControlPassword")
controlport = int(os.environ.get("TOR_ControlPort", 9052
                                 ))
app = Flask(__name__)

# === Paths & Constants ===
BASE_DIR = os.path.dirname(__file__)
ENV_FILE = os.path.join(BASE_DIR, ".env")
TOR_LOG_PATH = "/tmp/tor.log"
TOR_CONTROL_PORT = 9052
TOR_CONTROL_PASSWORD = "yourpassword"  # Optional if cookie auth is used
TOR_CONTROL_COOKIE_PATH = "/run/tor/control.authcookie"  # Depends on setup
PROXIES = {
    "http": "http://127.0.0.1:8118",
    "https": "http://127.0.0.1:8118"
}


# === Utility: Read/Write .env ===
def read_env():
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key] = value
    return config

def write_env(updated_vars):
    try:
        with open(ENV_FILE, "w") as f:
            for key, value in updated_vars.items():
                f.write(f"{key}={value}\n")
        print("[env] .env file updated successfully.")
    except Exception as e:
        print(f"[env] Failed to write .env file: {e}")


# === Exit Node Info & Bootstrap Status ===
def get_exit_info():
    try:
        response = requests.get("http://ip-api.com/json/", proxies=PROXIES, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[exit-info] Non-200 response: {response.status_code}")
    except Exception as e:
        print(f"[exit-info] Error: {e}")
    return {}

def get_bootstrap_status():
    if not os.path.exists(TOR_LOG_PATH):
        return "Unknown"
    try:
        with open(TOR_LOG_PATH, "r") as log:
            lines = log.readlines()
        for line in reversed(lines):
            if "Bootstrapped" in line:
                return line.strip()
    except Exception as e:
        print(f"[bootstrap] Error reading log: {e}")
    return "Bootstrapping..."


# === System Info ===
def get_real_ip():
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=5)
        if r.status_code == 200:
            return r.json().get("ip", "Unknown")
    except Exception as e:
        print(f"[real-ip] Error: {e}")
    return "Unavailable"

def get_container_ips():
    ip_info = {}
    try:
        host = socket.gethostname()
        ip_info["hostname"] = host
        ip_info["local_ip"] = socket.gethostbyname(host)
    except Exception as e:
        ip_info["error"] = f"Error: {e}"
    try:
        ip_info["interfaces"] = subprocess.check_output("ip -4 -o addr", shell=True).decode()
    except Exception as e:
        ip_info["interfaces"] = "Could not fetch interfaces"
    return ip_info

def get_open_ports():
    try:
        return subprocess.check_output("netstat -tuln", shell=True).decode()
    except Exception as e:
        return f"Could not determine open ports: {e}"

def get_dns_servers():
    try:
        with open("/etc/resolv.conf", "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading DNS: {e}"


from stem.control import Controller

def get_tor_circuits():
    try:
        with Controller.from_port(address="127.0.0.1", port=controlport) as controller:
            controller.authenticate(password=password)  # Plaintext version of hashed one
            return controller.get_info("circuit-status")
    except Exception as e:
        return f"Failed to retrieve Tor circuit info: {e}"


# === Restart Logic ===
def restart_container():
    print("[restart] Triggered. Sleeping for UI animation...")
    time.sleep(3)
    try:
        print("[restart] Sending SIGTERM to PID 1 (runsvdir)...")
        os.kill(1, signal.SIGTERM)
    except Exception as e:
        print(f"[restart] Error sending SIGTERM to PID 1: {e}")


# === Flask Routes ===
@app.route('/')
def index():
    config = read_env()
    exit_info = get_exit_info()
    return render_template("index.html", config=config, exit_info=exit_info)

@app.route('/exit_info')
def exit_info_route():
    return jsonify(get_exit_info())

@app.route('/system_info')
def system_info():
    return jsonify({
        "public_ip": get_real_ip(),
        "container_ips": get_container_ips(),
        "open_ports": get_open_ports()
    })

@app.route('/tor_info')
def tor_info():
    return jsonify({
        "dns_servers": get_dns_servers(),
        "tor_circuits": get_tor_circuits(),
        "bootstrap_status": get_bootstrap_status()
    })

@app.route('/update', methods=['POST'])
def update_config():
    data = request.json
    print("[update] Received config:", data)
    write_env(data)
    threading.Thread(target=restart_container).start()
    return jsonify({"status": "ok"})

@app.route('/status')
def status():
    info = get_exit_info()
    if info.get("status") == "success":
        return jsonify({"status": "ready"})
    return jsonify({"status": "bootstrapping", "info": get_bootstrap_status()})

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    print("[flask] UI server starting...")
    app.run(host="0.0.0.0", port=5000, debug=False)