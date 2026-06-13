import GLib from "gi://GLib?version=2.0"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, OnSimpleAction, Property, SimpleAction, WatchProp, from } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { DataSubpage } from "./data_subpage.js"
import { Package } from "../flatpak.js"
import { FileList } from "../utils/file_list.js"

import "../widgets/sidebar_button.js"
import "./data_subpage.js"
import "../widgets/search_button.js"
import "../widgets/select_button.js"
import { iterate_list_model } from "../utils/helper_funcs.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_page.ui" })
export class DataPage extends from(BasePage, {
	selection_mode_enabled: Property.readwrite.bool(),
	data_dir: Property.readonly.gobject(Gio.File),
	request_selection_mode: SimpleAction(),
	sort: SimpleAction({ parameter_type: new GLib.VariantType("(sb)") }),
	_files: Child<FileList>(),
	_active_data: Child<Gio.ListModel<Gio.File>>(),
	_active_filter: Child<Gtk.CustomFilter>(),
	_leftover_data: Child<Gio.ListModel<Gio.File>>(),
	_leftover_filter: Child<Gtk.CustomFilter>(),
	_sort_button: Child<Gtk.MenuButton>(),
	_current: Child<DataSubpage>(),
	_leftover: Child<DataSubpage>(),
}) {
	readonly #seen_paths = new Set<string>()

	constructor(params?: typeof DataPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:file-manager-symbolic"
		params.sidebar_title = _("User Data")
		params.data_dir = Package.user_data_dir
		super(params)
		this._active_filter.set_filter_func((item) => {
			if (!(item instanceof Gio.File) || !this.installations) return false
			for (const inst of iterate_list_model(this.installations)) {
				if (inst.has_package_by_id(item.get_basename()!)) return true
			}
			return false
		})
		this._leftover_filter.set_filter_func((item) => {
			if (!(item instanceof Gio.File) || !this.installations) return false
			for (const inst of iterate_list_model(this.installations)) {
				if (inst.has_package_by_id(item.get_basename()!)) return false
			}
			return true
		})
	}

	// async #test(): Promise<void> {
	// 	const menu: Gio.Menu = new Gio.Menu()
	// 	menu.append("Request", "DataPage.request_selection_mode")
	// 	const item = Gio.MenuItem.new("Sort", "DataPage.sort")
	// 	item.set_attribute_value("target", new GLib.Variant("(sb)", ["name", false]))
	// 	menu.append_item(item)
	// 	this._sort_button.menu_model = menu
	// }

	@OnSimpleAction("request_selection_mode")
	#on_request_selection_mode(): void {
		this.selection_mode_enabled = true
	}

	@WatchProp("loading")
	#on_loading_changed(): void {
		if (this.loading) {
			this.#seen_paths.clear()
			this._files.refresh()
		}
		this.selection_mode_enabled = false
	}
}
