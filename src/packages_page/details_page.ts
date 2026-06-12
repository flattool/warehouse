import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gdk from "gi://Gdk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, Child, Property, from, OnSignal, next_idle, Debounce } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"
import { activate_flatseal, get_readable_file_size, is_dbus_name_present } from "../utils/helper_funcs.js"
import { SharedVars } from "../utils/shared_vars.js"
import { LineProcess } from "../utils/cli.js"

import "./info_row.js"

const CLI_INFO_KEYS = [
	"License",
	"Sdk",
	"Collection",
	"Commit",
	"Parent",
	"Subject",
	"Date",
] as const

async function get_cli_info(flatpak: Package): Promise<Record<string, string>> {
	const cmd = ["flatpak", "info"]
	if (flatpak.installation) {
		cmd.push(flatpak.installation.command_syntax)
	}
	cmd.push(flatpak.app_ref)
	const to_ret: Record<string, string> = {}
	await LineProcess.run(cmd, {
		run_on_host: true,
		on_stdout_line(line) {
			line = line.trim()
			if (/^\s*$/.test(line)) {
				// skip lines that are only whitespace or empty
				return
			}
			let [line_key, rest] = line.split_n_times(":", 1)
			if (!line_key) return
			for (const key of CLI_INFO_KEYS) {
				line_key = line_key.trim()
				if (line_key === key) {
					to_ret[key.toLowerCase()] = rest?.trim() || ""
				}
			}
		},
	})
	return to_ret
}

const BLUR_AMOUNT = 100
const LIGHT_OPACTIY = 1.0
const DARK_OPACITY = 0.5
const BACKGROUND_PICTURE_OFFSET = -80
const BACKGROUND_PICTURE_HEIGHT = 350

let total_instances = 0

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/details_page.ui" })
export class DetailsPage extends from(Adw.NavigationPage, {
	flatpak: Property.readwrite.gobject(Package),
	runtime: Property.readwrite.gobject(Package),
	show_title: Property.readwrite.bool(),
	has_user_data: Property.readwrite.bool(),
	loading_user_data: Property.readwrite.bool(true),
	flatseal_found: Property.readwrite.bool(),
	data_size: Property.readwrite.string(),

	// Extra CLI Info
	info_license: Property.readwrite.string(),
	info_sdk: Property.readwrite.string(),
	info_collection: Property.readwrite.string(),
	info_commit: Property.readwrite.string(),
	info_parent: Property.readwrite.string(),
	info_subject: Property.readwrite.string(),
	info_date: Property.readwrite.string(),
	monitor: Property.computed.gobject(Gio.FileMonitor),

	_nav_view: Child<Adw.NavigationView>(),
	_blur_target: Child<Adw.Bin>(),
	_image: Child<Gtk.Image>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_user_data_row: Child<Adw.ActionRow>(),
}) {
	readonly #css_provider = new Gtk.CssProvider()
	readonly #css_class_name = `details-blur-${total_instances += 1}`
	readonly #gtk_settings = Gtk.Settings.get_default()
	#subpage?: DetailsPage
	#scroll_position = 0

	private _monitor: Gio.FileMonitor | null = null
	override get monitor(): Gio.FileMonitor | null { return this._monitor }
	override set monitor(v: Gio.FileMonitor | null) {
		this._monitor?.cancel()
		this._monitor = v
		v?.connect("changed", () => this.#on_monitor_changed())
	}

	constructor(params?: typeof DetailsPage.$params) {
		super(params)
		this._blur_target.add_css_class(this.#css_class_name)
		Gtk.StyleContext.add_provider_for_display(
			Gdk.Display.get_default()!,
			this.#css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		this.#load_css_translation(0)
		const vadjustment: Gtk.Adjustment = this._scrolled_window.vadjustment
		vadjustment.connect("value-changed", () => {
			this.#scroll_position = vadjustment.value
			this.show_title = this.#scroll_position > 135
			this.#load_css_translation(-this.#scroll_position)
		})
		is_dbus_name_present("com.github.tchx84.Flatseal").then((present) => this.flatseal_found = present).catch(log)
		this.#on_flatpak_change().catch(log)
	}

	pop_to_base_page(): void {
		this._nav_view.pop_to_tag("base-page")
	}

	@OnSignal("notify::flatpak")
	async #on_flatpak_change(): Promise<void> {
		this._nav_view.pop_to_tag("base-page")
		this.#load_css_translation(-this.#scroll_position)
		this.has_user_data = false
		this.loading_user_data = true
		let info: Record<string, string> = {}
		const pack = this.flatpak
		if (pack) {
			try {
				info = await get_cli_info(pack)
				this._image.set_from_file(pack.icon_path)
			} catch (e) {
				SharedVars.main_window?.add_error_toast(
					_("Could not show details"),
					e instanceof Error ? e.message : `${e}`,
				)
			}
		}
		this.info_license = info["license"] || ""
		this.info_sdk = info["sdk"] || ""
		this.info_commit = info["commit"] || ""
		this.info_collection = info["collection"] || ""
		this.info_parent = info["parent"] || ""
		this.info_subject = info["subject"] || ""
		this.info_date = info["date"] || ""
		if (!pack || !pack.is_app) return
		this.has_user_data = pack.data_dir?.query_exists(null) ?? false
		if (this.has_user_data) {
			this.data_size = await get_readable_file_size(pack.data_dir?.get_path() ?? "")
		} else {
			this.data_size = _("No user data found")
		}
		this.loading_user_data = false
		const installations = SharedVars.main_window?._installations
		if (!installations) return
		for (const inst of installations) {
			for (const pack of inst.packages) {
				await next_idle()
				if (pack.app_ref === pack.runtime) {
					this.runtime = pack
				}
			}
		}
	}

	@Debounce(200)
	#on_monitor_changed(): void {
		this.loading_user_data = true
		this.has_user_data = Boolean(this.flatpak?.data_dir?.query_exists(null))
		if (!this.has_user_data) {
			this.loading_user_data = false
			this.data_size = _("No user data found")
			return
		}
		get_readable_file_size(this.flatpak?.data_dir?.get_path() ?? "").then((size) => {
			this.data_size = size
			this.loading_user_data = false
		}).catch(log)
	}

	#load_css_translation(y: number): void {
		const is_dark: boolean = this.#gtk_settings?.gtk_interface_color_scheme === Gtk.InterfaceColorScheme.DARK
		const prefers_contrast: boolean = this.#gtk_settings?.gtk_interface_contrast === Gtk.InterfaceContrast.MORE
		const css_data = `
			.${this.#css_class_name} {
				transform: translateY(${y + BACKGROUND_PICTURE_OFFSET}px);
				margin-bottom: max(${BACKGROUND_PICTURE_OFFSET}px, 0px);
				background-image: ${prefers_contrast ? "none" : `url("file://${this.flatpak?.icon_path}")`};
				background-repeat: no-repeat;
				background-size: 100% ${BACKGROUND_PICTURE_HEIGHT}px;
				background-position: 0px 0px;
				filter: ${prefers_contrast ? "none" : `blur(${BLUR_AMOUNT}px)`};
				opacity: ${is_dark ? DARK_OPACITY : LIGHT_OPACTIY};
			}
		`
		this.#css_provider.load_from_data(css_data, -1)
	}

	protected _get_titile(): string {
		return this.flatpak?.title ?? _("Details")
	}

	protected async _show_runtime(): Promise<void> {
		this.#subpage ??= new DetailsPage({})
		this.#subpage.flatpak = this.runtime
		this._nav_view.push(this.#subpage)
	}

	protected _get_monitor_for_package(__: this): Gio.FileMonitor | null {
		if (!this.flatpak?.data_dir?.query_exists(null)) return null
		return this.flatpak.data_dir.monitor_directory(Gio.FileMonitorFlags.NONE, null)
	}

	protected _get_data_subtitle(__: this, data_size: string, loading_user_data: boolean): string {
		return loading_user_data ? _("Loading User Data...") : data_size
	}

	protected _markup_escape(__: this, text: string): string {
		return text.markup_escape_text()
	}

	protected _bool_cast(__: this, item: unknown): boolean {
		return Boolean(item)
	}

	protected _get_version_subtitle(__: this, version_text: string): string {
		return version_text || _("No version information found")
	}

	protected _get_visible_page_name(): "content_page" | "nothing_selected_page" {
		return this.flatpak ? "content_page" : "nothing_selected_page"
	}

	protected _can_edit_permissions(__: this): boolean {
		return this.flatseal_found && (this.flatpak?.is_app ?? false)
	}

	protected async _manage_permissions(): Promise<void> {
		if (!this.flatpak) return
		SharedVars.main_window?.add_toast(_("Opening Flatseal..."))
		try {
			await activate_flatseal(this.flatpak.application)
		} catch (e) {
			SharedVars.main_window?.add_error_toast(
				_("Could not manage permissions"),
				e instanceof Error ? e.message : `${e}`,
			)
		}
	}
}
