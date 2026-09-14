include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI app for GL.iNet DPI and Content Filtering Log Export
LUCI_DEPENDS:=+kmod-netfilter-netfilter +kmod-nf-nat +ipset +iptables-mod-tproxy +libubus-luardata +lua

define Package/luci-app-gl-dpi-logs/install
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/controller
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/model/cbi/gl-dpi-logs
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/view/gl-dpi-logs
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/model/cbi
	$(INSTALL_DIR) $(1)/etc/config

	$(INSTALL_DATA) ./luasrc/controller/gl_dpi_logs.lua $(1)/usr/lib/lua/luci/controller/
	$(INSTALL_DATA) ./luasrc/model/cbi/gl-dpi-logs/overview.lua $(1)/usr/lib/lua/luci/model/cbi/gl-dpi-logs/
	$(INSTALL_DATA) ./root/usr/share/luci/menu.d/gl-dpi-logs.json $(1)/usr/share/luci/menu.d/
endef

define Package/luci-app-gl-dpi-logs/conffiles
/etc/config/gl_dpi_logs
endef

include ../../lang/lua/luci.mk

define Package/luci-app-gl-dpi-logs/description
  LuCI app for exporting DPI and content filtering logs from
  GL.iNet routers running OpenWrt with Netify DPI.
  Reads statistics from /tmp/qos_stats, /tmp/content_protection_stats,
  parses blocked domains from dnsmasq, and exports to JSON/CSV.
endef

$(eval $(call BuildPackage,luci-app-gl-dpi-logs))