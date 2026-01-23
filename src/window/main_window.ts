import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"

import { GClass, Child, Property, from } from "../gobjectify/gobjectify.js"
import { Installation, get_installations } from "../flatpak.js"
import { SidebarRow } from "./sidebar_row.js"
import { BasePage } from "../pages/base_page.js"

import "../pages/remotes_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/window/main_window.ui" })
export class MainWindow extends from(Adw.ApplicationWindow, {
	_installations: Child<Gio.ListStore<Installation>>(),
	_sidebar_list: Child<Gtk.ListBox>(),
	_view_stack: Child<Adw.ViewStack>(),
}) {
	readonly #settings = new Gio.Settings({ schema_id: pkg.app_id })

	async _ready(): Promise<void> {
		if (pkg.profile === "development") this.add_css_class("devel")
		print(`Welcome to ${pkg.app_id}!`)

		this.#setup_sidebar()

		await get_installations(this._installations)
		for (const inst of this._installations) {
			await inst.load_remotes()
			await inst.load_packages()
		}
	}

	#setup_sidebar(): void {
		const base_list: Gtk.SelectionModel<Adw.ViewStackPage> = this._view_stack.pages
		this._sidebar_list.bind_model(
			base_list,
			(item) => new SidebarRow({
				icon_name: ((item as Adw.ViewStackPage).child as BasePage).icon_name,
				text: ((item as Adw.ViewStackPage).child as BasePage).sidebar_title,
			}),
		)
	}

	protected _on_row_selected(__: Gtk.ListBox, selected_row: Gtk.ListBoxRow): void {
		for (let i = 0; ; i += 1) {
			switch (this._sidebar_list.get_row_at_index(i)) {
				case null: return
				case selected_row: this._view_stack.pages.select_item(i, true)
			}
		}
	}
}
