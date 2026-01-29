import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, Child, from, OnSignal, next_idle, Debounce, timeout_ms } from "../gobjectify/gobjectify.js"
import { Installation, Remote } from "../flatpak.js"
import { RemoteRow } from "./remote_row.js"
import { BasePage } from "../widgets/base_page.js"

import "../widgets/loading_group.js"
import "../widgets/search_button.js"
import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remotes_page.ui" })
export class RemotesPage extends from(BasePage, {
	search_text: Property.string(),
	show_disabled: Property.bool(),
	is_loading: Property.bool(),
	no_results: Property.bool(),
	_search_filter: Child<Gtk.EveryFilter>(),
	_enabled_filter: Child<Gtk.CustomFilter>(),
	_remotes_list: Child<Gio.ListModel<Remote>>(),
	_only_remotes_filter: Child<Gtk.CustomFilter>(),
	_map_model: Child<Gtk.MapListModel<Gio.ListStore<Remote>>>(),
	_current_group: Child<Adw.PreferencesGroup>(),
}) implements BasePage {
	async _ready(): Promise<void> {
		this._only_remotes_filter.set_filter_func((item) => item instanceof Remote)
		this._map_model.set_map_func((item) => {
			if (!(item instanceof Installation)) return item
			return item.remotes
		})
		this._current_group.bind_model(this._remotes_list, (remote) => new RemoteRow({ remote: remote as Remote }))
		this._enabled_filter.set_filter_func((item) => {
			const remote = item as Remote
			if (this.show_disabled) return true
			return !remote.disabled
		})
		await timeout_ms(250)
		if (this._remotes_list.get_n_items() === 0) {
			this.is_loading = false
		}
	}

	@OnSignal("notify::show-disabled")
	@OnSignal("notify::search-text")
	async #do_search(): Promise<void> {
		let any_results = false
		for (let i = 0; ; i += 1) {
			await next_idle()
			const row: Gtk.Widget | null = this._current_group.get_row(i)
			if (!row) break
			if (!(row instanceof RemoteRow) || !row.remote) continue
			const remote: Remote = row.remote
			if (this._search_filter.match(remote)) {
				any_results = true
				row.visible = true
			} else {
				row.visible = false
			}
		}
		this.no_results = !any_results
	}

	@Debounce(200, { trigger: "leading" })
	protected _on_list_change_start(): void {
		this.is_loading = true
	}

	@Debounce(200)
	protected _on_list_change_finish(): void {
		this.#do_search().then(() => this.is_loading = false)
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _get_disabled_button_icon(): string {
		return this.show_disabled ? "warehouse:eye-open-negative-filled-symbolic" : "warehouse:eye-not-looking-symbolic"
	}
}
