import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Remote } from "../flatpak.js"
import { SharedVars } from "../utils/shared_vars.js"
import { ask_to_continue } from "../utils/helper_funcs.js"
import { LineProcess } from "../utils/cli.js"

import "../widgets/simple_menu.js"
import "../widgets/simple_menu_item.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/remotes_page/remote_row.ui" })
export class RemoteRow extends from(Adw.ActionRow, {
	remote: Property.readwrite.gobject(Remote),
	disabled: Property.readwrite.bool(),
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

	protected async _remove(): Promise<void> {
		if (!this.remote || !this.remote.installation) {
			SharedVars.main_window?.add_error_toast(_("Could not remove remote"), "Remote or its installation is null")
			return
		}
		const command: string[] = [
			"flatpak",
			"list",
			"--all",
			this.remote.installation.command_syntax,
			"--columns=origin",
		]
		try {
			const response = await LineProcess.run(command, { run_on_host: true })
			const origins: string = response.stdout.join("\n")
			if (origins.includes(this.remote.name)) {
				const dialog = new Adw.AlertDialog({
					heading: _("Could not Remove %s").format(this.remote.title),
					// eslint-disable-next-line
					body: _("There are applications or runtimes on your system installed from this remote. This remote cannot be removed until all packages provided by it are uninstalled"),
				})
				dialog.add_response("ok", _("OK"))
				dialog.present(SharedVars.main_window)
				return
			} else {
				const should_remove: boolean = await ask_to_continue(
					_("Remove %s?").format(this.remote.title),
					_("You will no longer be able to install applications or runtimes from this remote."),
					_("Remove"),
					Adw.ResponseAppearance.DESTRUCTIVE,
				)
				if (!should_remove) return
				await this.remote.remove()
			}
		} catch (e) {
			SharedVars.main_window?.add_error_toast(
				_("Could not remove remote"),
				e instanceof Error ? e.message : `${e}`,
			)
		}
	}
}
