import Gio from "gi://Gio?version=2.0"
import Adw from "gi://Adw?version=1"

import { GClass } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/window/main_window.ui" })
export class MainWindow extends Adw.ApplicationWindow {
	readonly #settings = new Gio.Settings({ schema_id: pkg.app_id })

	_ready(): void {
		if (pkg.profile === "development") this.add_css_class("devel")
		print(`Welcome to ${pkg.app_id}!`)
	}
}
