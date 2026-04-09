import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { GClass, Child, Property, from, OnSignal, Debounce, next_idle } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Package } from "../flatpak.js"
import { PackageRow } from "./package_row.js"
import { DetailsPage } from "./details_page.js"

import "./filter_page.js"
import "../widgets/sidebar_button.js"
import "../widgets/search_group.js"
import "../widgets/search_button.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends from(BasePage, {
	search_text: Property.string(),
	no_results: Property.bool(),
	_filtered_packages_list: Child<Gio.ListModel<Package>>(),
	// _sorted_packages_list: Child<Gio.ListModel<Package>>(),
	_bottom_sheet: Child<Adw.BottomSheet>(),
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
		this.#load_scrollbar_css()
		this._bottom_sheet.connect("notify::bottom-bar-height", () => this.#load_scrollbar_css())
		this._list_box.bind_model(this._filtered_packages_list, (flatpak) => new PackageRow({ flatpak }))
	}

	override grab_focus(): boolean {
		if (!this.visible) return false
		return this._list_box.get_selected_row()?.grab_focus() || super.grab_focus()
	}

	@OnSignal("notify::loading")
	#on_loading_changed(): void {
		if (this.loading) {
			this._search_enty.text = ""
		} else {
			this._list_box.select_row(this._list_box.get_row_at_index(0))
		}
	}

	#load_scrollbar_css(): void {
		this.#css_provider.load_from_data(`
			.scrollbar-offset scrollbar {
				margin-bottom: ${this._bottom_sheet.bottom_bar_height}px;
			}
		`, -1)
	}

	protected _on_row_selected(__: this, row: PackageRow | null): void {
		this._details_page.flatpak = row?.flatpak ?? null
		if (!row) return
		const maybe_viewport: Gtk.Widget | null = this._scrolled_window.get_child()
		if (!(maybe_viewport instanceof Gtk.Viewport)) return
		maybe_viewport.scroll_to(row, null)
	}

	protected _on_row_activated(__: this, _row: PackageRow | null): void {
		this._split_view.show_content = true
	}

	protected _get_visible_page(__: this): "loading_page" | "content_page" {
		return this.loading ? "loading_page" : "content_page"
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _has_any_packages(__: this, n_items: number): boolean {
		return n_items > 0
	}

	protected _has_no_packages(__: this, n_items: number): boolean {
		return n_items <= 0
	}
}
