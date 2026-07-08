import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation, Package, Remote } from "../flatpak.js"

@GClass()
export class BasePage extends from(Adw.NavigationPage, {
	installations: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Installation>>(),
	packages: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Package>>(),
	remotes: Property.readonly.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	sidebar_title: Property.readwrite.string(),
	icon_name: Property.readwrite.string(),
	loading: Property.readwrite.bool(true),
}) {}
