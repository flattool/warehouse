import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, Child, from, OnSignal, next_idle, Debounce, timeout_ms } from "../gobjectify/gobjectify.js"
import { Installation, Remote } from "../flatpak.js"
import { RemoteRow } from "./remote_row.js"
import { BasePage } from "../widgets/base_page.js"
import { type PopularRemote, popular_remotes } from "../popular_remotes.js"

import "../widgets/loading_group.js"
import "../widgets/search_button.js"
import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remotes_page.ui" })
export class RemotesPage extends from(BasePage, {
	search_text: Property.string(),
	show_disabled: Property.bool(),
	is_loading: Property.bool(),
	no_results: Property.bool(),
	none_enabled: Property.bool(),
	none_disabled: Property.bool(),
	_search_filter: Child<Gtk.EveryFilter>(),
	_enabled_filter: Child<Gtk.CustomFilter>(),
	_remotes_list: Child<Gio.ListModel<Remote>>(),
	_only_remotes_filter: Child<Gtk.CustomFilter>(),
	_map_model: Child<Gtk.MapListModel<Gio.ListStore<Remote>>>(),
	_current_group: Child<Adw.PreferencesGroup>(),
	_popular_remotes_group: Child<Adw.PreferencesGroup>(),
	_empty_row: Child<Adw.ActionRow>(),
	_none_enabled_row: Child<Adw.ActionRow>(),
}) implements BasePage {
	async _ready(): Promise<void> {
		for (const popular of popular_remotes) {
			const row = new Adw.ActionRow({
				title: popular.title,
				subtitle: popular.description,
				activatable: true,
			})
			row.add_suffix(Gtk.Image.new_from_icon_name("warehouse:plus-large-symbolic"))
			row.connect("activated", () => {
				print(popular.name, popular.link)
			})
			this._popular_remotes_group.add(row)
		}
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
			this.#all_after_list_change()
		}
		this._current_group.add(this._empty_row)
		this._current_group.add(this._none_enabled_row)
	}

	@OnSignal("notify::show-disabled")
	@OnSignal("notify::search-text")
	async #do_search(): Promise<void> {
		let any_results = false
		let total_enabled = 0
		for (let i = 0; ; i += 1) {
			await next_idle()
			const row: Gtk.Widget | null = this._current_group.get_row(i)
			if (!row) break
			if (!(row instanceof RemoteRow) || !row.remote) continue
			const remote: Remote = row.remote
			if (!remote.disabled) {
				total_enabled += 1
			}
			if (this._search_filter.match(remote)) {
				any_results = true
				row.visible = true
			} else {
				row.visible = false
			}
		}
		this.none_enabled = total_enabled === 0
		this.none_disabled = total_enabled === this._remotes_list.get_n_items()
		this.no_results = !any_results && this.search_text !== ""
	}

	#all_after_list_change(): void {
		if (this._remotes_list.get_n_items() === 0) {
			this.none_enabled = true
			this.none_disabled = true
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

	protected _add_repo_file(): void {
		print("add repo file")
	}
	protected _add_custom_remote(): void {
		print("add custom remote")
	}

	protected _has_remotes(__: this, n_items: number): boolean {
		return n_items > 0
	}

	protected _has_no_remotes(__: this, n_items: number): boolean {
		return n_items === 0
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _get_disabled_button_icon(): string {
		return this.show_disabled ? "warehouse:eye-open-negative-filled-symbolic" : "warehouse:eye-not-looking-symbolic"
	}

	protected _get_none_enabled_row_visible(__: this, none_enabled: boolean, show_disabled: boolean): boolean {
		return none_enabled && !show_disabled
	}
}
