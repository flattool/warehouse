import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, WatchProp, Property, from, Child, Signal, next_idle, PostInit } from "../gobjectify/gobjectify.js"
import { get_file_size_bytes, get_readable_byte_size, get_readable_file_size } from "../utils/helper_funcs.js"

// class OldParent {
// 	constructor(
// 		private readonly parent: Gtk.Widget,
// 		private readonly focusable = parent.focusable,
// 	) {}

// 	apply(): void { this.parent.focusable = this.focusable }
// }

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_box.ui" })
export class DataBox extends from(Gtk.Box, {
	title: Property.readwrite.string(),
	selection_mode_enabled: Property.readwrite.bool(),
	is_selected: Property.readwrite.bool(),
	app_id: Property.readonly.string(),
	folder: Property.readonly.gobject(Gio.File),
	readable_size: Property.readwrite.string(),
	is_warehouse: Property.readwrite.bool(),
	size_reported: Signal([Number]),
	_icon: Child<Gtk.Image>(),
	_select_button: Child<Gtk.CheckButton>(),
}) {
	#click = new Gtk.GestureClick()
	#long_press = new Gtk.GestureLongPress()
	#is_pressed = false
	// #old_parent_data?: OldParent

	constructor(params?: typeof DataBox.$params) {
		super(params)
		this.add_controller(this.#click)
		this.add_controller(this.#long_press)
		this.#click.$connect("released", (_g, _n, x, y) => this.#on_clicked(x, y))
		this.#long_press.$connect("pressed", () => this.#on_pressed())
		if (this.folder) {
			this.title = this.folder.get_basename()?.split(".").at(-1) || ""
			const id = this.folder.get_basename() || ""
			this._icon.icon_name = id
			this.is_warehouse = id === pkg.app_id
		}
	}

	@PostInit
	async #load_size(): Promise<void> {
		const path = this.folder?.get_path()
		if (!path) return
		try {
			const size = await get_file_size_bytes(path)
			this.readable_size = "~ " + get_readable_byte_size(size)
			this.$emit("size-reported", size)
		} catch (e) {
			print("Failed to get readable size:", e)
		}
	}

	#on_clicked(x: number, y: number): void {
		if (this.#is_pressed) { // The long_press gesture always triggers a click at the end
			this.#is_pressed = false
			return
		}
		if (!this.selection_mode_enabled || x < 0 || y < 0 || x > this.get_width() || y > this.get_height()) {
			// Only run when in selection mode, and when the click occurs within the box's bounds
			return
		}
		this.is_selected = !this.is_selected
	}

	#on_pressed(): void {
		this.#is_pressed = true
		if (this.selection_mode_enabled) {
			this.is_selected = true
		} else {
			this.activate_action("DataPage.request_selection_mode", null)
			next_idle().then(() => this.is_selected = true)
		}
	}

	@WatchProp("selection_mode_enabled")
	#on_selection_mode_enabled_changed(): void {
		if (this.selection_mode_enabled) {
			this.add_css_class("activatable")
		} else {
			this.remove_css_class("activatable")
			this.is_selected = false
		}
	}

	protected _is_size_ready(): boolean {
		return Boolean(this.readable_size)
	}
}
