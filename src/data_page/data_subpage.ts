import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import {
	Child, GClass, Menu, PostInit, Property, SimplerAction, WatchProp, from, next_idle,
} from "../gobjectify/gobjectify.js"
import { DataBox } from "./data_box.js"
import { get_readable_byte_size } from "../utils/helper_funcs.js"
import { SizedFolder } from "./size_folder.js"

import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_subpage.ui" })
export class DataSubpage extends from(Adw.BreakpointBin, {
	show_leftover: Property.readonly.bool(),
	selection_mode_enabled: Property.readwrite.bool(),
	folders: Property.readonly.gobject(Gtk.SortListModel).as<Gtk.SortListModel<SizedFolder>>(),
	loading: Property.readwrite.bool(),
	size: Property.readwrite.double(-1),
	selection_text: Property.readwrite.string(),
	search_text: Property.readwrite.string(),

	select_all: SimplerAction.void(),
	copy_paths: SimplerAction.void(),
	trash_selected: SimplerAction.void(),
	attempt_install: SimplerAction.void(),

	_searched_folders: Child<Gtk.FilterListModel<SizedFolder>>(),
	_search_filter: Child<Gtk.CustomFilter>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_flow_box: Child<Gtk.FlowBox>(),
	_more_menu: Child<Gtk.MenuButton>(),
}) {
	readonly #selected_folders = new Set<string>()

	constructor(params?: typeof DataSubpage.$params) {
		super(params)
		this._flow_box.bind_model(this._searched_folders, (folder) => {
			const path = folder.folder?.get_path() ?? ""
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
			if (this.selection_mode_enabled) {
				box.selection_mode_enabled = true
				box.is_selected = this.#selected_folders.has(path)
			}
			box.$connect("notify::is-selected", () => {
				if (box.is_selected) {
					this.#selected_folders.add(path)
				} else {
					this.#selected_folders.delete(path)
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
		this._more_menu.menu_model = Menu.build(Menu.items_for(DataSubpage, {
			attempt_install: _("Reinstall"),
			trash_selected: _("Trash"),
		}))
	}

	@PostInit
	#selection_changed(): void {
		this.selection_text = _("%s Selected").format(this.#selected_folders.size)
	}

	@WatchProp("search_text")
	#on_search_text_changed(): void {
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

	protected _get_visible_page(__: this, n_folders: number): "no-data-page" | "content-page" {
		return n_folders > 0 ? "content-page" : "no-data-page"
	}

	protected _get_no_data_title(): string {
		return (this.show_leftover
			? _("No Leftover Data")
			: _("No Active Data")
		)
	}

	protected _get_no_data_description(): string {
		return (this.show_leftover
			? _("Warehouse cannot see any active user data or your system has no active user data present")
			: _("There is no leftover user data")
		)
	}

	protected _get_no_data_icon(): string {
		return (this.show_leftover
			? "warehouse:check-plain-symbolic"
			: "warehouse:error-symbolic"
		)
	}
}
