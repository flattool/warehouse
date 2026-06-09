import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, Child, from, OnSignal } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Installation, Remote } from "../flatpak.js"
import { RemoteRow } from "./remote_row.js"
import { AddRemoteDialog } from "./add_remote_dialog.js"
import { type PopularRemote, popular_remotes } from "../popular_remotes.js"
import { SharedVars } from "../utils/shared_vars.js"

import "../widgets/sidebar_button.js"
import "../widgets/loading_group.js"
import "../widgets/search_button.js"
import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remotes_page.ui" })
export class RemotesPage extends from(BasePage, {
	search_text: Property.readwrite.string(),
	show_disabled: Property.readwrite.bool(),
	_disabled_list: Child<Gio.ListModel>(),
	_disabled_filter: Child<Gtk.CustomFilter>(),
	_searched_list: Child<Gio.ListModel<Remote>>(),
	_current_group: Child<Adw.PreferencesGroup>(),
	_popular_remotes_group: Child<Adw.PreferencesGroup>(),
	_empty_row: Child<Adw.ActionRow>(),
	_none_enabled_row: Child<Adw.ActionRow>(),
}) {
	constructor(params?: typeof RemotesPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:server-pick-symbolic"
		params.sidebar_title = _("Remotes")
		super(params)
		for (const remote of popular_remotes) {
			const row = new Adw.ActionRow({
				title: remote.info.title,
				subtitle: remote.info.description,
				activatable: true,
			})
			row.add_suffix(Gtk.Image.new_from_icon_name("warehouse:plus-large-symbolic"))
			row.connect("activated", () => this.#add_remote_via_dialog(remote).catch(log))
			this._popular_remotes_group.add(row)
		}
		this._disabled_filter.set_filter_func((remote) => this.show_disabled || !(remote as Remote).disabled)
		this._current_group.bind_model(this._searched_list, (remote) => new RemoteRow({ remote: remote as Remote }))
	}

	@OnSignal("notify::show-disabled")
	#on_show_disabled_changed(): void {
		this._disabled_filter.changed(this.show_disabled ? Gtk.FilterChange.LESS_STRICT : Gtk.FilterChange.MORE_STRICT)
	}

	async #add_remote_via_dialog(maybe_remote?: PopularRemote): Promise<void> {
		const dialog = AddRemoteDialog.new_for(this.installations!, maybe_remote)
		dialog.present(this)
		const [remote, installation] = await dialog.$connect_async("remote-confirmed")
		this.loading = true
		try {
			await installation!.add_remote(remote!)
		} catch (e) {
			this.loading = false
			SharedVars.main_window?.add_error_toast(
				_("Could not add remote"),
				e instanceof Error ? e.message : `${e}`,
			)
		}
	}

	protected _add_repo_file(): void {
		print("add repo file")
	}

	protected _add_custom_remote(): void {
		this.#add_remote_via_dialog().catch(log)
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _get_disabled_button_icon(): string {
		return this.show_disabled ? "warehouse:eye-open-negative-filled-symbolic" : "warehouse:eye-not-looking-symbolic"
	}

	protected _get_no_results(__: this, search_text: string, total_remotes: number, total_results: number): boolean {
		if (!search_text) return false
		return total_results === 0 && total_remotes > 1
	}

	protected _show_none_enabled_row(
		__: this,
		show_disabled: boolean,
		total_remotes: number,
		total_disabled: number,
	): boolean {
		return total_remotes > 0 && total_disabled === total_remotes && !show_disabled
	}

	protected _greater(__: this, a: number, b: number): boolean { return a > b }
	protected _equals(__: this, a: unknown, b: unknown): boolean { return a === b }
	protected _or(__: this, ...test: unknown[]): boolean {
		return test.some(Boolean)
	}
}
