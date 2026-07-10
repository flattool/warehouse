import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"
import GObject from "gi://GObject?version=2.0"

import { Child, GClass, PostInit, Property, Signal, WatchProp, from, next_idle } from "../gobjectify/gobjectify.js"
import { DataBox } from "./data_box.js"
import { get_file_size_bytes, get_readable_byte_size, iterate_list_model } from "../utils/helper_funcs.js"
import { SizedFolder } from "./size_folder.js"

import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_subpage.ui" })
export class DataSubpage extends from(Adw.BreakpointBin, {
	show_leftover: Property.readonly.bool(),
	selection_mode_enabled: Property.readwrite.bool(),
	folders: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<SizedFolder>>(),
	loading: Property.readwrite.bool(),
	size: Property.readwrite.double(-1),
	selection_text: Property.readwrite.string(),
	any_search_results: Property.readwrite.bool(true),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_flow_box: Child<Gtk.FlowBox>(),
}) {
	readonly #selected_folders = new Set<Gio.File>()

	constructor(params?: typeof DataSubpage.$params) {
		super(params)
		if (!this.folders) return
		this._flow_box.bind_model(this.folders, (folder) => {
			const box = new DataBox({ folder: folder.folder, is_leftover: this.show_leftover })
			let old_size = folder.size
			box.size = old_size
			folder.$connect("notify::size", () => {
				box.size = folder.size
				if (folder.size === -1) return
				if (this.size === -1) {
					this.size = folder.size
					return
				}
				this.size -= old_size
				old_size = folder.size
				this.size += folder.size
			})
			box.$connect("notify::is-selected", () => {
				if (box.is_selected) {
					this.#selected_folders.add(folder.folder!)
				} else {
					this.#selected_folders.delete(folder.folder!)
				}
				this.#selection_changed()
			})
			next_idle().then(() => box.get_parent()?.set_focusable(false))
			return box
		})
	}

	@PostInit
	#selection_changed(): void {
		this.selection_text = _("%s Selected").format(this.#selected_folders.size)
	}

	@WatchProp("loading")
	#on_loading_changed(): void {
		if (!this.loading) return
		this.#selected_folders.clear()
		this.#selection_changed()
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

	do_search(search_text: string): void {
		if (!this.folders) return
		let total_visible = 0
		for (const box of this._flow_box) {
			const data_box = (box as Gtk.FlowBoxChild).child as DataBox
			box.visible = (
				data_box.title.toLocaleLowerCase().includes(search_text)
				|| data_box.subtitle.toLocaleLowerCase().includes(search_text)
			)
			if (box.visible) {
				total_visible += 1
			}
		}
		print(search_text)
		this.any_search_results = !search_text || total_visible > 0
	}

	protected _get_readable_size(__: this, size: number): string {
		return size >= 0 ? get_readable_byte_size(size) : _("Loading Size...")
	}

	protected _is_size_unknown(__: this, size: number): boolean {
		return size < 0
	}

	protected _get_title(__: this, show_leftover: boolean): string {
		return show_leftover ? _("Leftover Data") : _("Active Data")
	}
}
