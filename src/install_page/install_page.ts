import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { from, GClass, Child, Property, Signal, SimplerAction } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/install_page.ui" })
export class InstallPage extends from(BasePage, {}) {
	constructor(params?: typeof InstallPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:arrow-pointing-at-line-down-symbolic"
		params.sidebar_title = _("Install Packages")
		super(params)
	}
}
