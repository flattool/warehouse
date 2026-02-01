import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Remote } from "../flatpak.js"
import { SharedVars } from "../utils/shared_vars.js"
import { ask_to_continue } from "../utils/helper_funcs.js"

import "../widgets/simple_menu.js"
import "../widgets/simple_menu_item.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remote_row.ui" })
export class RemoteRow extends from(Adw.ActionRow, {
	remote: Property.gobject(Remote, { flags: "CONSTRUCT" }),
	disabled: Property.bool(),
}) {
	async #set_remote_enabled(to_enable: boolean): Promise<void> {
		const err_title: string = to_enable ? _("Could not enable remote") : _("Could not disable remote")
		if (!this.remote) {
			SharedVars.main_window?.add_error_toast(err_title, "Remote is null")
			return
		}
		try {
			await this.remote.enable(to_enable)
		} catch (err) {
			SharedVars.main_window?.add_error_toast(err_title, `${err}`)
		}
	}

	protected _get_subtitle(__: this, inst_title: string): string {
		return _("Installation: %s").format(inst_title)
	}

	protected _get_disabled(): boolean {
		const ret: boolean = this.remote?.disabled ?? false
		if (ret) {
			this.add_css_class("warning")
		} else {
			this.remove_css_class("warning")
		}
		return ret
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
		this.#set_remote_enabled(true)
	}

	protected async _disable(): Promise<void> {
		const ok: boolean = await ask_to_continue(
			_("Disable %s?").format(this.remote!.title),
			_("Any installed apps from %s will stop receiving updates").format(this.remote!.title),
			_("Disable"),
			Adw.ResponseAppearance.DESTRUCTIVE,
		)
		if (ok) {
			this.#set_remote_enabled(false)
		}
	}

	protected _remove(): void {
		print("remove")
	}
}
