import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"
import GObject from "gi://GObject?version=2.0"

import { Child, GClass, Property, Signal, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"
import { InstallationChooser } from "../widgets/installation_chooser.js"
import { iterate_list_model } from "../utils/helper_funcs.js"
import { PopularRemote } from "../popular_remotes.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/add_remote_dialog.ui" })
export class AddRemoteDialog extends from(Adw.Dialog, {
	valid: Property.readwrite.bool(),
	text_valid: Property.readwrite.bool(),
	installation: Property.readwrite.gobject(Installation),
	installations: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Installation>>(),
	remote_confirmed: Signal([PopularRemote, Installation]),
	_title_row: Child<Adw.EntryRow>(),
	_name_row: Child<Adw.EntryRow>(),
	_url_row: Child<Adw.EntryRow>(),
	_chooser: Child<InstallationChooser>(),
}) {
	static new_for(installations: Gio.ListModel<Installation>, remote?: PopularRemote): AddRemoteDialog {
		const dialog = new AddRemoteDialog({ installations })
		if (remote) {
			const { info } = remote
			dialog._title_row.text = info.title
			dialog._name_row.text = info.name
			dialog._url_row.text = info.link
			dialog._title_row.editable = false
			dialog._name_row.editable = false
			dialog._url_row.editable = false
			dialog.#remote_description = info.description
		}
		return dialog
	}

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
	#remote_description: string = ""

	constructor(params: typeof AddRemoteDialog.$params) {
		super(params)
		this.connect("show", () => this._title_row.grab_focus())
		if (this.installations) {
			this._chooser.set_installations(iterate_list_model(this.installations))
		}
	}

	protected _on_cancel(): void {
		this.close()
	}

	protected _on_add(): void {
		if (!this.valid) return
		this.close()
		this.emit(
			"remote-confirmed",
			new PopularRemote({
				title: this._title_row.text,
				name: this._name_row.text,
				link: this._url_row.text,
				description: this.#remote_description,
			}),
			this.installation,
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

	protected _get_validity(__: this): boolean {
		return this.text_valid && this.installation !== null
	}
}
