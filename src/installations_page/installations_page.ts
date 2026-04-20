import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Child, Property, from } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { Installation } from "../flatpak.js"
import { InstallationRow } from "../installations_page/installation_row.js"

import "../widgets/sidebar_button.js"
import "../widgets/loading_group.js"
import "../widgets/search_button.js"
import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/installations_page/installations_page.ui" })
export class InstallationsPage extends from(BasePage, {
	search_text: Property.string(),
	_ui_installations: Child<Gio.ListModel<Installation>>(),
	_installation_tag_sorter: Child<Gtk.CustomSorter>(),
	_inst_group: Child<Adw.PreferencesGroup>(),
}) {
	_ready(): void {
		this._installation_tag_sorter.set_sort_func((a: Installation, b: Installation) => {
			if (a.location_tag === b.location_tag) return 0 // same
			if (a.location_tag === "other") return 1 // a should come after
			return -1 // a should come before
		})
		this._inst_group.bind_model(
			this._ui_installations,
			(inst) => new InstallationRow({ installation: inst as Installation }),
		)
	}

	protected _on_search_changed(entry: Gtk.SearchEntry): void {
		this.search_text = entry.text
	}

	protected _get_visible_page_name(__: this, total_insts: number): "no_installations_page" | "content_page" {
		return total_insts > 0 ? "content_page" : "no_installations_page"
	}

	protected _greater_than(__: this, a: number, b: number): boolean { return a > b }
	protected _is_equal(__: this, a: unknown, b: unknown): boolean { return a === b }
}
