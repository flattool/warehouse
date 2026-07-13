import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"
import Adw from "gi://Adw?version=1"
import Graphene from "gi://Graphene?version=1.0"

import { GClass, WatchProp, Property, from, Child, next_idle } from "../gobjectify/gobjectify.js"
import { ask_to_continue, get_readable_byte_size, trash_fallback_delete } from "../utils/helper_funcs.js"
import { DataPage } from "./data_page.js"
import { SharedVars } from "../utils/shared_vars.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_box.ui" })
export class DataBox extends from(Adw.Bin, {
	title: Property.readwrite.string(),
	subtitle: Property.readwrite.string(),
	selection_mode_enabled: Property.readwrite.bool(),
	is_selected: Property.readwrite.bool(),
	app_id: Property.readonly.string(),
	folder: Property.readonly.gobject(Gio.File),
	size: Property.readwrite.double(-1),
	is_leftover: Property.readonly.bool(),
	is_warehouse: Property.readwrite.bool(),
	_overlay: Child<Gtk.Overlay>(),
	_content_box: Child<Gtk.Box>(),
	_icon: Child<Gtk.Image>(),
	_select_button: Child<Gtk.CheckButton>(),
}) {
	readonly #click = new Gtk.GestureClick()
	readonly #long_press = new Gtk.GestureLongPress()
	#is_pressed = false

	constructor(params?: typeof DataBox.$params) {
		super(params)
		this._overlay.set_measure_overlay(this._content_box, true)
		this.add_controller(this.#click)
		this.add_controller(this.#long_press)
		this.#click.$connect("released", (_g, _n, x, y) => this.#on_clicked(x, y))
		this.#long_press.$connect("pressed", () => this.#on_pressed())
		if (!this.folder) return

		const theme = Gtk.IconTheme.get_for_display(this.get_display())
		const id = this.folder.get_basename() || ""
		this.title = id.split(".").at(-1) || ""
		this.subtitle = id
		this.is_warehouse = id === pkg.app_id

		if (theme.has_icon(id)) {
			this._icon.icon_name = id
		} else {
			this._icon.icon_name = "warehouse:flatpak-symbolic"
			return
		}
		if (this.is_leftover) {
			return
		}
		this._overlay.child = new BlurBin({
			icon_theme: theme,
			icon_name: id,
			light_opacity: 1.0,
			dark_opacity: 0.5,
			blur_px: 45,
			css_class_name: `databox-${id.replaceAll(".", "-")}`,
		})
	}

	#on_clicked(x: number, y: number): void {
		if (this.#is_pressed) { // The long_press gesture always triggers a click at the end
			this.#is_pressed = false
			return
		}
		if (!this.selection_mode_enabled || x < 0 || y < 0 || x > this.get_width() || y > this.get_height()) {
			// Only run when in selection mode, and when the click occurs within the box's bounds
			return
		}
		this.is_selected = !this.is_selected
	}

	#on_pressed(): void {
		this.#is_pressed = true
		if (this.selection_mode_enabled) {
			this.is_selected = true
		} else {
			DataPage.$actions.change_selection_mode.activate(this, true)
			next_idle().then(() => this.is_selected = true)
		}
	}

	@WatchProp("selection_mode_enabled")
	#on_selection_mode_enabled_changed(): void {
		if (this.selection_mode_enabled) {
			this.add_css_class("activatable")
		} else {
			this.remove_css_class("activatable")
			this.is_selected = false
		}
	}

	#gaurd_path(
		path: string | undefined | null,
		failure_title: string,
		callback: (path: string) => void,
	): void {
		const failure_message = "Folder path was null, undefined, or empty."
		if (path) {
			try {
				callback(path)
			} catch (e) {
				SharedVars.main_window?.add_error_toast(failure_title, e instanceof Error ? e.message : String(e))
			}
		} else {
			SharedVars.main_window?.add_error_toast(failure_title, failure_message)
		}
	}

	protected _do_copy(): void {
		this.#gaurd_path(
			this.folder?.get_path(),
			_("Could not copy path"),
			(path) => SharedVars.fancy_copy(_("Copied path"), path),
		)
	}

	protected _do_open(): void {
		this.#gaurd_path(
			this.folder?.get_path(),
			_("Could not open folder"),
			(path) => {
				SharedVars.main_window?.add_toast(_("Opening folder..."))
				try {
					Gio.AppInfo.launch_default_for_uri(`file://${path}`, null)
				} catch (e) {
					SharedVars.main_window?.add_error_toast(
						_("Could not open folder"),
						e instanceof Error ? e.message : String(e),
					)
				}
			},
		)
	}

	protected async _do_trash(): Promise<void> {
		if (!await ask_to_continue(
			_("Trash %s Data?").format(this.title),
			_("The app's data will be moved to the trash."),
			_("Trash"),
			Adw.ResponseAppearance.DESTRUCTIVE,
		)) return
		this.#gaurd_path(
			this.folder?.get_path(),
			_("Could not trash path"),
			() => trash_fallback_delete(this.folder!),
		)
	}

	protected _is_size_unknown(__: this, size: number): boolean {
		return size < 0
	}

	protected _get_readable_size(__: this, size: number): string {
		return size >= 0 ? get_readable_byte_size(size) : _("Loading Size...")
	}
}

@GClass() class BlurBin extends from(Adw.Bin, {
	icon_theme: Property.readonly.gobject(Gtk.IconTheme),
	icon_name: Property.readwrite.string(),
	light_opacity: Property.readwrite.double(),
	dark_opacity: Property.readwrite.double(),
	blur_px: Property.readwrite.double(),
	css_class_name: Property.readwrite.string(),
}) {
	readonly #paintable: Gtk.IconPaintable | undefined
	readonly #settings = Gtk.Settings.get_default()
	readonly #css_provider = new Gtk.CssProvider()
	readonly #downscale = 2

	constructor(params?: typeof BlurBin.$params) {
		super(params)
		this.#paintable = this.icon_theme?.lookup_icon(
			this.icon_name,
			null,
			10,
			1,
			Gtk.TextDirection.NONE,
			Gtk.IconLookupFlags.NONE,
		)
		this.#settings?.$connect("notify::gtk-interface-color-scheme", () => this.#apply_css())
		this.#settings?.$connect("notify::gtk-interface-contrast", () => this.#apply_css())
		this.#apply_css()
	}

	#apply_css(): void {
		const is_dark = this.#settings?.gtk_interface_color_scheme === Gtk.InterfaceColorScheme.DARK
		const prefers_contrast = this.#settings?.gtk_interface_contrast === Gtk.InterfaceContrast.MORE
		if (prefers_contrast) return
		this.add_css_class(this.css_class_name)
		Gtk.StyleContext.add_provider_for_display(
			this.get_display(),
			this.#css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		this.#css_provider.load_from_data(`
			.${this.css_class_name} {
				filter: saturate(200%) blur(${this.blur_px}px);
				transform: scale(${this.#downscale});
				opacity: ${is_dark ? this.dark_opacity : this.light_opacity};
			}
		`, -1)
	}

	override vfunc_snapshot(snapshot: Gtk.Snapshot): void {
		const prefers_contrast = this.#settings?.gtk_interface_contrast === Gtk.InterfaceContrast.MORE
		if (!this.#paintable || prefers_contrast) {
			super.vfunc_snapshot(snapshot)
			return
		}

		const width = this.get_width()
		const height = this.get_height()
		const center = Math.min(width, height) / 2

		snapshot.save()
		snapshot.translate(new Graphene.Point({ x: center, y: center }))
		snapshot.scale(1 / this.#downscale, 1 / this.#downscale)
		snapshot.rotate(-90)
		snapshot.translate(new Graphene.Point({ x: -center, y: -center }))
		this.#paintable.snapshot(snapshot, height, width)
		snapshot.restore()
		super.vfunc_snapshot(snapshot)
	}
}
