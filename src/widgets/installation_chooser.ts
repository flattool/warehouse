import Gio from "gi://Gio?version=2.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { Child, Debounce, GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/installation_chooser.ui" })
export class InstallationChooser extends from(Adw.PreferencesGroup, {
	installations: Property.gobject(Gio.ListModel, { flags: "CONSTRUCT" }).as<Gio.ListModel<Installation>>(),
	selected_installation: Property.gobject(Installation),
	has_user: Property.bool(),
	has_system: Property.bool(),
	_extra_installations: Child<Gio.ListModel<Installation>>(),
	_user_check: Child<Gtk.CheckButton>(),
	_system_check: Child<Gtk.CheckButton>(),
	_single_check: Child<Gtk.CheckButton>(),
	_multi_check: Child<Gtk.CheckButton>(),
	_single_extra_row: Child<Adw.ActionRow>(),
	_multi_extra_row: Child<Adw.ComboRow>(),
}) {
	#checks_to_insts = new Map<Gtk.CheckButton, () => Installation>()

	_ready(): void {
		if (!this.installations) throw new Error("Installation Chooser was used with a null installations list")
		this.installations.connect("items-changed", () => this.#on_items_changed())
		this.#on_items_changed()
	}

	@Debounce(100)
	#on_items_changed(): void {
		this.#checks_to_insts.clear()
		this.has_user = false
		this.has_system = false
		for (let i = 0; i < this.installations!.get_n_items(); i += 1) {
			const inst: Installation = this.installations!.get_item(i)!
			if (inst.location_tag === "user") {
				this.#checks_to_insts.set(this._user_check, () => inst)
				this.has_user = true
			} else if (inst.location_tag === "system") {
				this.#checks_to_insts.set(this._system_check, () => inst)
				this.has_system = true
			}
			if (this.has_user && this.has_system) break
		}
		this._single_extra_row.title = this._extra_installations.get_item(0)?.title ?? ""
		this.#checks_to_insts.set(this._single_check, () => this._extra_installations.get_item(0)!)
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

	protected _on_multi_row_css_change(): void { this._multi_check.activate() }
	protected _is_extra_installation(__: this, tag: Installation["location_tag"]): boolean { return tag === "other" }
	protected _greater_than(__: this, a: number, b: number): boolean { return a > b }
	protected _equals(__: this, a: unknown, b: unknown): boolean { return a === b }
}
