import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { GClass, Child, Property, from, OnSignal, Debounce, next_idle } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Package } from "../flatpak.js"
import { PackageRow } from "./package_row.js"
import { DetailsPage } from "./details_page.js"
import { SharedVars } from "../utils/shared_vars.js"
import { DropdownButton } from "../widgets/dropdown_button.js"

import "./filter_page.js"
import "../widgets/sidebar_button.js"
import "../widgets/search_group.js"
import "../widgets/search_button.js"
import "../widgets/simple_menu.js"
import "../widgets/simple_menu_item.js"
import "../widgets/group_heading.js"

@GClass() class SelectionManager extends from(GObject.Object, {
	total: Property.readwrite.uint32(),
}) {
	readonly #selected = new Set<Package>()

	reset(): void {
		this.total = 0
		this.#selected.clear()
	}

	select(pack: Package): void {
		this.#selected.add(pack)
		this.total = this.#selected.size
	}

	deselct(pack: Package): void {
		this.#selected.delete(pack)
		this.total = this.#selected.size
	}

	[Symbol.iterator](): IterableIterator<Package> {
		return this.#selected[Symbol.iterator]()
	}
}

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends from(BasePage, {
	show_filter_page: Property.readwrite.bool(),
	search_text: Property.readwrite.string(),
	no_results: Property.readwrite.bool(),
	in_selection_mode: Property.readwrite.bool(),
	show_apps: Property.readwrite.bool(),
	show_runtimes: Property.readwrite.bool(),
	_apps_list: Child<Gio.ListModel<Package>>(),
	_runtimes_list: Child<Gio.ListModel<Package>>(),
	_selection_manager: Child<SelectionManager>(),
	_split_view: Child<Adw.NavigationSplitView>(),
	_search_enty: Child<Gtk.SearchEntry>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	// _app_dropdown: Child<DropdownButton>(),
	_apps_list_box: Child<Gtk.ListBox>(),
	// _runtime_dropdown: Child<DropdownButton>(),
	_runtimes_list_box: Child<Gtk.ListBox>(),
	_details_page: Child<DetailsPage>(),
}) {
	readonly #css_provider = new Gtk.CssProvider()

	constructor(params?: typeof PackagesPage.$params) {
		super(params)
		Gtk.StyleContext.add_provider_for_display(
			Gdk.Display.get_default()!,
			this.#css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		const row_creation_func = (flatpak: Package): PackageRow => {
			const row = new PackageRow({ flatpak, in_selection_mode: this.in_selection_mode })
			row.connect("activated", () => {
				if (!this.in_selection_mode) return
				row.selected = !row.selected
			})
			row.connect("notify::selected", () => {
				if (row.selected) {
					this._selection_manager.select(flatpak)
				} else {
					this._selection_manager.deselct(flatpak)
				}
			})
			return row
		}
		this._apps_list_box.bind_model(this._apps_list, row_creation_func)
		this._runtimes_list_box.bind_model(this._runtimes_list, row_creation_func)
	}

	override grab_focus(): boolean {
		return this.visible && (
			this._apps_list_box.get_selected_row()?.grab_focus()
			|| this._runtimes_list_box.get_selected_row()?.grab_focus()
			|| super.grab_focus()
		)
	}

	#select_first(): void {
		const first_app_row = this._apps_list_box.get_row_at_index(0)
		const first_runtime_row = this._runtimes_list_box.get_row_at_index(0)
		if (first_app_row) {
			this._apps_list_box.select_row(first_app_row)
			this._runtimes_list_box.unselect_all()
		} else if (first_runtime_row) {
			this._runtimes_list_box.select_row(first_runtime_row)
			this._apps_list_box.unselect_all()
		}
	}

	#foreach_row(to_run: (row: PackageRow) => void): void {
		for (let i = 0; ; i += 1) {
			const app_row = this._apps_list_box.get_row_at_index(i)
			const runtime_row = this._runtimes_list_box.get_row_at_index(i)
			if (app_row instanceof PackageRow) {
				to_run(app_row)
			}
			if (runtime_row instanceof PackageRow) {
				to_run(runtime_row)
			}
			if (!app_row && !runtime_row) return
		}
	}

	@OnSignal("notify::search-text")
	#on_search_text_changed(): void {
		let any_matched = false
		let first_visible: PackageRow | null = null
		const search: string = this.search_text.toLocaleLowerCase()
		this.#foreach_row((row) => {
			const title: string = row.title.toLocaleLowerCase()
			const subtitle: string = row.subtitle.toLocaleLowerCase()
			if (row.visible = title.includes(search) || subtitle.includes(search)) {
				any_matched = true
				if (!first_visible) {
					first_visible = row
				}
			}
		})
		this.no_results = !any_matched
		if (
			this.search_text !== ""
			|| !this._apps_list_box.get_selected_row()
			|| !this._runtimes_list_box.get_selected_row()
		) {
			this.#select_first()
		}
	}

	@OnSignal("notify::loading")
	#on_loading_changed(): void {
		if (this.loading) return
		this._search_enty.text = ""
		this.#select_first()
		this.in_selection_mode = false
		if (this._apps_list.get_n_items() < 1 && this._runtimes_list.get_n_items() < 1) {
			this.show_filter_page = false
		}
	}

	@OnSignal("notify::show-filter-page")
	#on_show_filter_page_changed(): void {
		if (!this.show_filter_page) return
		this._split_view.show_content = true
	}

	@OnSignal("notify::in-selection-mode")
	#on_selection_mode_changed(): void {
		this.#foreach_row((row) => {
			if (!this.in_selection_mode) {
				row.selected = false
			}
			row.in_selection_mode = this.in_selection_mode
		})
		this._selection_manager.reset()
		this._apps_list_box.unselect_all()
		this._runtimes_list_box.unselect_all()
	}

	protected _should_show_bottom_bar(): boolean {
		if (this.in_selection_mode) return false
		return (this._apps_list?.get_n_items() ?? this._runtimes_list?.get_n_items() ?? 0) > 0
	}

	protected _on_row_selected(box: Gtk.ListBox, row: PackageRow | null): void {
		if (row && box === this._apps_list_box) {
			this._runtimes_list_box.unselect_all()
		} else if (row && box === this._runtimes_list_box) {
			this._apps_list_box.unselect_all()
		}
		this._details_page.flatpak = row?.flatpak ?? null
		this._details_page.pop_to_base_page()
		this.show_filter_page = false
		if (!row) return
		const maybe_viewport: Gtk.Widget | null = this._scrolled_window.get_child()
		if (!(maybe_viewport instanceof Gtk.Viewport)) return
		maybe_viewport.scroll_to(row, null)
	}

	protected _on_row_activated(__: this, _row: PackageRow | null): void {
		this._details_page.pop_to_base_page()
		this.show_filter_page = false
		if (!this.in_selection_mode) {
			this._split_view.show_content = true
		}
	}

	protected _on_app_header_clicked(): void {
		this.show_apps = !this.show_apps
	}

	protected on_runtime_header_clicked(): void {
		this.show_runtimes = !this.show_runtimes
	}

	protected _get_selection_mode(): Gtk.SelectionMode {
		return this.in_selection_mode ? Gtk.SelectionMode.NONE : Gtk.SelectionMode.SINGLE
	}

	protected _get_visible_page(
		__: this,
		loading: boolean,
		n_items: number,
	): "loading_page" | "content_page" | "no_packages_page" {
		if (loading) return "loading_page"
		if (n_items > 0) return "content_page"
		return "no_packages_page"
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _get_details_stack_page_name(): "details_page" | "filter_page" {
		return this.show_filter_page ? "filter_page" : "details_page"
	}

	protected _on_right_page_hidden(): void {
		this.show_filter_page = false
	}

	protected _on_select_all(): void {
		if (!this.in_selection_mode) return
		this.#foreach_row((row) => row.visible && (row.selected = true))
	}

	protected _on_copy_titles(): void { this.#do_copy("Copied Titles", "title") }
	protected _on_copy_ids(): void { this.#do_copy("Copied IDs", "application") }
	protected _on_copy_refs(): void { this.#do_copy("Copied Refs", "app_ref") }

	#do_copy(title: string, field: keyof Package): void {
		if (this._selection_manager.total < 1) return
		let out_arr: string[] = []
		for (const pack of this._selection_manager) {
			out_arr.push(`${pack[field]}`)
		}
		SharedVars.fancy_copy(title, out_arr.join("\n"))
	}

	protected _on_batch_uninstall(): void {
		print("not implemented yet")
	}

	protected _is_greater(__: this, a: number, b: number): boolean {
		return a > b
	}
}
