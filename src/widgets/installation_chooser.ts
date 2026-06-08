import Gio from "gi://Gio?version=2.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { Child, GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/installation_chooser.ui" })
export class InstallationChooser extends from(Adw.PreferencesGroup, {
	selected_installation: Property.readwrite.gobject(Installation),
	has_user: Property.readwrite.bool(),
	has_system: Property.readwrite.bool(),
	_extra_installations: Child<Gio.ListStore<Installation>>(),
	_user_check: Child<Gtk.CheckButton>(),
	_system_check: Child<Gtk.CheckButton>(),
	_single_check: Child<Gtk.CheckButton>(),
	_multi_check: Child<Gtk.CheckButton>(),
	_single_extra_row: Child<Adw.ActionRow>(),
	_multi_extra_row: Child<Adw.ComboRow>(),
}) {
	#checks_to_insts = new Map<Gtk.CheckButton, () => Installation>()

	constructor(
		params: { installations?: Generator<Installation, void, undefined> } & typeof InstallationChooser.$params,
	) {
		const { installations, ...base_params } = params
		super(base_params)
		if (installations) {
			this.set_installations(installations)
		}
	}

	set_installations(installations: Generator<Installation, void, undefined>): void {
		this._extra_installations.remove_all()
		this.#checks_to_insts.clear()
		this.has_user = false
		this.has_system = false
		for (const inst of installations) {
			if (inst.location_tag === "user") {
				this.#checks_to_insts.set(this._user_check, () => inst)
				this.has_user = true
			} else if (inst.location_tag === "system") {
				this.#checks_to_insts.set(this._system_check, () => inst)
				this.has_system = true
			} else {
				this._extra_installations.append(inst)
			}
		}
		const first = this._extra_installations.get_item(0)
		if (first) {
			this.#checks_to_insts.set(this._single_check, () => first)
			this._single_extra_row.title = first.title
		}
		this.#checks_to_insts.set(this._multi_check, () => this._multi_extra_row.get_selected_item<Installation>())
		this.#select_first()
	}

	#select_first(): void {
		for (let i = 0, row: Gtk.Widget | null; (row = this.get_row(i)) !== null; i += 1) {
			if (row.visible) {
				row.activate()
				return
			}
		}
	}

	protected _on_selected(check: Gtk.CheckButton): void {
		if (!check.active) return
		this.selected_installation = this.#checks_to_insts.get(check)?.() ?? null
	}

	protected _on_mutli_selected_item_changed(): void {
		this.selected_installation = this._multi_extra_row.get_selected_item<Installation>()
	}

	protected _on_multi_row_css_change(): void { this._multi_check.activate() }
	protected _greater_than(__: this, a: number, b: number): boolean { return a > b }
	protected _equals(__: this, a: unknown, b: unknown): boolean { return a === b }
}
