import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, OnSignal, from } from "../gobjectify/gobjectify.js"
import { SimpleMenuItem } from "./simple_menu_item.js"

@GClass()
export class SimpleMenu extends from(Gtk.ListBox, {
	menu_button: Property.readonly.gobject(Gtk.MenuButton),
}, Gtk.Buildable) {
	readonly #popover = new Gtk.Popover({ child: this, css_classes: ["menu"] })

	constructor(params?: typeof SimpleMenu.$params) {
		params ??= {}
		params.selection_mode = Gtk.SelectionMode.NONE
		super(params)
		this.menu_button?.set_popover(this.#popover)
	}

	@OnSignal("row-activated")
	#on_row_activated(row: Gtk.ListBoxRow): void {
		this.#popover.popdown()
		if (row instanceof SimpleMenuItem) {
			row.emit("chosen")
		}
	}
}
