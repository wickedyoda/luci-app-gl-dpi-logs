#!/usr/bin/env lua
-- LuCI Controller for GL.iNet DPI Logs Export App

module("luci.controller.gl_dpi_logs", package.seeall)

function index()
    -- Check if dependencies are available
    local fs = require "nixio.fs"
    if not fs.access("/usr/bin/env") then
        return
    end

    -- Register the menu entry under Services
    -- Note: no .leaf = true on parent so child entries can be dispatched
    entry({"admin", "services", "gl_dpi_logs"},
          template("gl-dpi-logs/overview"),
          _("DPI Logs"),
          60)

    -- API endpoints for data and export (flat paths, following the hwnat pattern)
    entry({"admin", "services", "gl_dpi_logs_data"},
          call("get_dpi_data")).leaf = true

    entry({"admin", "services", "gl_dpi_logs_export"},
          call("export_data")).leaf = true
end

function get_dpi_data()
    local json = require "luci.jsonc"
    local stat = require "nixio.fs".stat
    local data = {
        qos_stats = {},
        content_protection = {},
        blocked_domains = {},
        firewall_counters = {rules = {}},
        netify_info = {},
        config = {}
    }

    -- Read QoS stats
    local qos_file = "/tmp/qos_stats"
    if nixio.fs.access(qos_file) then
        local content = nixio.fs.readfile(qos_file)
        if content then
            for key, value in content:gmatch("(%S+):(%d+)") do
                data.qos_stats[key] = tonumber(value)
            end
            -- Extract date if present
            for date in content:gmatch("date:([%d-]+)") do
                data.qos_stats.date = date
            end
        end
    end

    -- Read content protection stats
    local cp_file = "/tmp/content_protection_stats"
    if nixio.fs.access(cp_file) then
        local content = nixio.fs.readfile(cp_file)
        if content then
            for key, value in content:gmatch("(%S+):(%d+)") do
                data.content_protection[key] = tonumber(value)
            end
            for date in content:gmatch("date:([%d-]+)") do
                data.content_protection.date = date
            end
        end
    end

    -- Read backup stats
    local cp_backup = "/etc/netifyd/content_protection_stats"
    if nixio.fs.access(cp_backup) then
        local content = nixio.fs.readfile(cp_backup)
        if content then
            for key, value in content:gmatch("(%S+):(%d+)") do
                data.content_protection[key] = tonumber(value)
            end
        end
    end

    -- Parse blocked domains from dnsmasq gl_dpi.conf
    local dnsmasq_conf = "/var/run/dnsmasq/gl_dpi.conf"
    if nixio.fs.access(dnsmasq_conf) then
        local content = nixio.fs.readfile(dnsmasq_conf)
        if content then
            local count = 0
            for domain in content:gmatch("ipset=/([^/]+)/GL_DPI_BLOCK") do
                table.insert(data.blocked_domains, domain)
                count = count + 1
                -- Limit to 500 domains for web display
                if count >= 500 then break end
            end
            data.blocked_domains_count = count
        end
    end

    -- Get firewall counters from iptables parental_control chain
    local handle = io.popen("iptables -L parental_control -n -v --line-numbers 2>/dev/null")
    if handle then
        local output = handle:read("*a")
        handle:close()
        if output then
            data.firewall_counters = data.firewall_counters or {}
            data.firewall_counters.raw = output
            data.firewall_counters.rules = data.firewall_counters.rules or {}
            -- Parse packet counts
            for pkts, bytes, target in output:gmatch("(%d+)%s+(%d+)%s+(%S+)") do
                table.insert(data.firewall_counters.rules, {
                    pkts = tonumber(pkts),
                    bytes = tonumber(bytes),
                    target = target
                })
            end
        end
    end

    -- Check netifyd status
    local netify_pid = nixio.fs.readfile("/var/run/netifyd.pid")
    if netify_pid then
        data.netify_info.running = true
        data.netify_info.pid = netify_pid
    else
        data.netify_info.running = false
    end

    -- Check app-metadata.json timestamp
    if nixio.fs.stat("/etc/netifyd/app-metadata.json") then
        data.netify_info.app_metadata_last_update = nixio.fs.stat("/etc/netifyd/app-metadata.json").ctime
    end

    -- Get UCI config
    local uci = require "uci"
    local cursor = uci.cursor()
    cursor.load("gl_dpi")
    data.config.dpi_log_level = cursor.get("gl_dpi", "dpi_config", "log")
    cursor.unload("gl_dpi")

    -- Get content protection config
    local cp_config = {}
    local uci2 = uci.cursor()
    uci2.load("gl_dpi_content_protection")
    uci2.foreach("gl_dpi_content_protection", "content_protection", function(s)
        cp_config.enabled = s.enabled
        cp_config.categories = s.category or ""
        cp_config.apps = s.app or ""
    end)
    data.config.content_protection = cp_config

    luci.http.prepare_content("application/json")
    luci.http.write(json.stringify(data))
end

function export_data()
    local json = require "luci.jsonc"
    local fs = require "nixio.fs"

    local format = luci.http.formvalue("format") or "json"
    local data = {}

    -- Read stat files
    for _, entry in ipairs({
        {"/tmp/qos_stats", "qos_stats"},
        {"/tmp/content_protection_stats", "content_protection"},
        {"/etc/netifyd/content_protection_stats", "content_protection_backup"},
        {"/etc/netifyd/qos_stats", "qos_stats_backup"},
    }) do
        if fs.access(entry[1]) then
            data[entry[2]] = fs.readfile(entry[1])
        end
    end

    -- Read blocked domains
    if fs.access("/var/run/dnsmasq/gl_dpi.conf") then
        local domains = {}
        local content = fs.readfile("/var/run/dnsmasq/gl_dpi.conf")
        if content then
            for domain in content:gmatch("ipset=/([^/]+)/GL_DPI_BLOCK") do
                table.insert(domains, domain)
            end
        end
        data.blocked_domains = domains
    end

    -- iptables output
    local handle = io.popen("iptables -L parental_control -n -v 2>/dev/null")
    if handle then
        data.iptables_parental_control = handle:read("*a")
        handle:close()
    end

    local timestamp = os.date("%Y%m%d_%H%M%S")

    if format == "csv" then
        luci.http.header("Content-Disposition", "attachment; filename=dpi_export_" .. timestamp .. ".csv")
        local csv = "Metric,Value,Date\n"
        for k, v in pairs(data) do
            if type(v) == "string" and not k:find("_backup") then
                for key, val in v:gmatch("(%S+):(%d+)") do
                    local date = v:match("date:(%S+)") or ""
                    csv = csv .. key .. "," .. val .. "," .. date .. "\n"
                end
            end
        end
        if data.blocked_domains then
            for _, d in ipairs(data.blocked_domains) do
                csv = csv .. "domain," .. d .. ",\n"
            end
        end
        luci.http.write(csv)
    else
        luci.http.header("Content-Disposition", "attachment; filename=dpi_export_" .. timestamp .. ".json")
        luci.http.prepare_content("application/json")
        luci.http.write(json.stringify(data, 2))
    end
end