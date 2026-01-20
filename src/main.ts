import GLib from "gi://GLib?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { GClass, SimpleAction, OnSimpleAction, from, dedent } from "./gobjectify/gobjectify.js"
import { MainWindow } from "./window/main_window.js"

@GClass({ manual_gtype_name: "Gjs_Application" })
export class Application extends from(Adw.Application, {
	_quit: SimpleAction({ accels: ["<primary>q"] }),
	about: SimpleAction(),
}) {
	#main_window?: MainWindow

	override vfunc_activate(): void {
		(this.#main_window ??= new MainWindow({ application: this })).present()
	}

	_ready(): void {
		this._quit.connect("activate", () => this.quit())
	}

	@OnSimpleAction("about")
	#about(): void {
		const gtk_version = `${Gtk.MAJOR_VERSION}.${Gtk.MINOR_VERSION}.${Gtk.MICRO_VERSION}`
		const adw_version = `${Adw.MAJOR_VERSION}.${Adw.MINOR_VERSION}.${Adw.MICRO_VERSION}`
		const os_string = `${GLib.get_os_info("NAME")} ${GLib.get_os_info("VERSION")}`
		const lang = GLib.environ_getenv(GLib.get_environ(), "LANG")
		const troubleshooting = dedent`
			OS: ${os_string}
			an-app version: ${pkg.version}
			GTK: ${gtk_version}
			libadwaita: ${adw_version}
			App ID: ${pkg.app_id}
			Profile: ${pkg.profile}
			Language: ${lang}
		`

		const dialog = Adw.AboutDialog.new_from_appdata(
			"/io/github/flattool/Warehouse/appdata",
			pkg.version.split(".dev")[0] ?? null,
		)
		dialog.version = pkg.version
		dialog.debug_info = troubleshooting
		dialog.present(this.active_window)
	}
}

export function main(argv: string[]): Promise<number> {
	const app = new Application({
		application_id: pkg.app_id,
		flags: Gio.ApplicationFlags.DEFAULT_FLAGS,
	})
	return app.runAsync(argv)
}
