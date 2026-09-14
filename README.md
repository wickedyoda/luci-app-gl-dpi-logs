# luci-app-gl-dpi-logs

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![OpenWrt](https://img.shields.io/badge/OpenWrt-21.02%2B-orange)
![GL.iNet](https://img.shields.io/badge/GL.iNet-Flint%204-lightgrey)

A LuCI app for exporting **DPI (Deep Packet Inspection)** and **Content Filtering logs** from GL.iNet routers running OpenWrt.

## Features

- Displays QoS packet statistics from `/tmp/qos_stats`
- Displays content protection block counts from `/tmp/content_protection_stats`
- Parses the blocked domains list from `/var/run/dnsmasq/gl_dpi.conf`
- Shows iptables `parental_control` chain counters
- Exports data to **JSON** or **CSV** format for external logging (ELK, Splunk, Grafana, etc.)

## Installation

### Prerequisites

- GL.iNet router (Flint 4 or any model running OpenWrt with Netify DPI)
- SSH access to the router
- At least 1MB free flash storage

### Manual Installation

```bash
# Copy the package to your router's /tmp directory
scp -P <ssh-port> -i ~/.ssh/id_ed25519_flint4 \
  bin/luci-app-gl-dpi-logs_*.ipk root@<router-ip>:/tmp/

# SSH into the router
ssh -p <ssh-port> -i ~/.ssh/id_ed25519_flint4 root@<router-ip>

# Install the package
opkg update
opkg install /tmp/luci-app-gl-dpi-logs_*.ipk

# Restart uhttpd to load the new controller
/etc/init.d/uhttpd restart
```

### From LUCI Web UI

After installation, navigate to:
**Network → DPI Logs**

## Usage

### Viewing Statistics

The overview page shows:
- Live QoS statistics (packets classified by priority level)
- Content protection counters (blocked requests today / total)
- Firewall drop counters (iptables parental_control chain)
- Netify DPI daemon status (running, PID, app metadata age)

### Exporting Data

Click **Export JSON** or **Export CSV** to download a snapshot of all statistics.

- JSON includes raw file contents and blocked domains list
- CSV exports structured metrics with timestamps

### Example CLI Export

```bash
# Get JSON data via curl (after installing the app)
curl -s -b /tmp/cookies.txt \
  http://<router-ip>/cgi-bin/luci/admin/services/gl_dpi_logs/data

# Export via SSH
ssh root@<router-ip> "
  cat /tmp/qos_stats
  echo '---'
  cat /tmp/content_protection_stats
  echo '---'
  cat /var/run/dnsmasq/gl_dpi.conf | wc -l
" > dpi_export_$(date +%Y%m%d).txt
```

## How It Works

The app reads statistics from the GL.iNet DPI system which is based on Netify's DPI engine:

| File | Description |
|------|-------------|
| `/tmp/qos_stats` | QoS packet counts per traffic category |
| `/tmp/content_protection_stats` | Content filtering block counts |
| `/var/run/dnsmasq/gl_dpi.conf` | Blocked domains (ipset format) |
| `/etc/netifyd/app-metadata.json` | DPI engine app signature database |
| `/etc/config/gl_dpi_content_protection` | Active content protection UCI config |

Statistics are read directly from the router's filesystem — no additional daemons or services are required.

## Building from Source

```bash
# Clone this repo
git clone https://github.com/wickedyoda/luci-app-gl-dpi-logs.git
cd luci-app-gl-dpi-logs

# The Makefile uses standard OpenWrt ImageBuilder patterns.
# Place in your OpenWrt feed or use with:
#   ./scripts/feeds install -a -p luci-app-gl-dpi-logs
#   make menuconfig  # select the package under LuCI applications
#   make package/luci-app-gl-dpi-logs/compile
```

## License

MIT