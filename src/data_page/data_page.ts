import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

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
			"sort",
			{ label: _("Name"), target: "name" },
			{ label: _("ID"), target: "id" },
			{ label: _("Size"), target: "size" },
		),
	),
	Menu.section(
		null,
		Menu.item_group(
			DataPage,
			"order",
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
	request_selection_mode: SimplerAction.void(),
	sort: SimplerAction.state.string({ default: "name" }).as<SortKind>(),
	order: SimplerAction.state.string({ default: "asc" }).as<OrderKind>(),
	_active_data: Child<ArrayStore<Gio.File>>(),
	_all_packages: Child<Gtk.FlattenListModel<Package>>(),
	_installations_packages: Child<Gtk.MapListModel>(),
	_leftover_data: Child<ArrayStore<Gio.File>>(),
	_files: Child<FileList>(),
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

	#package_ids = new Set<string>()

	constructor(params?: typeof DataPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:file-manager-symbolic"
		params.sidebar_title = _("User Data")
		params.data_dir = Package.user_data_dir
		super(params)
		this._installations_packages.set_map_func((inst) => (inst as Installation).packages)
		this.#rebuild_package_ids()
		this._all_packages.connect("items-changed", () => this.#rebuild_package_ids())
		this._files.connect("items-changed", () => this.#rebuild_package_ids())
		this._sort_button.menu_model = make_sort_menu()
	}

	@Debounce(200)
	#rebuild_package_ids(): void {
		const seen_active_ids = new Set<string>()
		const active_dirs: Gio.File[] = []
		this.#package_ids.clear()
		for (const pkg of iterate_list_model(this._all_packages)) {
			this.#package_ids.add(pkg.application)
			if (!pkg.is_app || seen_active_ids.has(pkg.application) || !pkg.data_dir?.query_exists(null)) {
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
