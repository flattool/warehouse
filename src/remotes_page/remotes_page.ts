import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, Child, from } from "../gobjectify/gobjectify.js"
import { Installation, Remote } from "../flatpak.js"
import { RemoteRow } from "./remote_row.js"
import { BasePage } from "../widgets/base_page.js"

import "../widgets/loading_group.js"
import "../widgets/search_button.js"
import "../widgets/search_group.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remotes_page.ui" })
export class RemotesPage extends from(BasePage, {
	_remotes_list: Child<Gio.ListModel<Remote>>(),
	_only_remotes_filter: Child<Gtk.CustomFilter>(),
	_map_model: Child<Gtk.MapListModel<Gio.ListStore<Remote>>>(),
	_current_group: Child<Adw.PreferencesGroup>(),
}) implements BasePage {
	_ready(): void {
		this._only_remotes_filter.set_filter_func((item) => item instanceof Remote)
		this._map_model.set_map_func((item) => {
			if (!(item instanceof Installation)) return item
			return item.remotes
		})
		this._current_group.bind_model(this._remotes_list, (remote) => new RemoteRow({ remote: remote as Remote }))
	}
}
