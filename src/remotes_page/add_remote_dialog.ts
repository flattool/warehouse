import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { Child, GClass, OnSignal, Property, from, next_idle, timeout_ms } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"
import { InstallationChooser } from "../widgets/installation_chooser.js"
import { iterate_list_model } from "../utils/helper_funcs.js"

const Base = from(Adw.Dialog, {
	valid: Property.bool(),
	text_valid: Property.bool(),
	installation: Property.gobject(Installation),
	installations: Property.gobject(Gio.ListModel, { flags: "CONSTRUCT_ONLY" }).as<Gio.ListModel<Installation>>(),
	_box: Child<Gtk.Box>(),
	_title_row: Child<Adw.EntryRow>(),
	_name_row: Child<Adw.EntryRow>(),
	_url_row: Child<Adw.EntryRow>(),
	_chooser: Child<InstallationChooser>(),
})

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/add_remote_dialog.ui" })
export class AddRemoteDialog extends Base {
	readonly #invalid_rows = new Set<Adw.EntryRow>([
		this._title_row,
		this._name_row,
		this._url_row,
	])
	readonly #row_regexes = new Map<Adw.EntryRow, RegExp>([
		[this._title_row, /^(?=.*[A-Za-z0-9])[A-Za-z0-9._-]+( +[A-Za-z0-9._-]+)*$/],
		[this._name_row, /^[a-zA-Z0-9\-._]+$/],
		[this._url_row, /^[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;= ]+$/],
	])

	constructor(...params: ConstructorParameters<typeof Base>) {
		super(...params)
		this.connect("show", () => this._title_row.grab_focus())
		if (this.installations) {
			this._chooser.set_installations(iterate_list_model(this.installations))
		} else {
			print("No installations!!!!!")
		}
	}

	protected _on_cancel(): void {
		this.close()
	}

	protected _on_add(): void {
		print("Add not implemented yet")
	}

	protected _on_row_edited(row: Adw.EntryRow): void {
		const regex: RegExp = this.#row_regexes.get(row)!
		const text: string = row.get_text()
		if (regex.test(text)) {
			this.#invalid_rows.delete(row)
			row.remove_css_class("error")
		} else {
			this.#invalid_rows.add(row)
			if (text !== "") {
				row.add_css_class("error")
			}
		}
		this.text_valid = this.#invalid_rows.size === 0
	}

	protected _get_validity(__: this): boolean {
		return this.text_valid && this.installation !== null
	}
}
