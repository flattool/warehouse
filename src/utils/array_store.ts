import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"

import { from, GClass } from "../gobjectify/gobjectify.js"

@GClass()
export class ArrayStore<T extends GObject.Object> extends from(
	GObject.Object,
	{},
	Gio.ListModel,
) implements Gio.ListModel.Interface {
	#items = new Array<T>()

	get length(): number {
		return this.#items.length
	}

	append(item: T): void {
		this.#items.push(item)
		this.with_implements.items_changed(this.#items.length - 1, 0, 1)
	}

	remove(position: number): boolean {
		if (position < 0 || position > this.length) return false
		this.#items.splice(position, 1)
		this.with_implements.items_changed(position, 1, 0)
		return true
	}

	swap_contents(contents: T[]): void {
		const old_length: number = this.#items.length
		this.#items = contents
		this.with_implements.items_changed(0, old_length, this.length)
	}

	remove_all(): void {
		this.swap_contents([])
	}

	index_of(item: T): number {
		return this.#items.indexOf(item)
	}

	vfunc_get_item(position: number): T | null {
		return this.#items[position] ?? null
	}

	vfunc_get_n_items(): number {
		return this.#items.length
	}

	vfunc_get_item_type(): GObject.GType {
		return GObject.Object.$gtype
	}

	[Symbol.iterator](): IterableIterator<T> {
		return this.#items[Symbol.iterator]()
	}
}
