import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"

@GClass()
export class BasePage extends from(Adw.NavigationPage, {
	installations: Property.gobject(Gio.ListStore, { flags: "CONSTRUCT" }).as<Gio.ListStore<Installation>>(),
	sidebar_title: Property.string(),
	icon_name: Property.string(),
}) {}
