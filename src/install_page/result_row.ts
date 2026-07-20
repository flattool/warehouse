import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { Child, from, GClass, Property, WatchProp } from "../gobjectify/gobjectify.js"
import { SearchResult } from "../flatpak.js"

type RowKind = "addable" | "added" | "installed" | "removable"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/result_row.ui" })
export class ResultRow extends from(Adw.ActionRow, {
	result: Property.readonly.gobject(SearchResult),
	kind: Property.readwrite.string("addable").as<RowKind>(),
	_suffix_image: Child<Gtk.Image>(),
}) {
	protected _get_tooltip(): string {
		switch (this.kind) {
			case "addable": return _("Add Package to queue")
			case "added": return _("Package has been added to queue")
			case "installed": return _("Package is already installed")
			case "removable": return _("Remove Package from queue")
		}
	}

	protected _get_sensitivity(): boolean {
		return this.kind === "addable" || this.kind === "removable"
	}

	protected _get_icon(): string {
		switch (this.kind) {
			case "addable": return "warehouse:plus-large-symbolic"
			case "added": return "warehouse:check-plain-symbolic"
			case "installed": return "warehouse:selection-mode-symbolic"
			case "removable": return "warehouse:minus-large-symbolic"
		}
	}

	@WatchProp("kind")
	#on_kind_changed(): void {
		if (this.kind === "installed") {
			this._suffix_image.add_css_class("success")
		} else {
			this._suffix_image.remove_css_class("success")
		}
	}
}
