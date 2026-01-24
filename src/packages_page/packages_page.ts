import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"
import type { BasePage } from "../widgets/base_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends from(Adw.NavigationPage, {
	installations: Property.gobject(Gio.ListStore, { flags: "CONSTRUCT_ONLY" }).as<Gio.ListStore<Installation>>(),
	sidebar_title: Property.string(),
	icon_name: Property.string(),
}) implements BasePage {}
