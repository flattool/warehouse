import GLib from "gi://GLib?version=2.0"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, OnSimpleAction, Property, SimpleAction, WatchProp, from } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { DataSubpage } from "./data_subpage.js"
import { Package } from "../flatpak.js"
import { FileList } from "../utils/file_list.js"
import { iterate_list_model } from "../utils/helper_funcs.js"
import { make_menu } from "../utils/menu_builder.js"

import "../widgets/sidebar_button.js"
import "./data_subpage.js"
import "../widgets/search_button.js"
import "../widgets/select_button.js"

const make_sort_menu = (): Gio.Menu => (
	make_menu()
	.section(
		_("Sort"),
		make_menu()
		.item({ label: _("By Name"), action: "DataPage.sort::name" })
		.item({ label: _("By ID"), action: "DataPage.sort::id" })
		.item({ label: _("By Size"), action: "DataPage.sort::size" }),
	).section(
		null,
		make_menu()
		.item({ label: _("Ascending"), action: "DataPage.order::asc" })
		.item({ label: _("Descending"), action: "DataPage.order::desc" }),
	).build()
)

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_page.ui" })
export class DataPage extends from(BasePage, {
	selection_mode_enabled: Property.readwrite.bool(),
	data_dir: Property.readonly.gobject(Gio.File),
	file_sorter: Property.readwrite.gobject(Gtk.Sorter),
	request_selection_mode: SimpleAction(),
	sort: SimpleAction({ parameter_type: new GLib.VariantType("s"), state: GLib.Variant.new_string("name") }),
	order: SimpleAction({ parameter_type: new GLib.VariantType("s"), state: GLib.Variant.new_string("asc") }),
	_files: Child<FileList>(),
	_active_data: Child<Gio.ListModel<Gio.File>>(),
	_active_filter: Child<Gtk.CustomFilter>(),
	_leftover_data: Child<Gio.ListModel<Gio.File>>(),
	_leftover_filter: Child<Gtk.CustomFilter>(),
	_sort_button: Child<Gtk.MenuButton>(),
	_current: Child<DataSubpage>(),
	_leftover: Child<DataSubpage>(),
}) {
	#ascending = true

	#id_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof Gio.File)) return -1
		if (!(two instanceof Gio.File)) return 1
		const result = (
			one.get_basename() ?? ""
		).localeCompare(
			two.get_basename() ?? "",
		)
		return this.#ascending ? result : -result
	})

	#name_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof Gio.File)) return -1
		if (!(two instanceof Gio.File)) return 1
		const result = (
			one.get_basename()?.split(".").at(-1) ?? ""
		).localeCompare(
			two.get_basename()?.split(".").at(-1) ?? "",
		)
		return this.#ascending ? result : -result
	})

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
		this._sort_button.menu_model = make_sort_menu()
	}

	@OnSimpleAction("request_selection_mode")
	#on_request_selection_mode(): void {
		this.selection_mode_enabled = true
	}

	@OnSimpleAction("sort")
	@OnSimpleAction("order")
	#on_sort(action: Gio.SimpleAction, value: GLib.Variant<"s">): void {
		action.state = value

		const sort_by = this.sort.get_state()!.get_string()[0] as "name" | "id" | "size"
		const order = this.order.get_state()!.get_string()[0] as "asc" | "desc"

		this.#ascending = order === "asc"
		print(sort_by, order)
	}

	@WatchProp("loading")
	#on_loading_changed(): void {
		if (this.loading) {
			this._files.refresh()
		}
		this.selection_mode_enabled = false
	}
}
