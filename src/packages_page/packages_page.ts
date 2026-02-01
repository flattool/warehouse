import Gio from "gi://Gio?version=2.0"
import type Gtk from "gi://Gtk?version=4.0"

import { GClass, Debounce, Child, Property, from, timeout_ms, OnSignal, next_idle } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Installation, Package } from "../flatpak.js"

import "../widgets/search_group.js"
import "../widgets/search_button.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends from(BasePage, {
	is_loading: Property.bool(),
	search_text: Property.string(),
	no_packages: Property.bool(),
	no_results: Property.bool(),
	_packages_list: Child<Gio.ListModel<Package>>(),
	_only_packages_filter: Child<Gtk.CustomFilter>(),
	_map_model: Child<Gtk.MapListModel<Gio.ListStore<Installation>>>(),
	_list_box: Child<Gtk.ListBox>(),
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
		for (let i = 0; i < this._packages_list.get_n_items(); i += 1) {
			const flat_package = this._packages_list.get_item(i)!
			print(flat_package.title, flat_package.origin)
		}
	}

	#all_after_list_change(): void {
		if (this._packages_list.get_n_items() === 0) {
			this.no_packages = true
		}
		this.is_loading = false
	}

	@Debounce(200, { trigger: "leading" })
	protected _on_list_change_start(): void {
		this.is_loading = true
	}

	@Debounce(200)
	protected _on_list_change_finish(): void {
		this.#do_search().then(() => this.#all_after_list_change())
	}

	protected _get_visible_page(__: this, is_loading: boolean): "loading_page" | "content_page" {
		return is_loading ? "loading_page" : "content_page"
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}
}
