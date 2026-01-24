import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Remote } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remote_row.ui" })
export class RemoteRow extends from(Adw.ActionRow, {
	remote: Property.gobject(Remote, { flags: "CONSTRUCT" }),
}) {
	protected _get_subtitle(__: this, inst_title: string): string {
		return _("Installation: %s").format(inst_title)
	}
}
