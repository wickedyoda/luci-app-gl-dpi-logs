# luci-app-gl-dpi-logs

![License](https://img.shields.io/badge/license-GPLv3%20or%20later-blue.svg)
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

- GL.iNet Flint 4 router (tested on model **GL-BE14000** running OpenWrt 21.02-SNAPSHOT, MediaTek MT7988 Filogic 800, aarch64)
  - *Other GL.iNet models may work but are untested — use at your own risk.*
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
- **Export Raw Files** downloads the actual stat files and full (untruncated) blocked domain list
- **CLI Details** shows file sizes, domain count, iptables totals, and system info

### Example CLI Export

```bash
# Get JSON data via curl (after installing the app)
curl -s -b /tmp/cookies.txt \
  http://<router-ip>/cgi-bin/luci/admin/services/gl_dpi_logs_data

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

## Data Limitations on GL.iGet Flint 4

The GL.iGet Flint 4 firmware (GL-BE14000, MediaTek MT7988, OpenWrt 21.02) provides a reduced set of statistics compared to a full OpenWrt + Netifyd installation. The following limitations are firmware-specific:

### QoS Statistics (`/tmp/qos_stats`)
- **Contains**: Aggregate total only (e.g., `qos:368760 date:2026-09-14`)
- **Missing**: Per-category breakdown — no `qos_pri`, `qos_normal`, `qos_service`, `qos_bulk` counters
- **Cause**: GL.iGet's Netifyd build does not output detailed category-level statistics

### Content Protection Stats (`/tmp/content_protection_stats`)
- **Contains**: Aggregate counts only (e.g., `content_protection_day:12458 content_protection_all:98366`)
- **Missing**: Per-rule or per-category breakdown of blocks

### Blocked Domains (`/var/run/dnsmasq/gl_dpi.conf`)
- **Contains**: Full list of blocked domains (60+ KB, 1,400+ entries) in DNS ipset format
- **Limitation**: Domain count is only available via the CLI Details button or Export Raw Files — the main dashboard shows a truncated list (first 500 domains)

### Firewall Drop Counters
- **Contains**: iptables `parental_control` chain exists with DROP rules for `GL_DPI_BLOCK`
- **Missing**: Rule-level byte/packet counters — the chain drops at the IP level with no per-rule breakdown
- **Alternative**: Use `iptables -L parental_control -n -v --line-numbers` via SSH for full output

### Netify DPI Engine
- **Running**: Yes (PID via `/var/run/netifyd.pid`)
- **Missing**: App metadata (`app-metadata.json`) may exist but is not exposed via the LuCI API — the dashboard shows "Netify data not available" for per-application statistics

### Recommendations for Full Data
For richer statistics, install a full OpenWrt build with upstream Netifyd, or use the **CLI Details** button and **Export Raw Files** feature to access all available raw data.

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

GNU General Public License v3.0 (GPLv3) — see [LICENSE](LICENSE) for details.

**Not open-source in the permissive sense:** This software is copyleft. You
may use, modify, and distribute it provided you comply with the GPLv3 terms,
including providing source code for derivative works. THE SOFTWARE IS PROVIDED
"AS IS", WITHOUT WARRANTY OF ANY KIND. THE DEVELOPERS ARE NOT RESPONSIBLE
FOR ANY ISSUES ARISING FROM USE. See [TOS.md](TOS.md) for full terms.