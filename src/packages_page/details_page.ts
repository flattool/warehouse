import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gdk from "gi://Gdk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, Child, Property, from, OnSignal, next_idle, Debounce } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"
import { get_readable_file_size, run_command_async } from "../utils/helper_funcs.js"
import { SharedVars } from "../utils/shared_vars.js"

import "./info_row.js"

const BACKGROUND_PICTURE_OFFSET = -80

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
	const lines: string[] = (await run_command_async(cmd, { run_on_host: true })).trim().split("\n")
	const to_ret: Record<string, string> = {}
	if (lines.length < 1) return to_ret
	for (let line of lines) {
		line = line.trim()
		if (/^\s*$/.test(line)) {
			// skip lines that are only whitespice or emtpy
			continue
		}
		let [line_key, rest] = line.split_n_times(":", 1)
		if (!line_key) continue
		for (const key of CLI_INFO_KEYS) {
			line_key = line_key.trim()
			if (line_key === key) {
				to_ret[key.toLowerCase()] = rest?.trim() || ""
			}
		}
	}
	return to_ret
}

let total_instances = 0

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/details_page.ui" })
export class DetailsPage extends from(Adw.NavigationPage, {
	flatpak: Property.gobject(Package),
	runtime: Property.gobject(Package),
	show_title: Property.bool(),
	has_user_data: Property.bool(),
	loading_user_data: Property.bool({ default: true }),
	data_size: Property.string(),

	// Extra CLI Info
	info_license: Property.string(),
	info_sdk: Property.string(),
	info_collection: Property.string(),
	info_commit: Property.string(),
	info_parent: Property.string(),
	info_subject: Property.string(),
	info_date: Property.string(),
	monitor: Property.gobject(Gio.FileMonitor),

	_nav_view: Child<Adw.NavigationView>(),
	_background_picture: Child<Gtk.Picture>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_user_data_row: Child<Adw.ActionRow>(),
}) {
	readonly #css_provider = new Gtk.CssProvider()
	readonly #css_class_name = `details-blur-${total_instances += 1}`
	#subpage?: DetailsPage

	private _monitor: Gio.FileMonitor | null = null
	override get monitor(): Gio.FileMonitor | null { return this._monitor }
	override set monitor(v: Gio.FileMonitor | null) {
		this._monitor?.cancel()
		this._monitor = v
		v?.connect("changed", () => this.#on_monitor_changed())
	}

	_ready(): void {
		this._background_picture.add_css_class(this.#css_class_name)
		this.#load_css_translation(0)
		Gtk.StyleContext.add_provider_for_display(
			Gdk.Display.get_default()!,
			this.#css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		const vadjustment: Gtk.Adjustment = this._scrolled_window.vadjustment
		vadjustment.connect("value-changed", () => {
			const value = vadjustment.value
			this.show_title = value > 0
			this.#load_css_translation(-value)
		})
		this.#on_flatpak_change().catch(log)
	}

	pop_to_base_page(): void {
		this._nav_view.pop_to_tag("base-page")
	}

	@OnSignal("notify::flatpak")
	async #on_flatpak_change(): Promise<void> {
		this._nav_view.pop_to_tag("base-page")
		this.has_user_data = false
		this.loading_user_data = true
		let info: Record<string, string> = {}
		if (this.flatpak) {
			info = await get_cli_info(this.flatpak)
		}
		this.info_license = info["license"] || ""
		this.info_sdk = info["sdk"] || ""
		this.info_commit = info["commit"] || ""
		this.info_collection = info["collection"] || ""
		this.info_parent = info["parent"] || ""
		this.info_subject = info["subject"] || ""
		this.info_date = info["date"] || ""
		if (!this.flatpak || !this.flatpak.is_app) return
		this.has_user_data = this.flatpak.data_dir?.query_exists(null) ?? false
		if (this.has_user_data) {
			this.data_size = await get_readable_file_size(this.flatpak.data_dir?.get_path() ?? "")
		} else {
			this.data_size = _("No user data found")
		}
		this.loading_user_data = false
		const installations = SharedVars.main_window?._installations
		if (!installations) return
		for (const inst of installations) {
			for (const pack of inst.packages) {
				await next_idle()
				if (pack.app_ref === this.flatpak.runtime) {
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
		this.#css_provider.load_from_data(`
			.${this.#css_class_name} {
				filter: blur(200px);
				transform: translateY(${y + BACKGROUND_PICTURE_OFFSET}px);
			}
			@media (prefers-color-scheme: dark) {
				.${this.#css_class_name} {
					opacity: 0.5;
				}
			}
			@media (prefers-contrast: more) {
				.${this.#css_class_name} {
					filter: none;
					opacity: 1;
				}
			}
		`, -1)
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
}
