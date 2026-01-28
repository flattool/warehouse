import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Remote } from "../flatpak.js"
import { SharedVars } from "../utils/shared_vars.js"

import "../widgets/simple_menu.js"
import "../widgets/simple_menu_item.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remote_row.ui" })
export class RemoteRow extends from(Adw.ActionRow, {
	remote: Property.gobject(Remote, { flags: "CONSTRUCT" }),
}) {
	protected _get_subtitle(__: this, inst_title: string): string {
		return _("Installation: %s").format(inst_title)
	}

	protected _copy_title(): void {
		if (this.remote) {
			const title: string = this.remote.title
			SharedVars.fancy_copy(_("Copied %s").format(title), title)
		} else {
			SharedVars.main_window?.add_error_toast(_("Could not copy title"), "Remote is null")
		}
	}

	protected _copy_name(): void {
		if (this.remote) {
			const name: string = this.remote.name
			SharedVars.fancy_copy(_("Copied %s").format(name), name)
		} else {
			SharedVars.main_window?.add_error_toast(_("Could not copy name"), "Remote is null")
		}
	}

	protected async _enable(): Promise<void> {
		if (!this.remote) {
			SharedVars.main_window?.add_error_toast(_("Could not enable remote"), "Remote is null")
			return
		}
		try {
			await this.remote.enable(true)
		} catch (error) {
			SharedVars.main_window?.add_error_toast(_("Could not enable remote"), `${error}`)
		}
	}

	protected async _disable(): Promise<void> {
		if (!this.remote) {
			SharedVars.main_window?.add_error_toast(_("Could not enable remote"), "Remote is null")
			return
		}
		try {
			await this.remote.enable(false)
		} catch (error) {
			SharedVars.main_window?.add_error_toast(_("Could not enable remote"), `${error}`)
		}
	}

	protected _remove(): void {
		print("remove")
	}
}
