# Privacy Policy

## 1. Introduction

This Privacy Policy describes how the LuCI GL DPI Logs application ("the App") collects, uses, and protects information when you use it on your OpenWrt/LEDE router.

## 2. Information We Collect

The App operates entirely **locally on your router**. It:

- Reads and displays existing router logs (QoS statistics, content filtering logs, TCP dump files)
- **Does NOT transmit any data off your router**
- **Does NOT collect personal information**
- **Does NOT use analytics, telemetry, or third-party services**

## 3. Log Data Processed

The App processes these local log files:
- `/tmp/qos_stats` - QoS bandwidth statistics
- `/tmp/content_protection_stats` - Content filtering logs  
- `/var/run/dnsmasq/gl_dpi.conf` - DPI domain data
- iptables/ip6tables output - Firewall counters

## 4. No User Data Collection

- No authentication or user accounts
- No cookies, tracking, or analytics
- No network communication with external servers
- All processing occurs in memory on the router

## 5. Data Export

When you export logs via the App:
- The exported JSON/CSV data remains on your local network
- You control when and how to download the data
- We do not receive copies of your exported data

## 6. Changes to This Policy

This policy may be updated. Changes will be reflected in the next version of the App.

## 7. Contact

For privacy questions, contact the project maintainers through the project repository.

---

**Last updated:** September 2026