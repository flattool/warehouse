import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import GObject from "gi://GObject?version=2.0"

import { GClass, Property, Child, Signal, from } from "../gobjectify/gobjectify.js"
import { Installation, type CustomInstallationCreationConfig } from "../flatpak.js"

const TITLE_REGEX = /^[^\n"'=/\\]+$/
const NAME_REGEX = /^(?!user|system)([a-zA-Z0-9_-]+)$/i
const NAME_REPLACEMENT_REGEX = /[^a-zA-Z0-9_-]/g
const PATH_REGEX = /^\/[^\n]*[^\s\n]$/

const Base = from(Adw.Dialog, {
	valid: Property.bool(),
	reused_name: Property.bool(),
	reused_path: Property.bool(),
	_group: Child<Gtk.ListBox>(),
	_title_row: Child<Adw.EntryRow>(),
	_name_row: Child<Adw.EntryRow>(),
	_path_row: Child<Adw.EntryRow>(),
})

@GClass({ template: "resource:///io/github/flattool/Warehouse/installations_page/create_installation_dialog.ui" })
@Signal("installation-confirmed", { param_types: [GObject.TYPE_JSOBJECT] }) // CustomInstallationCreationConfig
export class CreateInstallationDialog extends Base {
	readonly #installation_names = new Set<string>()
	readonly #installation_paths = new Set<string>()
	readonly #invalid_rows = new Set<Adw.EntryRow>([this._title_row, this._name_row, this._path_row])
	#can_replace_name = true

	constructor(params: ConstructorParameters<typeof Base>[0] & {
		installations?: Generator<Installation, void, undefined>,
	}) {
		const { installations, ...base_params } = params
		super(base_params)
		this.connect("show", () => this._title_row.grab_focus())
		if (!installations) return
		for (const inst of installations) {
			this.#installation_names.add(inst.name.toLocaleLowerCase())
			this.#installation_paths.add(inst.location_path)
		}
	}

	protected _on_cancel(): void {
		this.close()
	}

	protected _on_create(): void {
		if (!this.valid) return
		this.close()
		this.emit(
			"installation-confirmed",
			{
				title: this._title_row.text,
				name: this._name_row.text,
				location_path: this._path_row.text.normalize_path(),
			} satisfies CustomInstallationCreationConfig,
		)
	}

	protected _on_row_edited(row: Adw.EntryRow): void {
		let text: string = row.text
		let valid = false
		if (row === this._title_row) {
			valid = TITLE_REGEX.test(text)
			if (this.#can_replace_name) {
				this._name_row.text = text.toLocaleLowerCase().replace(NAME_REPLACEMENT_REGEX, "")
			}
		} else if (row === this._name_row) {
			if (this._group.get_focus_child() === row) {
				this.#can_replace_name = false
			}
			if (!text) {
				this.#can_replace_name = true
			}
			this.reused_name = this.#installation_names.has(text)
			valid = NAME_REGEX.test(text) && !this.reused_name
		} else if (row === this._path_row) {
			text = text.normalize_path()
			this.reused_path = this.#installation_paths.has(text)
			valid = PATH_REGEX.test(text) && !this.reused_path
		}
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
		this.valid = this.#invalid_rows.size === 0
	}
}
