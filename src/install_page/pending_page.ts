import Adw from "gi://Adw?version=1"

import { Child, from, GClass, Property, Signal } from "../gobjectify/gobjectify.js"
import { Remote, SearchResult } from "../flatpak.js"
import { PendingGroup } from "./pending_group.js"

type StackPages = "none-pending" | "some-pending"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/pending_page.ui" })
export class PendingPage extends from(Adw.Bin, {
	stack_page: Property.readwrite.string("none-pending").as<StackPages>(),
	queue_remove: Signal([SearchResult, Remote]),
	_group_page: Child<Adw.PreferencesPage>(),
}) {
	readonly #remote_to_group = new Map<Remote, PendingGroup>()

	readonly #on_result_remove = (group: PendingGroup | null, result: SearchResult | null): void => {
		if (!group) return
		if (group.n_results < 1) {
			group.remote && this.#remote_to_group.delete(group.remote)
			this._group_page.remove(group)
		}
		this.#on_groups_changed()
		this.$emit("queue-remove", result, group.remote)
	}

	add(result: SearchResult, remote: Remote): void {
		let group = this.#remote_to_group.get(remote)
		if (!group) {
			group = new PendingGroup({ remote })
			group.$connect("queue-remove", this.#on_result_remove)
			this.#remote_to_group.set(remote, group)
			this._group_page.add(group)
		}
		group.add_result(result)
		this.#on_groups_changed()
	}

	#on_groups_changed(): void {
		this.stack_page = this.#remote_to_group.size > 0 ? "some-pending" : "none-pending"
	}
}
