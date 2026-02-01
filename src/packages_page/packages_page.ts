import Gio from "gi://Gio?version=2.0"
import type Gtk from "gi://Gtk?version=4.0"

import { GClass, Debounce, Child, Property, from, timeout_ms, OnSignal, next_idle } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Installation, Package } from "../flatpak.js"
import { PackageRow } from "./package_row.js"
import { DetailsPage } from "./details_page.js"

import "../widgets/search_group.js"
import "../widgets/search_button.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends from(BasePage, {
	is_loading: Property.bool(),
	search_text: Property.string(),
	no_results: Property.bool(),
	_packages_list: Child<Gio.ListModel<Package>>(),
	_only_packages_filter: Child<Gtk.CustomFilter>(),
	_map_model: Child<Gtk.MapListModel<Gio.ListStore<Installation>>>(),
	_list_box: Child<Gtk.ListBox>(),
	_details_page: Child<DetailsPage>(),
}) {
	async _ready(): Promise<void> {
		this._only_packages_filter.set_filter_func((item) => item instanceof Package)
		this._map_model.set_map_func((item) => {
			if (!(item instanceof Installation)) return item
			return item.packages
		})
		await timeout_ms(250)
		if (this._packages_list.get_n_items() === 0) {
			this.#all_after_list_change()
		}
	}

	@OnSignal("notify::search-text")
	async #do_search(): Promise<void> {
		print("doing search")
	}

	#all_after_list_change(): void {
		this.is_loading = false
	}

	@Debounce(200, { trigger: "leading" })
	protected _on_list_change_start(): void {
		this.is_loading = true
	}

	@Debounce(200)
	protected async _on_list_change_finish(): Promise<void> {
		this.is_loading = true
		this._list_box.remove_all()
		for (let i = 0; i < this._packages_list.get_n_items(); i += 1) {
			await next_idle()
			const flatpak: Package = this._packages_list.get_item(i)!
			const row = new PackageRow({ flatpak })
			this._list_box.append(row)
		}
		await this.#do_search()
		await next_idle()
		this.#all_after_list_change()
	}

	protected _on_row_activated(__: Gtk.ListBox, row: Gtk.ListBoxRow): void {
		if (!(row instanceof PackageRow)) return
		this._details_page.flatpak = row.flatpak
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
