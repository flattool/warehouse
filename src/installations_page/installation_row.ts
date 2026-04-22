import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { Installation } from "../flatpak.js"
import { SharedVars } from "../utils/shared_vars.js"
import { LineProcess } from "../utils/cli.js"
import { ask_to_continue } from "../utils/helper_funcs.js"

import "../widgets/simple_menu.js"
import "../widgets/simple_menu_item.js"
import Gtk from "gi://Gtk?version=4.0"

@GClass({ template: "resource:///io/github/flattool/Warehouse/installations_page/installation_row.ui" })
export class InstallationRow extends from(Adw.ActionRow, {
	installation: Property.gobject(Installation),
}) {
	protected _is_other_installation(): boolean {
		return this.installation?.location_tag === "other"
	}

	protected _copy_title(): void {
		if (this.installation) {
			SharedVars.fancy_copy(_("Copied title"), this.installation.title)
		} else {
			SharedVars.main_window?.add_error_toast(_("Could not copy title"), "Installation is null")
		}
	}

	protected _copy_name(): void {
		if (this.installation) {
			SharedVars.fancy_copy(_("Copied name"), this.installation.name)
		} else {
			SharedVars.main_window?.add_error_toast(_("Could not copy name"), "Installation is null")
		}
	}

	protected _copy_path(): void {
		if (this.installation) {
			SharedVars.fancy_copy(_("Copied installation location"), this.installation.location_path)
		} else {
			SharedVars.main_window?.add_error_toast(_("Could not copy installation location"), "Installation is null")
		}
	}

	protected async _open_path(): Promise<void> {
		if (!this.installation) {
			SharedVars.main_window?.add_error_toast(_("Could not open location folder"), "Installation is null")
			return
		}
		try {
			SharedVars.main_window?.add_toast("Opening installation folder...")
			await LineProcess.run(["xdg-open", this.installation.location_path])
		} catch (e) {
			SharedVars.main_window?.add_error_toast(
				_("Could not open installation folder"),
				e instanceof Error ? e.message : `${e}`,
			)
		}
	}

	protected async _remove(): Promise<void> {
		if (!this.installation) {
			SharedVars.main_window?.add_error_toast(_("Could not remove installation"), "Installation is null")
			return
		}
		try {
			const command = ["flatpak", "list", "--all", this.installation.command_syntax]
			const result = await LineProcess.run(command, { run_on_host: true })
			if (result.stdout.length > 0) {
				const dialog = new Adw.AlertDialog({
					heading: _("Could not Remove %s").format(this.installation.title),
					// eslint-disable-next-line
					body: _("There are applications or runtimes on your system installed in this installation. This installation cannot be removed until all packages provided by it are uninstalled.")
				})
				dialog.add_response("ok", _("OK"))
				dialog.present(this)
				return
			} else {
				const check = new Gtk.CheckButton({ active: true })

				const row = new Adw.ActionRow({
					title: _("Delete '%s'").format(this.installation.location_path),
					subtitle: _("Permanently delete all metadata used by this installation."),
					activatable: true,
				})
				row.add_prefix(check)
				row.set_activatable_widget(check)

				const listbox = new Gtk.ListBox({ selection_mode: Gtk.SelectionMode.NONE })
				listbox.add_css_class("boxed-list")
				listbox.append(row)

				const should_remove: boolean = await ask_to_continue(
					_("Remove %s?").format(this.installation.title),
					_("You will no longer be able to install applications or runtimes to this installation."),
					_("Remove"),
					Adw.ResponseAppearance.DESTRUCTIVE,
					listbox,
				)
				if (!should_remove) return
				await this.installation.remove(check.active)
			}
		} catch (e) {
			SharedVars.main_window?.add_error_toast(
				_("Could not open installation folder"),
				e instanceof Error ? e.message : `${e}`,
			)
		}
	}
}
