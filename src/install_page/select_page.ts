import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"
import GObject from "gi://GObject?version=2.0"

import { Child, from, GClass, Property, WatchProp } from "../gobjectify/gobjectify.js"
import { Installation, Remote, search_packages } from "../flatpak.js"
import { ArrayStore } from "../utils/array_store.js"
import { make_signal_factory } from "../utils/helper_funcs.js"
import { SelectableRemote, SelectableRemoteBox } from "./selectable_remote.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/select_page.ui" })
export class SelectPage extends from(Adw.Bin, {
	remotes: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	selected_remote: Property.readwrite.gobject(SelectableRemote),
	_selectable_remotes: Child<Gtk.MapListModel<SelectableRemote>>(),
	_search_entry: Child<Gtk.SearchEntry>(),
	_remote_dropdown: Child<Gtk.DropDown>(),
}) {
	constructor(params?: typeof SelectPage.$params) {
		super(params)
		this._selectable_remotes.set_map_func((item) => new SelectableRemote({ remote: item as Remote }))
		this._remote_dropdown.list_factory = make_signal_factory(SelectableRemoteBox, SelectableRemote, {
			setup: () => new SelectableRemoteBox(),
			bind: (box, remote) => box.remote = remote,
			unbind: (box) => box.remote = null,
		})
	}

	protected async _do_test(): Promise<void> {
		const search = this._search_entry.get_text().trim()
		if (!search) return
		const inst = this.selected_remote?.remote?.installation
		if (!inst) return
		const remote_name = this.selected_remote?.remote?.name
		try {
			for (const result of await search_packages(search, inst, remote_name)) {
				print(result.name)
			}
		} catch (e) {
			print(e instanceof Error ? e.message : e)
		}
	}

	protected _remote_selected(): void {
		if (this.selected_remote) {
			this.selected_remote.selected = false
		}
		this.selected_remote = this._remote_dropdown.selected_item as SelectableRemote | null
		if (this.selected_remote) {
			this.selected_remote.selected = true
		}
	}
}
