import Gtk from "gi://Gtk?version=4.0"

import { SharedVars } from "../utils/shared_vars.js"
import { GClass, OnSignal, PostInit } from "../gobjectify/gobjectify.js"

@GClass()
export class SidebarButton extends Gtk.Button {
	@PostInit
	#ready(): void {
		this.icon_name = (this.get_direction() === Gtk.TextDirection.RTL
			? "warehouse:sidebar-show-right-symbolic"
			: "warehouse:sidebar-show-symbolic"
		)
		SharedVars.main_window?._split_view.$connect("notify::collapsed", () => this.#on_collapse())
	}

	@PostInit
	#on_collapse(): void {
		this.set_visible(SharedVars.main_window?._split_view?.collapsed ?? false)
	}

	@OnSignal("clicked")
	#on_clicked(): void {
		SharedVars.main_window?._split_view?.set_show_sidebar(true)
	}
}
