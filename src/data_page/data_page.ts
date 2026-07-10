import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"
import GLib from "gi://GLib?version=2.0"

import {
	GClass,
	Child,
	OnSimplerAction,
	Property,
	SimplerAction,
	WatchProp,
	Menu,
	from,
	Debounce,
} from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { DataSubpage } from "./data_subpage.js"
import { Package, type Installation } from "../flatpak.js"
import { FileList } from "../utils/file_list.js"
import { iterate_list_model } from "../utils/helper_funcs.js"
import { ArrayStore } from "../utils/array_store.js"
import { DataBox } from "./data_box.js"

import "../widgets/sidebar_button.js"
import "./data_subpage.js"
import "../widgets/search_button.js"
import "../widgets/select_button.js"

type SortKind = "name" | "id" | "size"
type OrderKind = "asc" | "desc"

const make_sort_menu = (): Gio.Menu => Menu.build(
	Menu.section(
		_("Sort"),
		Menu.item_group(
			DataPage,
			"sort_act",
			{ label: _("Name"), target: "name" },
			{ label: _("ID"), target: "id" },
			{ label: _("Size"), target: "size" },
		),
	),
	Menu.section(
		null,
		Menu.item_group(
			DataPage,
			"order_act",
			{ label: _("Ascending"), target: "asc" },
			{ label: _("Descending"), target: "desc" },
		),
	),
)

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_page.ui" })
export class DataPage extends from(BasePage, {
	selection_mode_enabled: Property.readwrite.bool(),
	data_dir: Property.readonly.gobject(Gio.File),
	file_sorter: Property.readwrite.gobject(Gtk.Sorter),
	sorter: Property.readwrite.gobject(Gtk.CustomSorter),
	sort: Property.readwrite.string("name").as<SortKind>(),
	order: Property.readwrite.string("asc").as<OrderKind>(),
	sort_act: SimplerAction.property("sort", (s: SortKind) => GLib.Variant.new_string(s)),
	order_act: SimplerAction.property("order", (o: OrderKind) => GLib.Variant.new_string(o)),
	request_selection_mode: SimplerAction.void(),
	_active_data: Child<ArrayStore<Gio.File>>(),
	_all_apps: Child<Gtk.FlattenListModel<Package>>(),
	_installations_packages: Child<Gtk.MapListModel>(),
	_leftover_data: Child<ArrayStore<Gio.File>>(),
	_files: Child<FileList>(),
	_sort_button: Child<Gtk.MenuButton>(),
	_active_page: Child<DataSubpage>(),
	_leftover_page: Child<DataSubpage>(),
}) {
	readonly #id_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof Gio.File)) return -1
		if (!(two instanceof Gio.File)) return 1
		const result = (
			one.get_basename() ?? ""
		).localeCompare(
			two.get_basename() ?? "",
		)
		return this.order === "asc" ? result : -result
	})

	readonly #name_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof Gio.File)) return -1
		if (!(two instanceof Gio.File)) return 1
		const result = (
			one.get_basename()?.split(".").at(-1) ?? ""
		).localeCompare(
			two.get_basename()?.split(".").at(-1) ?? "",
		)
		return this.order === "asc" ? result : -result
	})

	readonly #size_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof Gio.File)) return -1
		if (!(two instanceof Gio.File)) return 1
		return 0
		// const size_one = this.#size_cache.get(one) ?? -1
		// const size_two = this.#size_cache.get(two) ?? -1
		// const result = size_one - size_two
		// return this.order === "asc" ? result : -result
	})

	readonly #package_ids = new Set<string>()

	constructor(params?: typeof DataPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:file-manager-symbolic"
		params.sidebar_title = _("User Data")
		params.data_dir = Package.user_data_dir
		super(params)
		this._installations_packages.set_map_func((inst) => (inst as Installation).packages)
		this.#refresh_lists()
		this._all_apps.connect("items-changed", () => this.#refresh_lists())
		this._files.connect("items-changed", () => this.#refresh_lists())
		this._sort_button.menu_model = make_sort_menu()
	}

	@WatchProp("order")
	@Debounce(200)
	#update_sorter(): void {
		this.selection_mode_enabled = false
		this.sorter?.changed(Gtk.SorterChange.DIFFERENT)
	}

	@WatchProp("sort")
	#on_sort_changed(): void {
		this.selection_mode_enabled = false
		this.sorter = ((): Gtk.CustomSorter => {
			switch (this.sort) {
				case "id": return this.#id_sorter
				case "name": return this.#name_sorter
				case "size": return this.#size_sorter
			}
		})()
		this.sorter?.changed(Gtk.SorterChange.DIFFERENT)
	}

	@Debounce(200)
	#refresh_lists(): void {
		this.#package_ids.clear()

		const seen_active_ids = new Set<string>()
		const active_dirs: Gio.File[] = []
		for (const pkg of iterate_list_model(this._all_apps)) {
			this.#package_ids.add(pkg.application)
			if (seen_active_ids.has(pkg.application) || !pkg.data_dir?.query_exists(null)) {
				continue
			}
			seen_active_ids.add(pkg.application)
			active_dirs.push(pkg.data_dir)
		}
		this._active_data.swap_contents(active_dirs)

		const leftovers: Gio.File[] = []
		for (const file of this._files) {
			const id = file.get_basename()
			if (id !== null && !this.#package_ids.has(id)) {
				leftovers.push(file)
			}
		}
		this._leftover_data.swap_contents(leftovers)
	}

	@OnSimplerAction("request_selection_mode")
	#on_request_selection_mode(): void {
		this.selection_mode_enabled = true
	}

	@WatchProp("loading")
	#on_loading_changed(): void {
		if (this.loading) {
			this._files.refresh()
		}
		this.selection_mode_enabled = false
	}
}
