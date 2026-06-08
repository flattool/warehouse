import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"
import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, Child, from } from "../gobjectify/gobjectify.js"
import { Installation, Package, Remote } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/filter_page.ui" })
export class FilterPage extends from(Adw.NavigationPage, {
	remotes: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	runtimes: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Package>>(),
	installations: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Installation>>(),
	_remote_group: Child<Adw.PreferencesGroup>(),
	_runtime_group: Child<Adw.PreferencesGroup>(),
	_installations_group: Child<Adw.PreferencesGroup>(),
}) {
	constructor(params?: typeof FilterPage.$params) {
		super(params)

		this._remote_group.bind_model(this.remotes, (item) => {
			const remote = item as Remote
			const check = new Gtk.CheckButton()
			const row = new Adw.ActionRow({
				title: remote.title,
				subtitle: _("Installation: %s").format(remote.installation!.title),
				activatable_widget: check,
				activatable: true,
			})
			row.add_suffix(check)
			return row
		})

		this._runtime_group.bind_model(this.runtimes, (item) => {
			const runtime = item as Package
			const check = new Gtk.CheckButton()
			const row = new Adw.ActionRow({
				title: runtime.title,
				subtitle: runtime.app_ref,
				activatable_widget: check,
				activatable: true,
			})
			row.add_suffix(check)
			return row
		})

		this._installations_group.bind_model(this.installations, (item) => {
			const installation = item as Installation
			const check = new Gtk.CheckButton()
			const row = new Adw.ActionRow({
				title: installation.title,
				subtitle: installation.location_path,
				activatable_widget: check,
				activatable: true,
			})
			row.add_suffix(check)
			return row
		})
	}
}
