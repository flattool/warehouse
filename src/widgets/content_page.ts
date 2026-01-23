import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"

@GClass()
export class ContentPage extends from(Adw.Bin, {
	title: Property.string(),
	icon: Property.string(),
	installations: Property.gobject(Gio.ListStore, { flags: "CONSTRUCT_ONLY" }).as<Gio.ListStore<Installation>>(),
}) {}
