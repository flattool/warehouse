import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { get_file_size_bytes } from "../utils/helper_funcs.js"

@GClass()
export class SizedFolder extends from(GObject.Object, {
	folder: Property.readonly.gobject(Gio.File),
	size: Property.readwrite.double(-1),
}) {
	constructor(params?: typeof SizedFolder.$params) {
		super(params)
		this.#load_size()
	}

	async #load_size(): Promise<void> {
		const path = this.folder?.get_path()
		if (!path) {
			this.size = 0
			return
		}
		try {
			this.size = await get_file_size_bytes(path)
		} catch (e) {
			this.size = 0
			print(`Error loading size for '${path}':`, e)
		}
	}
}
