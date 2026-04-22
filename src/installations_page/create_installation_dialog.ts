import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, Child, Signal, from, Debounce, OnSignal } from "../gobjectify/gobjectify.js"
import { Installation, type CustomInstallationCreationConfig } from "../flatpak.js"

// TODO: ensure that name and path are unique!
@GClass({ template: "resource:///io/github/flattool/Warehouse/installations_page/create_installation_dialog.ui" })
@Signal("installation-confirmed", { param_types: [GObject.TYPE_JSOBJECT] }) // CustomInstallationCreationConfig
export class CreateInstallationDialog extends from(Adw.Dialog, {
	text_valid: Property.bool(),
	name_and_path_unique: Property.bool({ default: true }),
	installations: Property.gobject(Gio.ListModel, { flags: "CONSTRUCT_ONLY" }).as<Gio.ListModel<Installation>>(),
	_title_row: Child<Adw.EntryRow>(),
	_name_row: Child<Adw.EntryRow>(),
	_path_row: Child<Adw.EntryRow>(),
}) {
	readonly #invalid_rows = new Set<Adw.EntryRow>([this._title_row, this._name_row, this._path_row])
	readonly #row_regexes = new Map<Adw.EntryRow, RegExp>([
		[this._title_row, /^[^\n"'=]+$/],
		[this._name_row, /^(?!user|system)([a-zA-Z0-9_-]+)$/i],
		[this._path_row, /^\/[^\n]*[^\s\n]$/],
	])

	@OnSignal("show")
	#on_show(): void {
		this._title_row.grab_focus()
	}

	protected _get_validity(): boolean {
		return this.text_valid && this.name_and_path_unique
	}

	protected _on_cancel(): void {
		this.close()
	}

	protected _on_create(): void {
		if (!this._get_validity()) return
		this.close()
		this.emit(
			"installation-confirmed",
			{
				title: this._title_row.text,
				name: this._name_row.text,
				location_path: this._path_row.text,
			} satisfies CustomInstallationCreationConfig,
		)
	}

	protected _on_row_edited(row: Adw.EntryRow): void {
		const regex: RegExp = this.#row_regexes.get(row)!
		const text: string = row.get_text()
		const valid: boolean = regex.test(text)
		if (valid) {
			this.#invalid_rows.delete(row)
		} else {
			this.#invalid_rows.add(row)
		}
		if (valid || text === "") {
			row.remove_css_class("error")
		} else {
			row.add_css_class("error")
		}
		this.text_valid = this.#invalid_rows.size === 0
	}
}
