import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { Child, from, GClass, Property, WatchProp } from "../gobjectify/gobjectify.js"
import { Remote } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/select_page.ui" })
export class SelectPage extends from(Adw.Bin, {
	remotes: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	_sorted_remotes: Child<Gio.ListModel<Remote>>(),
	_remotes_group: Child<Adw.PreferencesGroup>(),
}) {
	constructor(params?: typeof SelectPage.$params) {
		super(params)
		this._remotes_group.bind_model(this._sorted_remotes, (item) => {
			const remote = item as Remote
			const row = new Adw.ActionRow({
				activatable: true,
				title: remote.title,
				subtitle: _("Installation: %s").format(remote.installation?.title ?? ""),
			})
			const suffix_label = new Gtk.Label({
				label: remote.name,
				margin_end: 6,
				wrap: true,
				wrap_mode: Gtk.WrapMode.WORD_CHAR,
				natural_wrap_mode: Gtk.NaturalWrapMode.NONE,
				halign: Gtk.Align.END,
				hexpand: true,
				justify: Gtk.Justification.RIGHT,
			})
			suffix_label.add_css_class("subtitle")
			row.add_suffix(suffix_label)
			row.add_suffix(new Gtk.Image({ icon_name: "go-next-symbolic" }))
			return row
		})
	}
}
