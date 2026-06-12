import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"
import GLib from "gi://GLib?version=2.0"

import { GClass, from, Signal, Property, Debounce, next_idle, WatchProp } from "../gobjectify/gobjectify.js"

Gio._promisify(Gio.File.prototype, "enumerate_children_async")

@GClass()
export class FileList extends from(GObject.Object, {
	directory: Property.readwrite.gobject(Gio.File),
	change_started: Signal(),
}, Gio.ListModel) implements Gio.ListModel.Interface {
	get n_items(): number { return this.vfunc_get_n_items() }

	#items: Gio.File[] = []
	#monitor: Gio.FileMonitor | undefined
	#connection: number | undefined

	@WatchProp("directory")
	#set_up_monitor(): void {
		if (this.#connection !== undefined) {
			this.#monitor?.disconnect(this.#connection)
		}
		this.#monitor?.cancel()
		this.#monitor = this.directory?.monitor_directory(Gio.FileMonitorFlags.NONE, null)
		this.#connection = this.#monitor?.$connect("changed", () => this.#on_monitor_notice())
		this.#on_monitor_notice()
	}

	#on_monitor_notice(): void {
		this.#emit_start_changing()
		this.#debounced_refresh()
	}

	@Debounce(200, { trigger: "leading" })
	#emit_start_changing(): void {
		this.$emit("change-started")
	}

	@Debounce(200)
	#debounced_refresh(): void {
		this.#refresh_items().catch(console.error.bind(console))
	}

	async #refresh_items(): Promise<void> {
		const old_length: number = this.#items.length
		const do_change = (): void => this.with_implements.items_changed(0, old_length, this.#items.length)

		if (!this.directory || !this.directory.query_exists(null)) {
			this.#items = []
			do_change()
			return
		}

		try {
			const enumerator: Gio.FileEnumerator = await this.directory.enumerate_children_async(
				Gio.FILE_ATTRIBUTE_STANDARD_NAME,
				Gio.FileQueryInfoFlags.NONE,
				GLib.PRIORITY_DEFAULT,
				null,
			)
			const files: Gio.File[] = []
			for (const info of enumerator) {
				await next_idle()
				files.push(this.directory.get_child(info.get_name()))
			}
			this.#items = files
		} catch (e) {
			console.error(`Failed to refresh files due to ${e}`)
			this.#items = []
		}

		do_change()
	}

	vfunc_get_item(position: number): Gio.File | null {
		return this.#items[position] ?? null
	}

	vfunc_get_n_items(): number {
		return this.#items.length
	}

	vfunc_get_item_type(): GObject.GType<Gio.File> {
		return Gio.File.$gtype
	}

	*[Symbol.iterator](): IterableIterator<Gio.File> {
		for (const file of this.#items) yield file
	}
}
