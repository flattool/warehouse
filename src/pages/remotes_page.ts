import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"

import { BasePage } from "./base_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/pages/remotes_page.ui" })
export class RemotesPage extends from(BasePage, {
	// installations: Property.gobject(Gio.ListStore),
}) {}
