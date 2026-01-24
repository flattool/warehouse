import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, Child, from } from "../gobjectify/gobjectify.js"
import { Installation, Remote } from "../flatpak.js"
import type { BasePage } from "../widgets/base_page.js"

import "../widgets/loading_group.js"
import "../widgets/search_button.js"
import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remotes_page.ui" })
export class RemotesPage extends from(Adw.NavigationPage, {
	installations: Property.gobject(Gio.ListStore, { flags: "CONSTRUCT_ONLY" }).as<Gio.ListStore<Installation>>(),
	sidebar_title: Property.string(),
	icon_name: Property.string(),
	_map_model: Child<Gtk.MapListModel<Gio.ListStore<Remote>>>(),
	_current_group: Child<Adw.PreferencesGroup>(),
}) implements BasePage {
	async _ready(): Promise<void> {
		this._map_model.set_map_func((item) => {
			print(item)
			if (!(item instanceof Installation)) return item
			return item.remotes
		})
	}
}
