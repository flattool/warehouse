import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, PostInit, Property, WatchProp, from, next_idle } from "../gobjectify/gobjectify.js"
import { DataBox } from "./data_box.js"
import { get_readable_byte_size, iterate_list_model } from "../utils/helper_funcs.js"

class SizeRecorder {
	readonly #sizes: number[] = []
	readonly on_add: (size: number) => void

	get length(): number { return this.#sizes.length }

	constructor(on_add: typeof this.on_add) {
		this.on_add = on_add
	}

	add(size: number): void {
		this.#sizes.push(size)
		this.on_add(size)
	}

	get_total(): number {
		let total = 0
		this.#sizes.forEach((size) => total += size)
		return total
	}

	reset(): void { this.#sizes.length = 0 }
}

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_subpage.ui" })
export class DataSubpage extends from(Adw.BreakpointBin, {
	show_leftover: Property.readonly.bool(),
	selection_mode_enabled: Property.readwrite.bool(),
	folders: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Gio.File>>(),
	loading: Property.readwrite.bool(),
	size: Property.readwrite.double(),
	readable_size: Property.readwrite.string(),
	selection_text: Property.readwrite.string(),
	_spinner: Child<Adw.Spinner>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_flow_box: Child<Gtk.FlowBox>(),
}) {
	readonly #size_recorder = new SizeRecorder(this.#size_callback.bind(this))
	readonly #selected_folders = new Set<Gio.File>()

	constructor(params?: typeof DataSubpage.$params) {
		super(params)
		if (!this.folders) return
		this.folders.connect("items-changed", () => this.#begin_size_load())
		this._flow_box.bind_model(this.folders, (folder) => {
			const box = new DataBox({ folder, is_leftover: this.show_leftover })
			box.$connect("size-reported", (__, size) => this.#size_recorder.add(size))
			box.$connect("notify::is-selected", () => {
				if (box.is_selected) {
					this.#selected_folders.add(folder)
				} else {
					this.#selected_folders.delete(folder)
				}
				this.#selection_changed()
			})
			next_idle().then(() => box.parent.focusable = false)
			return box
		})
	}

	#begin_size_load(): void {
		this.#size_recorder.reset()
		this._spinner.visible = true
		this.readable_size = _("Loading File Size...")
		if (!this.folders || this.folders.get_n_items() === 0) {
			this.#apply_size(0)
		}
	}

	#apply_size(total: number): void {
		this._spinner.visible = false
		this.size = total
		this.readable_size = "~ " + get_readable_byte_size(total)
	}

	@PostInit
	#selection_changed(): void {
		this.selection_text = _("%s Selected").format(this.#selected_folders.size)
	}

	#size_callback(): void {
		if (this.#size_recorder.length !== (this.folders?.get_n_items() ?? 0)) return
		this.#apply_size(this.#size_recorder.get_total())
	}

	@WatchProp("loading")
	#on_loading_changed(): void {
		if (!this.loading) return
		this.#selected_folders.clear()
		this.#selection_changed()
		this.#begin_size_load()
	}

	@WatchProp("selection_mode_enabled")
	#on_selection_mode_changed(): void {
		if (this.selection_mode_enabled) {
			this._scrolled_window.add_css_class("undershoot-bottom")
		} else {
			this._scrolled_window.remove_css_class("undershoot-bottom")
		}
		for (const child of this._flow_box) {
			if (!(child instanceof Gtk.FlowBoxChild) || !(child.child instanceof DataBox)) continue
			child.child.selection_mode_enabled = this.selection_mode_enabled
		}
	}

	protected _get_title(__: this, show_leftover: boolean): string {
		return show_leftover ? _("Leftover Data") : _("Active Data")
	}
}
