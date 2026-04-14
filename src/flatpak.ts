// This frustratingly must be one file due to circular imports

import GObject from "gi://GObject?version=2.0"
import GLib from "gi://GLib?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, next_idle, from, Debounce } from "./gobjectify/gobjectify.js"
// import { run_command_async, run_command_async_pkexec_on_fail } from "./utils/helper_funcs.js"
import { LineProcess } from "./utils/cli.js"
import { SharedVars } from "./utils/shared_vars.js"
import { ArrayStore } from "./utils/array_store.js"

const REMOTES_LIST_COLUMN_ITEMS = {
	columns: ["title", "comment", "description", "options", "name"] as const,
	index_of(item: (typeof this.columns)[number]): number {
		return this.columns.indexOf(item)
	},
} as const
const PACK_LIST_COLUMN_ITEMS = {
	columns: [
		"application",
		"description",
		"version",
		"branch",
		"arch",
		"runtime",
		"ref",
		"active",
		"latest",
		"options",
		"size",
		"name",
		"origin",
	] as const,
	index_of(item: (typeof this.columns)[number]): number {
		return this.columns.indexOf(item)
	},
} as const

@GClass()
export class Installation extends from(GObject.Object, {
	name: Property.string({ flags: "CONSTRUCT_ONLY" }),
	title: Property.string({ flags: "CONSTRUCT_ONLY" }),
	location_tag: Property.string({ flags: "CONSTRUCT_ONLY", default: "system" }).as<"system" | "user" | "other">(),
	location_path: Property.string({ flags: "CONSTRUCT_ONLY" }),
	masked_ids: Property.jsobject().as<Set<string>>(),
	pinned_refs: Property.jsobject().as<Set<string>>(),
	loading: Property.bool({ default: true }),
}) {
	readonly remotes = new ArrayStore<Remote>({})
	readonly packages = new ArrayStore<Package>({})
	readonly icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default() ?? new Gdk.Display())

	readonly #items_loading = new Set<"remotes" | "packages">()
	#monitor?: Gio.FileMonitor

	get command_syntax(): string {
		return this.location_tag === "other" ? `--installation=${this.name}` : `--${this.name}`
	}

	_ready(): void {
		const file: Gio.File = Gio.File.new_for_path(this.location_path).get_child("repo")
		this.icon_theme.add_search_path(`${this.location_path}/exports/share/icons`.normalize_path())
		if (
			file.query_exists(null)
			&& file.query_file_type(Gio.FileQueryInfoFlags.NONE, null) === Gio.FileType.DIRECTORY
		) {
			this.#monitor = file.monitor_directory(Gio.FileMonitorFlags.NONE, null)
			this.#monitor.connect("changed", () => this.#reload())
		} else {
			print(`Remote: '${this.title}' - '${this.name}' does not have as 'repo' directory!`)
		}
	}

	async load_remotes(): Promise<void> {
		this.#start_loading("remotes")
		await get_remotes(this, this.remotes)
		this.#stop_loading("remotes")
	}

	async load_packages(): Promise<void> {
		this.#start_loading("packages")
		const masked = new Set<string>()
		await LineProcess.run(["flatpak", "mask", this.command_syntax], {
			run_on_host: true,
			on_stdout_line(line) {
				line = line.trim()
				if (!line) return
				masked.add(line)
			},
		})
		this.masked_ids = masked
		const pinned = new Set<string>()
		await LineProcess.run(["flatpak", "pin", this.command_syntax], {
			run_on_host: true,
			on_stdout_line(line) {
				line = line.trim()
				if (!line) return
				pinned.add(line)
			},
		})
		this.pinned_refs = pinned
		await get_packages(this, this.packages)
		this.#stop_loading("packages")
	}

	@Debounce(200)
	#reload(): void {
		this.load_packages().catch(log)
		this.load_remotes().catch(log)
	}

	#start_loading(item: "remotes" | "packages"): void {
		this.#items_loading.add(item)
		this.loading = true
	}

	#stop_loading(item: "remotes" | "packages"): void {
		this.#items_loading.delete(item)
		this.loading = this.#items_loading.size > 0
	}
}

export async function get_installations(list: ArrayStore<Installation>): Promise<void> {
	const raw_insts = new Set<string>()
	const process = new LineProcess(["flatpak", "--installations"], true)
	process.on_stdout_line = (line): void => void raw_insts.add(line.normalize_path())
	await process.run()
	const insts: Installation[] = []
	if (SharedVars.CUSTOM_INSTALLATIONS_DIR.query_exists(null)) {
		for (const file_info of SharedVars.CUSTOM_INSTALLATIONS_DIR.enumerate_children(
			"standard::*",
			Gio.FileQueryInfoFlags.NONE,
			null,
		)) {
			const path: string = `${SharedVars.CUSTOM_INSTALLATIONS_DIR.get_path()}/${file_info.get_name()}`
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
				} catch (error) {
					title = name
				}
				let inst_path: string
				try {
					inst_path = keyfile.get_string(group, "Path").normalize_path()
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
				if (inst_path && raw_insts.has(inst_path)) {
					raw_insts.delete(inst_path)
				}
				insts.push(installation)
			}
		}
	}
	if (raw_insts.size === 1) {
		const system_raw: string = [...raw_insts.values()][0]!
		insts.push(new Installation({
			name: "system",
			title: _("System"),
			location_tag: "system",
			location_path: system_raw,
		}))
	}
	insts.push(new Installation({
		name: "user",
		title: _("User"),
		location_tag: "user",
		location_path: `${SharedVars.local_share_path}/flatpak`,
	}))
	list.swap_contents(insts)
}

@GClass()
export class Remote extends from(GObject.Object, {
	name: Property.string({ flags: "CONSTRUCT_ONLY" }),
	title: Property.string({ flags: "CONSTRUCT_ONLY" }),
	comment: Property.string({ flags: "CONSTRUCT_ONLY" }),
	description: Property.string({ flags: "CONSTRUCT_ONLY" }),
	options: Property.string({ flags: "CONSTRUCT_ONLY" }),
	installation: Property.gobject(Installation, { flags: "CONSTRUCT_ONLY" }),
	disabled: Property.bool(),
}) {
	override get disabled(): boolean {
		return this.options.includes("disabled")
	}
	override set disabled(_v: boolean) { throw new Error("Remote::disabled cannot be set!") }

	async enable(enable_remote: boolean): Promise<void> {
		if (!this.installation) throw new Error(`Remote '${this.name}' installation is null`)
		const command: string[] = [
			"flatpak",
			"remote-modify",
			this.installation.command_syntax,
			this.name,
			enable_remote ? "--enable" : "--disable",
		]
		if (this.installation.location_tag === "other") {
			command.unshift("pkexec")
		}
		await LineProcess.run(command, { run_on_host: true })
		this.notify("disabled")
	}

	async remove(): Promise<void> {
		if (!this.installation) throw new Error(`Remote '${this.name}' installation is null`)
		const command: string[] = [
			"flatpak",
			"remote-delete",
			this.installation.command_syntax,
			this.name,
		]
		await LineProcess.run(command, { run_on_host: true })
	}
}

async function get_remotes(
	installation: Installation,
	list: ArrayStore<Remote>,
): Promise<void> {
	const columns: string = REMOTES_LIST_COLUMN_ITEMS.columns.join(",")
	const remotes: Remote[] = []
	const process = new LineProcess(
		["flatpak", "remotes", installation.command_syntax, `--columns=${columns}`, "--show-disabled"],
		true,
	)
	process.on_stdout_line = (line): void => {
		const info: string[] = line.trim().split("\t")
		if (info.length !== REMOTES_LIST_COLUMN_ITEMS.columns.length) return
		const remote = new Remote({
			name: info[REMOTES_LIST_COLUMN_ITEMS.index_of("name")] ?? "",
			title: info[REMOTES_LIST_COLUMN_ITEMS.index_of("title")] ?? "",
			comment: info[REMOTES_LIST_COLUMN_ITEMS.index_of("comment")] ?? "",
			description: info[REMOTES_LIST_COLUMN_ITEMS.index_of("description")] ?? "",
			options: info[REMOTES_LIST_COLUMN_ITEMS.index_of("options")] ?? "",
			installation,
		})
		remotes.push(remote)
	}
	await process.run()
	list.swap_contents(remotes)
}

const BasePackage = from(GObject.Object, {
	title: Property.string({ flags: "CONSTRUCT_ONLY" }),
	description: Property.string({ flags: "CONSTRUCT_ONLY" }),
	application: Property.string({ flags: "CONSTRUCT_ONLY" }),
	version: Property.string({ flags: "CONSTRUCT_ONLY" }),
	branch: Property.string({ flags: "CONSTRUCT_ONLY" }),
	arch: Property.string({ flags: "CONSTRUCT_ONLY" }),
	runtime: Property.string({ flags: "CONSTRUCT_ONLY" }),
	origin: Property.string({ flags: "CONSTRUCT_ONLY" }),
	app_ref: Property.string({ flags: "CONSTRUCT_ONLY" }),
	active: Property.string({ flags: "CONSTRUCT_ONLY" }),
	latest: Property.string({ flags: "CONSTRUCT_ONLY" }),
	size: Property.string({ flags: "CONSTRUCT_ONLY" }),
	options: Property.string({ flags: "CONSTRUCT_ONLY" }),
	installation: Property.gobject(Installation, { flags: "CONSTRUCT_ONLY" }),
	data_dir: Property.gobject(Gio.File),
	is_runtime: Property.bool(),
	is_app: Property.bool(),
	is_eol: Property.bool(),
	is_masked: Property.bool(),
	is_pinned: Property.bool(),
	icon_path: Property.string(),
})

@GClass()
export class Package extends BasePackage {
	static readonly user_data_dir = Gio.File.new_for_path(GLib.get_home_dir() + "/.var/app")

	private _is_runtime?: boolean
	override get is_runtime(): boolean {
		return this._is_runtime ??= this.options.includes("runtime")
	}
	override set is_runtime(_v: boolean) { throw new Error("Package::is_runtime cannot be set!") }
	override get is_app(): boolean {
		return !this.is_runtime
	}
	override set is_app(_v: boolean) { throw new Error("Package::is_app cannot be set!") }

	private _is_eol?: boolean
	override get is_eol(): boolean {
		return this._is_eol ??= this.options.includes("eol")
	}
	override set is_eol(_v: boolean) { throw new Error("Package::is_eol cannot be set!") }

	private _is_masked?: boolean
	override get is_masked(): boolean {
		return this._is_masked ??= this.installation?.masked_ids?.has(this.application) ?? false
	}
	override set is_masked(_v: boolean) { throw new Error("Package::is_masked cannot be set!") }

	private _is_pinned?: boolean
	override get is_pinned(): boolean {
		return this._is_pinned ??= this.installation?.pinned_refs?.has(this.app_ref) ?? false
	}
	override set is_pinned(_v: boolean) { throw new Error("Package::is_pinned cannot be set!") }

	constructor(...params: ConstructorParameters<typeof BasePackage>) {
		super(...params)
		if (!this.is_runtime) {
			this.data_dir = Gio.File.new_for_path(`${Package.user_data_dir.get_path()}/${this.application}`)
		}
		this.#icon_tryer()
	}

	#icon_tryer(): void {
		const FALLBACK = "application-x-executable-symbolic"
		const icon_theme: Gtk.IconTheme | undefined = this.installation?.icon_theme
		if (!icon_theme) return
		this.icon_path = icon_theme.lookup_icon(
			icon_theme.has_icon(this.application) ? this.application : FALLBACK,
			null,
			1024,
			1,
			Gtk.TextDirection.NONE,
			Gtk.IconLookupFlags.FORCE_REGULAR,
		).get_file()?.get_path() ?? ""
	}
}

async function get_packages(
	installation: Installation,
	list: ArrayStore<Package>,
): Promise<void> {
	const columns: string = PACK_LIST_COLUMN_ITEMS.columns.join(",")
	const paks: Package[] = []
	const process = new LineProcess(
		["flatpak", "list", "--all", installation.command_syntax, `--columns=${columns}`],
		true,
	)
	process.on_stdout_line = (line): void => {
		const info: string[] = line.trim().split("\t")
		if (info.length !== PACK_LIST_COLUMN_ITEMS.columns.length) {
			print("Skipping the following line:")
			print(line)
			print("")
			return
		}
		const pack = new Package({
			title: info[PACK_LIST_COLUMN_ITEMS.index_of("name")] ?? "",
			description: info[PACK_LIST_COLUMN_ITEMS.index_of("description")] ?? "",
			application: info[PACK_LIST_COLUMN_ITEMS.index_of("application")] ?? "",
			version: info[PACK_LIST_COLUMN_ITEMS.index_of("version")] ?? "",
			branch: info[PACK_LIST_COLUMN_ITEMS.index_of("branch")] ?? "",
			arch: info[PACK_LIST_COLUMN_ITEMS.index_of("arch")] ?? "",
			runtime: info[PACK_LIST_COLUMN_ITEMS.index_of("runtime")] ?? "",
			origin: info[PACK_LIST_COLUMN_ITEMS.index_of("origin")] ?? "",
			app_ref: info[PACK_LIST_COLUMN_ITEMS.index_of("ref")] ?? "",
			active: info[PACK_LIST_COLUMN_ITEMS.index_of("active")] ?? "",
			latest: info[PACK_LIST_COLUMN_ITEMS.index_of("latest")] ?? "",
			size: info[PACK_LIST_COLUMN_ITEMS.index_of("size")] ?? "",
			options: info[PACK_LIST_COLUMN_ITEMS.index_of("options")] ?? "",
			installation,
		})
		paks.push(pack)
	}
	await process.run()
	list.swap_contents(paks)
}
