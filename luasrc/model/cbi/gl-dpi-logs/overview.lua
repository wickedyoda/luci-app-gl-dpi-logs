-- CBI model for DPI Logs Overview
local fs = require "nixio.fs"

local qos_stats = ""
local content_stats = ""

if fs.access("/tmp/qos_stats") then
    qos_stats = fs.readfile("/tmp/qos_stats") or ""
end

if fs.access("/tmp/content_protection_stats") then
    content_stats = fs.readfile("/tmp/content_protection_stats") or ""
end

local m = Map("gl_dpi_logs", translate("DPI Logs"))

local s = m:section(SimpleSection, nil, translate(
    "This page shows DPI and Content Filtering statistics from your GL.iNet router."
))

local stat = m:section(ParsedString, "Statistics", "statistics")
stat:style("table")

-- QoS Stats display
local s1 = m:section(Table, {}, "QoS Statistics")
s1:style("table")
s1.read = function(self, section)
    luci.sys.call("echo ''")
end

-- Show raw stats as text
local info = m:section(SimpleSection)
info.title = translate("QoS Stats File")
info.description = translate("Contents of /tmp/qos_stats")
info.template = "gl-dpi-logs/stats_display"
info.data = qos_stats

local info2 = m:section(SimpleSection)
info2.title = translate("Content Protection Stats File")
info2.description = translate("Contents of /tmp/content_protection_stats")
info2.template = "gl-dpi-logs/stats_display"
info2.data = content_stats

return m