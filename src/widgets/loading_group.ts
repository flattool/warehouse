import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/loading_group.ui" })
export class LoadingGroup extends from(Adw.Bin, {
	content: Property.gobject(Gtk.Widget),
	is_loading: Property.bool(),
	title: Property.string({ default: "TITLE" }),
	description: Property.string({ default: "DESCRIPTION" }),
}) {
	protected _get_visible_page(): "loading_page" | "content_page" {
		return this.is_loading ? "loading_page" : "content_page"
	}
}
