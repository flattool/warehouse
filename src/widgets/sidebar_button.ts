import Gtk from "gi://Gtk?version=4.0"
import type Adw from "gi://Adw?version=1"

import { SharedVars } from "../utils/shared_vars.js"
import { GClass, OnSignal, PostInit, from } from "../gobjectify/gobjectify.js"

@GClass()
export class SidebarButton extends from(Gtk.Button, {}) {
	split_view?: Adw.OverlaySplitView = SharedVars.main_window?._split_view

	constructor(params?: typeof SidebarButton.$params) {
		super(params)
		this.icon_name = (this.get_direction() === Gtk.TextDirection.RTL
			? "warehouse:sidebar-show-right-symbolic"
			: "warehouse:sidebar-show-symbolic"
		)
		this.split_view?.$connect("notify::collapsed", () => this.#on_collapse())
	}

	@PostInit
	#on_collapse(): void {
		this.set_visible(this.split_view?.collapsed ?? false)
	}

	@OnSignal("clicked")
	#on_clicked(): void {
		this.split_view?.set_show_sidebar(true)
	}
}
