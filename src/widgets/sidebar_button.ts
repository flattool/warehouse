import Gtk from "gi://Gtk?version=4.0"
import type Adw from "gi://Adw?version=1"

import { SharedVars } from "../utils/shared_vars.js"
import { GClass } from "../gobjectify/gobjectify.js"

@GClass()
export class SidebarButton extends Gtk.Button {
	_ready(): void {
		if (this.get_direction() === Gtk.TextDirection.RTL) {
			this.icon_name = "warehouse:sidebar-show-right-symbolic"
		} else {
			this.icon_name = "warehouse:sidebar-show-symbolic"
		}
		const split_view: Adw.OverlaySplitView | undefined = SharedVars.main_window?._split_view
		this.connect("clicked", () => split_view?.set_show_sidebar(true))
		const on_collapse = (): void => this.set_visible(split_view?.collapsed ?? false)
		split_view?.connect("notify::collapsed", on_collapse)
		on_collapse()
	}
}
