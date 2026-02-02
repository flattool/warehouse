import Adw from "gi://Adw?version=1"
import GObject from "gi://GObject?version=2.0"

import { GClass, OnSignal, Property, from } from "../gobjectify/gobjectify.js"
import { SharedVars } from "../utils/shared_vars.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/info_row.ui" })
export class InfoRow extends from(Adw.ActionRow, {
	info: Property.string(),
	always_visible: Property.bool(),
}) {
	_on_activated(): void {
		SharedVars.fancy_copy(_("Copied %s").format(this.title), this.info)
	}

	protected _should_be_visible(__: this, always_visible: boolean, info: string): boolean {
		return always_visible || Boolean(info)
	}

	protected _markup_escape(__: this, text: string): string {
		return text.markup_escape_text()
	}
}
