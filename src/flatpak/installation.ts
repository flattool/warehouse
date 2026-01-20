import GObject from "gi://GObject?version=2.0"
import GLib from "gi://GLib?version=2.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, next_idle, from } from "../gobjectify/gobjectify.js"
import { run_command_async } from "../utils/helper_funcs.js"
import { SharedVars } from "../utils/shared_vars.js"

const CUSTOM_INSTALLATIONS_DIR = Gio.File.new_for_path("/run/host/etc/flatpak/installations.d")

const Base = from(GObject.Object, {
	name: Property.string({ flags: "CONSTRUCT_ONLY" }),
	title: Property.string({ flags: "CONSTRUCT_ONLY" }),
	location_tag: Property.string({ flags: "CONSTRUCT_ONLY", default: "system" }).as<"system" | "user" | "other">(),
	location_path: Property.string({ flags: "CONSTRUCT_ONLY" }),
})

@GClass()
export class Installation extends Base {
	readonly packages = Gio.ListStore.new(GObject.Object.$gtype)
	readonly installations = Gio.ListStore.new(GObject.Object.$gtype)

	get command_syntax(): string {
		return this.location_tag === "other" ? `--installation=${this.name}` : `--${this.name}`
	}

	async load_packages(): Promise<void> {
		// return await get_packages(this, this.packages)
	}

	async load_remotes(): Promise<void> {
		// return await get_remotes(this, this.remotes)
	}
}

export async function get_installations(list: Gio.ListStore): Promise<void> {
	list.remove_all()
	const raw_installations = new Set(
		(await run_command_async(["flatpak", "--installations"], { run_on_host: true })).split("\n"),
	)
	if (CUSTOM_INSTALLATIONS_DIR.query_exists(null)) {
		for (const file_info of CUSTOM_INSTALLATIONS_DIR.enumerate_children(
			"standard::*",
			Gio.FileQueryInfoFlags.NONE,
			null,
		)) {
			const path: string = `${CUSTOM_INSTALLATIONS_DIR.get_path()}/${file_info.get_name()}`
			const keyfile = new GLib.KeyFile()
			try {
				keyfile.load_from_file(path, GLib.KeyFileFlags.NONE)
			} catch (error) {
				print(error)
				continue
			}
			const groups: string[] = keyfile.get_groups()[0]
			for (const group of groups) {
				await next_idle()
				const name = group.replace('Installation "', "").replace('"', "")
				let title: string
				try {
					title = keyfile.get_string(group, "DisplayName")
				} catch {
					title = name
				}
				let inst_path: string
				try {
					inst_path = keyfile.get_string(group, "Path")
				} catch (error) {
					print(error)
					continue
				}
				const installation = new Installation({
					name,
					title,
					location_tag: "other",
					location_path: inst_path,
				})
				if (inst_path && raw_installations.has(inst_path)) {
					raw_installations.delete(inst_path)
				}
				list.append(installation)
			}
		}
	}
	if (raw_installations.size === 1) {
		const system_raw: string = [...raw_installations.values()][0]!
		list.append(new Installation({
			name: "system",
			title: _("System"),
			location_tag: "system",
			location_path: system_raw,
		}))
	}
	list.append(new Installation({
		name: "user",
		title: _("User"),
		location_tag: "user",
		location_path: `${SharedVars.local_share_path}/flatpak`,
	}))
}
