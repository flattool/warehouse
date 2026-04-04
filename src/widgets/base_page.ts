import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation, Package, Remote } from "../flatpak.js"

@GClass()
export class BasePage extends from(Adw.NavigationPage, {
	installations: Property.gobject(Gio.ListModel, { flags: "CONSTRUCT" }).as<Gio.ListModel<Installation>>(),
	packages: Property.gobject(Gio.ListModel, { flags: "CONSTRUCT" }).as<Gio.ListModel<Package>>(),
	remotes: Property.gobject(Gio.ListModel, { flags: "CONSTRUCT" }).as<Gio.ListModel<Remote>>(),
	sidebar_title: Property.string(),
	icon_name: Property.string(),
	loading: Property.bool({ default: true }),
}) {}
