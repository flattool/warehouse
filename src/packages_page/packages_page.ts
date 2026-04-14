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

import "./filter_page.js"
import "../widgets/sidebar_button.js"
import "../widgets/search_group.js"
import "../widgets/search_button.js"
import "../widgets/simple_menu.js"
import "../widgets/simple_menu_item.js"

@GClass() class SelectionManager extends from(GObject.Object, {
	total: Property.uint32(),
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
	show_runtimes: Property.bool(),
	show_filter_page: Property.bool(),
	search_text: Property.string(),
	no_results: Property.bool(),
	in_selection_mode: Property.bool(),
	_sorted_packages_list: Child<Gio.ListModel<Package>>(),
	_selection_manager: Child<SelectionManager>(),
	_split_view: Child<Adw.NavigationSplitView>(),
	_search_enty: Child<Gtk.SearchEntry>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_list_box: Child<Gtk.ListBox>(),
	_details_page: Child<DetailsPage>(),
}) {
	readonly #css_provider = new Gtk.CssProvider()

	async _ready(): Promise<void> {
		Gtk.StyleContext.add_provider_for_display(
			Gdk.Display.get_default()!,
			this.#css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		this._list_box.bind_model(this._sorted_packages_list, (flatpak) => {
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
		})
	}

	override grab_focus(): boolean {
		if (!this.visible) return false
		return this._list_box.get_selected_row()?.grab_focus() || super.grab_focus()
	}

	@OnSignal("notify::search-text")
	#on_search_text_changed(): void {
		let any_matched = false
		let first_visible: PackageRow | null = null
		const search: string = this.search_text.toLocaleLowerCase()
		for (const row of this._list_box) {
			if (!(row instanceof PackageRow)) continue
			const title: string = row.title.toLocaleLowerCase()
			const subtitle: string = row.subtitle.toLocaleLowerCase()
			if (row.visible = title.includes(search) || subtitle.includes(search)) {
				any_matched = true
				if (!first_visible) {
					first_visible = row
				}
			}
		}
		this.no_results = !any_matched
		if (this.search_text !== "" || this._list_box.get_selected_row() === null) {
			this._list_box.select_row(first_visible)
		}
	}

	@OnSignal("notify::loading")
	#on_loading_changed(): void {
		if (this.loading) return
		this._search_enty.text = ""
		this._list_box.select_row(this._list_box.get_row_at_index(0))
		this.in_selection_mode = false
		if (this._sorted_packages_list.get_n_items() < 1) {
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
		for (const row of this._list_box) {
			if (!(row instanceof PackageRow)) continue
			if (!this.in_selection_mode) {
				row.selected = false
			}
			row.in_selection_mode = this.in_selection_mode
		}
		this._selection_manager.reset()
		this._list_box.unselect_all()
	}

	protected _show_package_by_runtime(__: this, is_package_runtime: boolean, show_runtimes: boolean): boolean {
		return is_package_runtime === show_runtimes
	}

	protected _get_title(__: this, show_runtimes: boolean, in_selection_mode: boolean, total_selected: number): string {
		if (in_selection_mode) return _("%s Selected").format(total_selected)
		return show_runtimes ? _("Manage Runtimes") : _("Manage Applications")
	}

	protected _get_sidebar_title(): string {
		return this.show_runtimes ? _("Runtimes") : _("Applications")
	}

	protected _get_icon_name(): string {
		return this.show_runtimes ? "warehouse:flatpak-symbolic" : "warehouse:toolbars-symbolic"
	}

	protected _should_show_bottom_bar(): boolean {
		return (!this.in_selection_mode) && (this._sorted_packages_list?.get_n_items() ?? 0) > 0
	}

	protected _on_row_selected(__: this, row: PackageRow | null): void {
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
		for (const row of this._list_box) {
			if (!(row instanceof PackageRow) || !row.visible) continue
			row.selected = true
		}
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
