import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/search_group.ui" })
export class SearchGroup extends from(Adw.Bin, {
	content: Property.gobject(Gtk.Widget),
	no_results: Property.bool(),
}) {
	protected _get_visible_page(): "no_results_page" | "content_page" {
		return this.no_results ? "no_results_page" : "content_page"
	}
}
