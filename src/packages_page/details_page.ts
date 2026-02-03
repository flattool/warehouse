import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gdk from "gi://Gdk?version=4.0"

import { GClass, Child, Property, from, OnSignal, next_idle } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"
import { run_command_async } from "../utils/helper_funcs.js"
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

let max_instances = 0

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/details_page.ui" })
export class DetailsPage extends from(Adw.NavigationPage, {
	flatpak: Property.gobject(Package),
	show_title: Property.bool(),

	// Extra CLI Info
	info_license: Property.string(),
	info_sdk: Property.string(),
	info_collection: Property.string(),
	info_commit: Property.string(),
	info_parent: Property.string(),
	info_subject: Property.string(),
	info_date: Property.string(),

	_nav_view: Child<Adw.NavigationView>(),
	_background_picture: Child<Gtk.Picture>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
}) {
	readonly #css_provider = new Gtk.CssProvider()
	readonly #css_class_name = `details-blur-${max_instances += 1}`

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
	}

	@OnSignal("notify::flatpak")
	async #on_flatpak_change(): Promise<void> {
		this._nav_view.pop()
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
	}

	protected async _show_runtime(): Promise<void> {
		if (!this.flatpak) return
		const installations = SharedVars.main_window?._installations
		if (!installations) return
		for (const inst of installations) {
			for (const pack of inst.packages) {
				await next_idle()
				if (pack.app_ref === this.flatpak.runtime) {
					const subpage = new DetailsPage({})
					subpage.flatpak = pack
					this._nav_view.push(subpage)
					return
				}
			}
		}
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

	protected _get_user_data_label(__: this, data_size: string): string {
		return data_size
	}

	protected _markup_escape(__: this, text: string): string {
		return text.markup_escape_text()
	}

	protected _bool_cast(__: this, item: unknown): boolean {
		return Boolean(item)
	}
}
