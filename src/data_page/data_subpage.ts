import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, Property, WatchProp, from, next_idle } from "../gobjectify/gobjectify.js"
import { DataBox } from "./data_box.js"
import { get_readable_byte_size } from "../utils/helper_funcs.js"

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
	_spinner: Child<Adw.Spinner>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_flow_box: Child<Gtk.FlowBox>(),
}) {
	readonly #size_recorder = new SizeRecorder(this.#size_callback.bind(this))

	constructor(params?: typeof DataSubpage.$params) {
		super(params)
		if (this.folders) {
			this._flow_box.bind_model(this.folders, (folder) => {
				const box = new DataBox({ folder })
				box.$connect("size-reported", (__, size) => this.#size_recorder.add(size))
				next_idle().then(() => box.parent.focusable = false)
				return box
			})
		}
	}

	#size_callback(): void {
		if (this.#size_recorder.length !== (this.folders?.get_n_items() ?? 0)) return
		this._spinner.visible = false
		this.size = this.#size_recorder.get_total()
		this.readable_size = "~ " + get_readable_byte_size(this.size)
	}

	@WatchProp("loading")
	#on_loading_changed(): void {
		if (!this.loading) return
		this.#size_recorder.reset()
		this._spinner.visible = true
		this.readable_size = _("Loading File Size...")
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
