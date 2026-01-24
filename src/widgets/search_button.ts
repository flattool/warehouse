import Gtk from "gi://Gtk?version=4.0"
import GObject from "gi://GObject?version=2.0"

import { from, GClass, OnSignal, Property, Signal } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/search_button.ui" })
@Signal("start-searching", { flags: GObject.SignalFlags.ACTION })
export class SearchButton extends from(Gtk.ToggleButton, {
	search_bar: Property.gobject(Gtk.SearchBar),
	keyboard_shortcut: Property.string({ default: "<primary>f" }),
}) {
	@OnSignal("start-searching")
	#on_start_search(): void {
		if (!this.sensitive) return
		if (this.search_bar && !this.search_bar.sensitive) return
		this.active = true
		const entry: Gtk.Widget | undefined = this.search_bar?.child
		if (entry instanceof Gtk.SearchEntry) {
			entry.grab_focus()
		}
	}

	protected _get_trigger(__: this, shortcut_str: string): Gtk.ShortcutTrigger {
		return Gtk.ShortcutTrigger.parse_string(shortcut_str)
	}
}
