import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gdk from "gi://Gdk?version=4.0"

import { GClass, Child, Property, from, OnSignal } from "../gobjectify/gobjectify.js"
import { Package } from "../flatpak.js"
import { run_command_async } from "../utils/helper_funcs.js"

import "./info_row.js"

const BACKGROUND_PICTURE_OFFSET = -80
const css_provider = new Gtk.CssProvider()

function load_css_translation(y: number): void {
	css_provider.load_from_data(`
		.details-blurred {
			filter: blur(200px);
			transform: translateY(${y + BACKGROUND_PICTURE_OFFSET}px);
		}
		@media (prefers-color-scheme: dark) {
			.details-blurred {
				opacity: 0.5;
			}
		}
		@media (prefers-contrast: more) {
			.details-blurred {
				filter: none;
				opacity: 1;
			}
		}
	`, -1)
}

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
				to_ret[key] = rest?.trim() || ""
			}
		}
	}
	return to_ret
}

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/details_page.ui" })
export class DetailsPage extends from(Adw.NavigationPage, {
	flatpak: Property.gobject(Package),
	show_title: Property.bool(),
	_background_picture: Child<Gtk.Picture>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
}) {
	_ready(): void {
		load_css_translation(0)
		Gtk.StyleContext.add_provider_for_display(
			Gdk.Display.get_default()!,
			css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		const vadjustment: Gtk.Adjustment = this._scrolled_window.vadjustment
		vadjustment.connect("value-changed", () => {
			const value = vadjustment.value
			this.show_title = value > 0
			load_css_translation(-value)
		})
	}

	@OnSignal("notify::flatpak")
	async #on_flatpak_change(): Promise<void> {
		if (!this.flatpak) return
		const info = await get_cli_info(this.flatpak)
		print(JSON.stringify(info))
	}

	protected _markup_escape(__: this, text: string): string {
		return text.markup_escape_text()
	}
}
