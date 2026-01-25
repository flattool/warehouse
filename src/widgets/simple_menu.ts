import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { SimpleMenuItem } from "./simple_menu_item.js"

@GClass()
export class SimpleMenu extends from(Gtk.ListBox, {
	menu_button: Property.gobject(Gtk.MenuButton, { flags: "CONSTRUCT_ONLY" }),
}, Gtk.Buildable) {
	readonly #popover = new Gtk.Popover({ child: this, css_classes: ["menu"] })

	_ready(): void {
		this.selection_mode = Gtk.SelectionMode.NONE
		this.menu_button?.set_popover(this.#popover)
		this.connect("row-activated", this.#on_row_activated.bind(this))
	}

	#on_row_activated(__: this, row: Gtk.ListBoxRow): void {
		this.#popover.popdown()
		if (row instanceof SimpleMenuItem) {
			row.emit("chosen")
		}
	}
}
