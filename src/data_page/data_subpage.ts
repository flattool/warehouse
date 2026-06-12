import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, Property, WatchProp, from, next_idle } from "../gobjectify/gobjectify.js"
import { DataBox } from "./data_box.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_subpage.ui" })
export class DataSubpage extends from(Adw.BreakpointBin, {
	show_leftover: Property.readonly.bool(),
	selection_mode_enabled: Property.readwrite.bool(),
	folders: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Gio.File>>(),
	_flow_box: Child<Gtk.FlowBox>(),
}) {
	constructor(params?: typeof DataSubpage.$params) {
		super(params)
		if (this.folders) {
			this._flow_box.bind_model(this.folders, (folder) => {
				const box = new DataBox({ folder })
				next_idle().then(() => box.parent.focusable = false)
				return box
			})
		}
	}

	protected _get_title(__: this, show_leftover: boolean): string {
		return show_leftover ? _("Leftover Data") : _("Active Data")
	}

	on_button_clicked(): void {
		print("button clicked")
	}

	@WatchProp("selection_mode_enabled")
	#on_selection_mode_changed(): void {
		for (const child of this._flow_box) {
			if (!(child instanceof Gtk.FlowBoxChild) || !(child.child instanceof DataBox)) continue
			child.child.selection_mode_enabled = this.selection_mode_enabled
		}
	}
}
