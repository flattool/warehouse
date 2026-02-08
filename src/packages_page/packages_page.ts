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

		await timeout_ms(250)
		if (this._sorted_packages_list.get_n_items() === 0) {
			this.#all_after_list_change()
		}
	}

	override grab_focus(): boolean {
		this._list_box.get_row_at_index(0)?.grab_focus()
		return true
	}

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

	@Debounce(200, { trigger: "leading" })
	protected _on_list_change_start(): void {
		this.is_loading = true
	}

	@Debounce(200)
	protected async _on_list_change_finish(): Promise<void> {
		this.is_loading = true
		this._list_box.remove_all()
		for (let i = 0; i < this._sorted_packages_list.get_n_items(); i += 1) {
			await next_idle()
			const flatpak: Package = this._sorted_packages_list.get_item(i)!
			const row = new PackageRow({ flatpak })
			this._list_box.append(row)
		}
		await this.#do_search()
		await next_idle()
		this.#all_after_list_change()
	}

	protected _on_row_chosen(__: Gtk.ListBox, row: Gtk.ListBoxRow): void {
		if (!(row instanceof PackageRow)) return
		this._details_page.pop_to_base_page()
		this._details_page.flatpak = row.flatpak
		this._split_view.show_content = true
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
