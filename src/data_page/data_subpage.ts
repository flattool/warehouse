import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, PostInit, Property, WatchProp, from, next_idle } from "../gobjectify/gobjectify.js"
import { DataBox } from "./data_box.js"
import { DataPage } from "./data_page.js"
import { get_readable_byte_size } from "../utils/helper_funcs.js"
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
	search_text: Property.readwrite.string(),
	_searched_folders: Child<Gtk.FilterListModel<SizedFolder>>(),
	_search_filter: Child<Gtk.CustomFilter>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_flow_box: Child<Gtk.FlowBox>(),
}) {
	readonly #selected_folders = new Set<Gio.File>()

	constructor(params?: typeof DataSubpage.$params) {
		super(params)
		this._flow_box.bind_model(this._searched_folders, (folder) => {
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
		this._search_filter.set_filter_func((item) => {
			const folder = (item as SizedFolder).folder
			return folder?.get_basename()?.toLocaleLowerCase().includes(this.search_text) ?? false
		})
	}

	@PostInit
	#selection_changed(): void {
		this.selection_text = _("%s Selected").format(this.#selected_folders.size)
	}

	@WatchProp("search_text")
	#on_search_text_changed(): void {
		DataPage.$actions.change_selection_mode.activate(this, false)
		this._search_filter.changed(Gtk.FilterChange.DIFFERENT)
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

	protected _get_no_results(__: this, search_text: string, n_searched: number): boolean {
		return search_text !== "" && n_searched < 1
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
