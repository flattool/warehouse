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
	next_idle,
} from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { DataSubpage } from "./data_subpage.js"
import { Package, type Installation } from "../flatpak.js"
import { FileList } from "../utils/file_list.js"
import { iterate_list_model } from "../utils/helper_funcs.js"
import { ArrayStore } from "../utils/array_store.js"
import { SizedFolder } from "./size_folder.js"

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
	refreshing: Property.readwrite.bool(),
	sort_act: SimplerAction.property("sort", (s: SortKind) => GLib.Variant.new_string(s)),
	order_act: SimplerAction.property("order", (o: OrderKind) => GLib.Variant.new_string(o)),
	change_selection_mode: SimplerAction.param.bool(),
	_active_data: Child<ArrayStore<SizedFolder>>(),
	_all_apps: Child<Gtk.FlattenListModel<Package>>(),
	_installations_packages: Child<Gtk.MapListModel>(),
	_leftover_data: Child<ArrayStore<SizedFolder>>(),
	_files: Child<FileList>(),
	_sort_button: Child<Gtk.MenuButton>(),
	_active_page: Child<DataSubpage>(),
	_leftover_page: Child<DataSubpage>(),
}) {
	readonly #id_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof SizedFolder)) return -1
		if (!(two instanceof SizedFolder)) return 1
		const result = (
			one.folder?.get_basename() ?? ""
		).localeCompare(
			two.folder?.get_basename() ?? "",
		)
		return this.order === "asc" ? result : -result
	})

	readonly #name_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof SizedFolder)) return -1
		if (!(two instanceof SizedFolder)) return 1
		const result = (
			one.folder?.get_basename()?.split(".").at(-1) ?? ""
		).localeCompare(
			two.folder?.get_basename()?.split(".").at(-1) ?? "",
		)
		return this.order === "asc" ? result : -result
	})

	readonly #size_sorter = Gtk.CustomSorter.new((one, two) => {
		if (one === two) return 0
		if (!(one instanceof SizedFolder)) return -1
		if (!(two instanceof SizedFolder)) return 1
		const size_one = one.size
		const size_two = two.size
		const result = size_one - size_two
		return this.order === "asc" ? result : -result
	})

	readonly #package_ids = new Set<string>()

	constructor(params?: typeof DataPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:file-manager-symbolic"
		params.sidebar_title = _("User Data")
		params.data_dir = Package.user_data_dir
		super(params)
		this._installations_packages.set_map_func((inst) => (inst as Installation).packages)
		this.#request_refresh()
		this._all_apps.connect("items-changed", () => this.#request_refresh())
		this._files.connect("items-changed", () => this.#request_refresh())
		this._sort_button.menu_model = make_sort_menu()
		this._active_page.$connect("notify::size", () => this.#on_page_size_changed())
		this._leftover_page.$connect("notify::size", () => this.#on_page_size_changed())
	}

	@Debounce(200)
	#on_page_size_changed(): void {
		if (this.sorter !== this.#size_sorter) return
		this.sorter.changed(Gtk.SorterChange.DIFFERENT)
	}

	@WatchProp("order")
	#update_sorter(): void {
		this.sorter?.changed(Gtk.SorterChange.DIFFERENT)
	}

	@WatchProp("sort")
	#on_sort_changed(): void {
		this.sorter = ((): Gtk.CustomSorter => {
			switch (this.sort) {
				case "id": return this.#id_sorter
				case "name": return this.#name_sorter
				case "size": return this.#size_sorter
			}
		})()
		this.sorter?.changed(Gtk.SorterChange.DIFFERENT)
	}

	#request_refresh(): void {
		this.refreshing = true
		this.selection_mode_enabled = false
		this.#refresh_lists()
	}

	@Debounce(200)
	#refresh_lists(): void {
		this.#package_ids.clear()
		this._active_page.size = -1
		this._leftover_page.size = -1

		const seen_active_ids = new Set<string>()
		const active_dirs: SizedFolder[] = []
		for (const pkg of iterate_list_model(this._all_apps)) {
			this.#package_ids.add(pkg.application)
			if (seen_active_ids.has(pkg.application) || !pkg.data_dir?.query_exists(null)) {
				continue
			}
			seen_active_ids.add(pkg.application)
			active_dirs.push(new SizedFolder({ folder: pkg.data_dir }))
		}

		const leftovers: SizedFolder[] = []
		for (const file of this._files) {
			const id = file.get_basename()
			if (id !== null && !this.#package_ids.has(id)) {
				leftovers.push(new SizedFolder({ folder: file }))
			}
		}

		this._active_data.swap_contents(active_dirs)
		this._leftover_data.swap_contents(leftovers)

		next_idle().then(() => this.refreshing = false)
	}

	@OnSimplerAction("change_selection_mode")
	#on_request_selection_mode(change_to: boolean): void {
		this.selection_mode_enabled = change_to
	}

	protected _get_header_buttons_sensitive(
		__: this,
		page: DataSubpage,
		loading: boolean,
		refreshing: boolean,
		n_active: number,
		n_leftover: number,
	): boolean {
		return !loading && !refreshing && page.show_leftover ? n_leftover > 0 : n_active > 0
	}

	protected _get_show_loading(): boolean {
		return this.loading || this.refreshing
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		const text = entry.text.toLocaleLowerCase()
		this._active_page.search_text = text
		this._leftover_page.search_text = text
	}
}
