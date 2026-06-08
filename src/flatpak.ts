// This frustratingly must be one file due to circular imports

import GObject from "gi://GObject?version=2.0"
import GLib from "gi://GLib?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, next_idle, from, Debounce, dedent } from "./gobjectify/gobjectify.js"
// import { run_command_async, run_command_async_pkexec_on_fail } from "./utils/helper_funcs.js"
import { LineProcess } from "./utils/cli.js"
import { SharedVars } from "./utils/shared_vars.js"
import { ArrayStore } from "./utils/array_store.js"
import type { PopularRemote } from "./popular_remotes.js"
import { remove_host_prefix } from "./utils/helper_funcs.js"

@GClass()
export class CustomInstallationCreationConfig extends from(GObject.Object, {
	name: Property.readonly.string(),
	title: Property.readonly.string(),
	location_path: Property.readonly.string(),
}) {
	constructor(params: Required<typeof CustomInstallationCreationConfig.$params>) {
		super(params)
	}
}

export class CustomInstallationFile {
	static async get_custom_installations(on_each_inst?: (inst: Installation) => void): Promise<Installation[]> {
		const custom_dir: Gio.File = SharedVars.CUSTOM_INSTALLATIONS_DIR
		const to_ret: Installation[] = []
		if (!custom_dir.query_exists(null)) return to_ret
		let enumerator: Gio.FileEnumerator
		try {
			enumerator = custom_dir.enumerate_children("standard::*", Gio.FileQueryInfoFlags.NONE, null)
		} catch (e) {
			print(e)
			return to_ret
		}
		for (const file_info of enumerator) {
			const path: string = `${SharedVars.CUSTOM_INSTALLATIONS_DIR.get_path()}/${file_info.get_name()}`
			const keyfile = new GLib.KeyFile()
			try {
				const custom = new CustomInstallationFile(path, keyfile)
				await custom.#get_installations((inst) => {
					to_ret.push(inst)
					on_each_inst?.(inst)
				})
			} catch (e) {
				print(e)
				continue
			}
		}
		return to_ret
	}

	static async create_installation(config: CustomInstallationCreationConfig): Promise<void> {
		const { name, title, location_path } = config
		let config_contents = dedent`
			[Installation "${name}"]
			DisplayName=${title}
			Path=${location_path}
		`
		config_contents += "\n"
		if (!name || name.startsWith(".")) {
			throw new Error("Cannot create installation with empty name or ")
		}
		const temp_path = `${GLib.get_user_data_dir()}/${name}.conf`
		if (!GLib.file_set_contents(temp_path, config_contents)) {
			throw new Error(`Could not create temp file '${temp_path}' for new installation`)
		}
		const dest_path: string = remove_host_prefix(`${SharedVars.CUSTOM_INSTALLATIONS_DIR.get_path()}/${name}.conf`)
		await LineProcess.run(
			["pkexec", "mv", temp_path, dest_path],
			{ run_on_host: true },
		)
	}

	readonly path: string
	readonly keyfile: GLib.KeyFile
	readonly #installations: Installation[] = []

	private constructor(path: string, keyfile: GLib.KeyFile) {
		this.path = path
		this.keyfile = keyfile
		this.keyfile.load_from_file(this.path, GLib.KeyFileFlags.NONE)
	}

	async remove_installation(installation: Installation, remove_installation_location: boolean): Promise<void> {
		if (!this.path || this.path == "/" || !this.path.includes(SharedVars.CUSTOM_INSTALLATIONS_DIR.get_path()!)) {
			// eslint-disable-next-line
			throw new Error(`Custom installation config path '${this.path}' empty, or not in custom installation config location '${SharedVars.CUSTOM_INSTALLATIONS_DIR}'`)
		}

		const group = `Installation "${installation.name}"`
		this.keyfile.remove_group(group)

		let sub_command = ""
		if (this.keyfile.get_groups()[0].length > 0) {
			// still has custom installations
			const basename = Gio.File.new_for_path(this.path).get_basename()!
			const temp_path = `${GLib.get_user_data_dir()}/__warehouse_temp_inst_config_${basename}__`
			this.keyfile.save_to_file(temp_path)
			sub_command += `mv ${GLib.shell_quote(temp_path)} ${GLib.shell_quote(remove_host_prefix(this.path))}`
		} else {
			// has no custom installations
			sub_command += `rm ${GLib.shell_quote(remove_host_prefix(this.path))}`
		}
		const inst_path = installation.location_path
		if (remove_installation_location && inst_path != "/" && Gio.File.new_for_path(inst_path).query_exists(null)) {
			sub_command += `&& rm -rf ${GLib.shell_quote(remove_host_prefix(inst_path))}`
		}
		await LineProcess.run(["pkexec", "sh", "-c", sub_command], { run_on_host: true })
	}

	async #get_installations(on_each_inst?: (inst: Installation) => void): Promise<readonly Installation[]> {
		if (this.#installations.length > 0) {
			return this.#installations
		}
		const to_ret: Installation[] = []
		const groups: string[] = this.keyfile.get_groups()[0]
		for (const group of groups) {
			await next_idle()
			const name = group.replace('Installation "', "").replace('"', "")
			let title: string
			try {
				title = this.keyfile.get_string(group, "DisplayName")
			} catch (error) {
				title = name
			}
			let inst_path: string
			try {
				inst_path = this.keyfile.get_string(group, "Path").normalize_path()
			} catch (error) {
				print(error)
				continue
			}
			const installation = new Installation({
				name,
				title,
				location_tag: "other",
				location_path: inst_path,
				custom_file: this,
			})
			on_each_inst?.(installation)
			to_ret.push(installation)
		}
		return to_ret
	}
}

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
	name: Property.readonly.string(),
	title: Property.readonly.string(),
	location_tag: Property.readonly.string("system").as<"system" | "user" | "other">(),
	location_path: Property.readonly.string(),
	custom_file: Property.readonly.jsobject().as<CustomInstallationFile>(),
	masked_ids: Property.readwrite.jsobject().as<Set<string>>(),
	pinned_refs: Property.readwrite.jsobject().as<Set<string>>(),
	loading: Property.readwrite.bool(true),
}) {
	readonly remotes = new ArrayStore<Remote>({})
	readonly packages = new ArrayStore<Package>({})
	readonly icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default() ?? new Gdk.Display())

	readonly #items_loading = new Set<"remotes" | "packages">()
	#monitor?: Gio.FileMonitor

	get command_syntax(): string {
		return this.location_tag === "other" ? `--installation=${this.name}` : `--${this.name}`
	}

	constructor(params?: typeof Installation.$params) {
		super(params)
		const file: Gio.File = Gio.File.new_for_path(this.location_path).get_child("repo")
		this.icon_theme.add_search_path(`${this.location_path}/exports/share/icons`.normalize_path())
		if (
			file.query_exists(null)
			&& file.query_file_type(Gio.FileQueryInfoFlags.NONE, null) === Gio.FileType.DIRECTORY
		) {
			this.#monitor = file.monitor_directory(Gio.FileMonitorFlags.NONE, null)
			this.#monitor.connect("changed", () => this.#reload())
		} else {
			print(`Remote: '${this.title}' - '${this.name}' does not have a 'repo' directory!`)
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

	async add_remote(remote: PopularRemote): Promise<void> {
		const { info } = remote
		const command = [
			"flatpak",
			"remote-add",
			this.command_syntax,
			"--if-not-exists",
			`--title=${info.title}`,
			`--description=${info.description}`,
			info.name,
			info.link,
		]
		await LineProcess.run(command, { run_on_host: true })
	}

	async remove(remove_installation_location = false): Promise<void> {
		try {
			await this.custom_file!.remove_installation(this, remove_installation_location)
			SharedVars.main_window?.add_toast(_("Removed %s").format(this.title))
		} catch (e) {
			SharedVars.main_window?.add_error_toast(
				_("Could not remove installation"),
				e instanceof Error ? e.message : `${e}`,
			)
		}
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
	await LineProcess.run(
		["flatpak", "--installations"],
		{ run_on_host: true, on_stdout_line: (line) => raw_insts.add(line.normalize_path()) },
	)
	const insts: Installation[] = await CustomInstallationFile.get_custom_installations(
		(inst) => raw_insts.delete(inst.location_path),
	)
	if (raw_insts.size === 1) {
		const system_raw: string = [...raw_insts.values()][0]!
		insts.push(new Installation({
			name: "system",
			title: _("System"),
			location_tag: "system",
			location_path: system_raw,
			custom_file: null,
		}))
	}
	insts.push(new Installation({
		name: "user",
		title: _("User"),
		location_tag: "user",
		location_path: `${SharedVars.local_share_path.normalize_path()}/flatpak`,
		custom_file: null,
	}))
	list.swap_contents(insts)
}

const REMOTES_LIST_COLUMN_ITEMS = {
	columns: ["title", "comment", "description", "options", "name"] as const,
	index_of(item: (typeof this.columns)[number]): number {
		return this.columns.indexOf(item)
	},
} as const

@GClass()
export class Remote extends from(GObject.Object, {
	name: Property.readonly.string(),
	title: Property.readonly.string(),
	comment: Property.readonly.string(),
	description: Property.readonly.string(),
	options: Property.readonly.string(),
	installation: Property.readonly.gobject(Installation),
	disabled: Property.readonly.bool(),
}) {
	constructor(params?: typeof Remote.$params) {
		if (params) {
			params.disabled = params.options?.includes("disabled") ?? false
		}
		super(params)
	}

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

@GClass()
export class Package extends from(GObject.Object, {
	title: Property.readonly.string(),
	description: Property.readonly.string(),
	application: Property.readonly.string(),
	version: Property.readonly.string(),
	branch: Property.readonly.string(),
	arch: Property.readonly.string(),
	runtime: Property.readonly.string(),
	origin: Property.readonly.string(),
	app_ref: Property.readonly.string(),
	active: Property.readonly.string(),
	latest: Property.readonly.string(),
	size: Property.readonly.string(),
	options: Property.readonly.string(),
	installation: Property.readonly.gobject(Installation),
	data_dir: Property.readonly.gobject(Gio.File),
	is_runtime: Property.readonly.bool(),
	is_app: Property.readonly.bool(),
	is_eol: Property.readonly.bool(),
	is_masked: Property.readonly.bool(),
	is_pinned: Property.readonly.bool(),
	icon_path: Property.readonly.string(),
}) {
	static readonly user_data_dir = Gio.File.new_for_path(GLib.get_home_dir() + "/.var/app")

	constructor(params: { application: string } & typeof Package.$params) {
		params.is_runtime = params.options?.includes("runtime") ?? false
		params.is_app = !params.is_runtime
		params.is_eol = params.options?.includes("eol") ?? false
		if (params.installation && params.app_ref) {
			params.is_masked = params.installation!.masked_ids?.has(params.app_ref) ?? false
			params.is_pinned = params.installation!.pinned_refs?.has(params.app_ref) ?? false
		}
		if (params.is_app) {
			params.data_dir = Gio.File.new_for_path(`${Package.user_data_dir.get_path()}/${params.application}`)
		}

		const icon_theme: Gtk.IconTheme | undefined = params.installation?.icon_theme
		if (icon_theme) {
			const FALLBACK = "application-x-executable-symbolic"
			params.icon_path = icon_theme.lookup_icon(
				icon_theme.has_icon(params.application) ? params.application : FALLBACK,
				null,
				1024,
				1,
				Gtk.TextDirection.NONE,
				Gtk.IconLookupFlags.FORCE_REGULAR,
			).get_file()?.get_path() ?? ""
		}

		super(params)
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
