import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gio from "gi://Gio?version=2.0"
import Pango from "gi://Pango?version=1.0"

import { GClass, Child, Property, from, Debounce } from "../gobjectify/gobjectify.js"
import { Installation, Package, Remote, get_installations } from "../flatpak.js"
import { SharedVars } from "../utils/shared_vars.js"
import { ArrayStore } from "../utils/array_store.js"
import { BasePage } from "../widgets/base_page.js"

import "../packages_page/packages_page.js"
import "../remotes_page/remotes_page.js"
import "../data_page/data_page.js"
import "../installations_page/installations_page.js"
import "../install_page/install_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/window/main_window.ui" })
export class MainWindow extends from(Adw.ApplicationWindow, {
	loading: Property.readwrite.bool(true),
	_installations: Child<ArrayStore<Installation>>(),
	_only_remotes_filter: Child<Gtk.CustomFilter>(),
	_map_remotes_model: Child<Gtk.MapListModel>(),
	_only_packages_filter: Child<Gtk.CustomFilter>(),
	_map_packages_model: Child<Gtk.MapListModel>(),
	_toast_overlay: Child<Adw.ToastOverlay>(),
	_split_view: Child<Adw.OverlaySplitView>(),
	_view_stack: Child<Adw.ViewStack>(),
}) {
	readonly #settings = new Gio.Settings({ schema_id: pkg.app_id })
	#custom_inst_watcher: Gio.FileMonitor | null = null
	#custom_inst_watcher_connection = 0
	#notify_loading_connects: number[] = []
	#installations_loading = new Set<string>()

	constructor(params?: typeof MainWindow.$params) {
		super(params)
		// if (pkg.profile === "development") this.add_css_class("devel")
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

		this.#settings.bind("window-width", this, "default-width", Gio.SettingsBindFlags.DEFAULT)
		this.#settings.bind("window-height", this, "default-height", Gio.SettingsBindFlags.DEFAULT)
		this.#settings.bind("is-maximized", this, "maximized", Gio.SettingsBindFlags.DEFAULT)
		this.#settings.bind("is-fullscreen", this, "fullscreened", Gio.SettingsBindFlags.DEFAULT)

		this.#load_installations().catch(log)
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

	#on_inst_loading_changed(inst: Installation): void {
		if (inst.loading) {
			this.#installations_loading.add(inst.location_path)
			this.loading = true
		} else {
			this.#installations_loading.delete(inst.location_path)
			this.loading = this.#installations_loading.size > 0
		}
	}

	async #load_installations(): Promise<void> {
		this.loading = true
		await get_installations(this._installations)
		try {
			const to_await: Promise<unknown>[] = []
			for (const inst of this._installations) {
				this.#notify_loading_connects.push(
					inst.connect("notify::loading", () => this.#on_inst_loading_changed(inst)),
				)
				to_await.push(Promise.all([
					inst.load_packages(),
					inst.load_remotes(),
				]))
			}
			await Promise.all(to_await)

			if (!SharedVars.CUSTOM_INSTALLATIONS_DIR.query_exists(null)) return
			this.#custom_inst_watcher = SharedVars.CUSTOM_INSTALLATIONS_DIR.monitor_directory(
				Gio.FileMonitorFlags.NONE,
				null,
			)
			this.#custom_inst_watcher_connection = this.#custom_inst_watcher.$connect("changed", () => this.refresh())
		} catch (err) {
			this.add_error_toast(_("Could not load packages"), `${err}`)
		}
		this.loading = false
	}

	@Debounce(200)
	async refresh(): Promise<void> {
		print("refreshing...")
		let i = 0
		for (const inst of this._installations) {
			inst.disconnect(this.#notify_loading_connects[i]!)
			i += 1
		}
		this.#notify_loading_connects.length = 0
		this.#custom_inst_watcher?.disconnect(this.#custom_inst_watcher_connection)
		this.#custom_inst_watcher = null
		await this.#load_installations()
	}

	protected _do_test(): void {
		this.refresh()
	}

	protected _on_row_chosen(): void {
		if (this._split_view.collapsed) {
			this._split_view.show_sidebar = false
		}
	}
}
