import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"
import Pango from "gi://Pango?version=1.0"

import { GClass, Child, Property, from, Debounce } from "../gobjectify/gobjectify.js"
import { Installation, Package, Remote, get_installations } from "../flatpak.js"
import { SidebarRow } from "./sidebar_row.js"
import { BasePage } from "../widgets/base_page.js"
import { SharedVars } from "../utils/shared_vars.js"

import "../packages_page/packages_page.js"
import "../remotes_page/remotes_page.js"
import "../data_page/data_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/window/main_window.ui" })
export class MainWindow extends from(Adw.ApplicationWindow, {
	_installations: Child<Gio.ListStore<Installation>>(),

	_only_remotes_filter: Child<Gtk.CustomFilter>(),
	_map_remotes_model: Child<Gtk.MapListModel>(),

	_only_packages_filter: Child<Gtk.CustomFilter>(),
	_map_packages_model: Child<Gtk.MapListModel>(),

	_toast_overlay: Child<Adw.ToastOverlay>(),
	_sidebar_list: Child<Gtk.ListBox>(),
	_view_stack: Child<Adw.ViewStack>(),
}) {
	readonly #settings = new Gio.Settings({ schema_id: pkg.app_id })
	#custom_inst_watcher: Gio.FileMonitor | null = null

	async _ready(): Promise<void> {
		if (pkg.profile === "development") this.add_css_class("devel")
		print(`Welcome to ${pkg.app_id}!`)

		this._only_remotes_filter.set_filter_func((item) => item instanceof Remote)
		this._map_remotes_model.set_map_func((item) => {
			if (!(item instanceof Installation)) return item
			return item.remotes
		})

		this._only_packages_filter.set_filter_func((item) => item instanceof Package)
		this._map_packages_model.set_map_func((item) => {
			if (!(item instanceof Installation)) return item
			return item.packages
		})

		this.#setup_sidebar()
		await this.#load_installations()

		if (SharedVars.CUSTOM_INSTALLATIONS_DIR.query_exists(null)) {
			this.#custom_inst_watcher = SharedVars.CUSTOM_INSTALLATIONS_DIR.monitor_directory(
				Gio.FileMonitorFlags.NONE,
				null,
			)
			this.#custom_inst_watcher.connect("changed", () => this.#refresh())
		}
	}

	add_toast(title: string, params?: { button_label: string, on_clicked: () => void }): void {
		const toast = new Adw.Toast({ title })
		if (params) {
			toast.button_label = params.button_label
			toast.connect("button-clicked", params.on_clicked)
		}
		this._toast_overlay.add_toast(toast)
	}

	add_error_toast(title: string, message: string): void {
		const label = new Gtk.Label({
			selectable: true,
			wrap: true,
			wrap_mode: Pango.WrapMode.WORD_CHAR,
		})
		label.set_markup(`<tt>${message.markup_escape_text()}</tt>`)
		const error_dialog = new Adw.AlertDialog({
			heading: title,
			extra_child: label,
		})
		error_dialog.add_response("copy", _("Copy"))
		error_dialog.add_response("ok", _("OK"))
		error_dialog.connect("response", (__, response) => {
			if (response !== "copy") return
			SharedVars.clipboard.set(message)
		})
		this.add_toast(title, { button_label: _("Details"), on_clicked: () => error_dialog.present(this) })
		print("==== Error Toast ====")
		print(title)
		print(message)
		print("=====================")
	}

	async #load_installations(): Promise<void> {
		await get_installations(this._installations)
		for (const inst of this._installations) {
			await inst.load_remotes()
			await inst.load_packages()
		}
	}

	@Debounce(200)
	#refresh(): void {
		this.#load_installations().catch((err) => {
			this.add_error_toast(_("Could not load packages"), `${err}`)
		})
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
		this._sidebar_list.select_row(this._sidebar_list.get_row_at_index(0))
	}

	@Debounce(10)
	protected _on_row_chosen(__: Gtk.ListBox, selected_row: Gtk.ListBoxRow): void {
		for (let i = 0; ; i += 1) {
			const row = this._sidebar_list.get_row_at_index(i)
			if (!row) break
			if (row === selected_row) {
				this._view_stack.pages.select_item(i, true)
				break
			}
		}
		this._view_stack.child_focus(Gtk.DirectionType.RIGHT)
	}
}
