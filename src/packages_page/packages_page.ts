import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { GClass, Debounce, Child, Property, from, timeout_ms, OnSignal, next_idle } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Installation, Package } from "../flatpak.js"
import { PackageRow } from "./package_row.js"
import { DetailsPage } from "./details_page.js"

import "./filter_page.js"
import "../widgets/sidebar_button.js"
import "../widgets/search_group.js"
import "../widgets/search_button.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends from(BasePage, {
	is_loading: Property.bool(),
	search_text: Property.string(),
	no_results: Property.bool(),
	_bottom_sheet: Child<Adw.BottomSheet>(),
	_split_view: Child<Adw.NavigationSplitView>(),
	_sorted_packages_list: Child<Gio.ListModel<Package>>(),
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

		await timeout_ms(250)
		if (this._sorted_packages_list.get_n_items() === 0) {
			this.#all_after_list_change()
		}
	}

	// override grab_focus(): boolean {
	// 	this._list_box.get_row_at_index(0)?.grab_focus()
	// 	return true
	// }

	@OnSignal("notify::search-text")
	async #do_search(): Promise<void> {
		print("doing search")
	}

	#all_after_list_change(): void {
		this.is_loading = false
	}

	#load_scrollbar_css(): void {
		this.#css_provider.load_from_data(`
			.scrollbar-offset scrollbar {
				margin-bottom: ${this._bottom_sheet.bottom_bar_height}px;
			}
		`, -1)
	}

	protected _get_visible_page(__: this, is_loading: boolean): "loading_page" | "content_page" {
		return is_loading ? "loading_page" : "content_page"
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _has_any_packages(__: this, n_items: number): boolean {
		return n_items > 0
	}
}
