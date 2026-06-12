import Gtk from "gi://Gtk?version=4.0"
import GObject from "gi://GObject?version=2.0"

import { GClass, Signal, Property, from, OnSignal } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/select_button.ui" })
export class SelectButton extends from(Gtk.ToggleButton, {
	keyboard_shortcut: Property.readwrite.string("<primary>Return"),
	selection_mode_enabled: Property.readwrite.bool(),
	toggle_selection_mode: Signal([], { flags: GObject.SignalFlags.ACTION }),
}) {
	@OnSignal("toggle-selection-mode")
	#on_toggle_selection_mode(): void {
		if (!this.sensitive) return
		this.selection_mode_enabled = !this.selection_mode_enabled
	}

	protected _get_trigger(__: this, shortcut_str: string): Gtk.ShortcutTrigger {
		return Gtk.ShortcutTrigger.parse_string(shortcut_str)
	}
}
