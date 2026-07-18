import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"
import GObject from "gi://GObject?version=2.0"

import { Child, from, GClass, Property, WatchProp } from "../gobjectify/gobjectify.js"
import { Installation, Remote } from "../flatpak.js"
import { ArrayStore } from "../utils/array_store.js"
import { make_signal_factory } from "../utils/helper_funcs.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/select_page.ui" })
export class SelectPage extends from(Adw.Bin, {
	remotes: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	_remote_dropdown: Child<Gtk.DropDown>(),
}) {
	constructor(params?: typeof SelectPage.$params) {
		super(params)
		this._remote_dropdown.list_factory = make_signal_factory(FilterableRemote, Remote, {
			setup: () => new FilterableRemote(),
			bind: (filterable, remote) => filterable.remote = remote,
			unbind: (filterable) => filterable.remote = null,
		})
	}
}

@GClass() class FilterableRemote extends from(Gtk.Box, {
	remote: Property.readwrite.gobject(Remote),
}) {
	#title_label = new Gtk.Label({ hexpand: true, halign: Gtk.Align.START })
	#inst_label = new Gtk.Label({ hexpand: true, halign: Gtk.Align.START })
	#name_label = new Gtk.Label({ hexpand: true, halign: Gtk.Align.END })

	constructor(params?: typeof FilterableRemote.$params) {
		super(params)
		const left_box = new Gtk.Box({ hexpand: true, orientation: Gtk.Orientation.VERTICAL })
		left_box.append(this.#title_label)
		left_box.append(this.#inst_label)
		this.append(left_box)
		this.append(this.#name_label)
	}

	@WatchProp("remote")
	#on_remote_changed(): void {
		this.#title_label.label = this.remote?.title ?? ""
		this.#inst_label.label = this.remote?.installation?.title ?? ""
		this.#name_label.label = this.remote?.name ?? ""
	}
}
