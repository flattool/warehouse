import Adw from "gi://Adw?version=1"

import { Child, from, GClass, Property, Signal, WatchProp } from "../gobjectify/gobjectify.js"
import { Installation, Remote, SearchResult } from "../flatpak.js"
import { PendingGroup } from "./pending_group.js"

type StackPages = "none-pending" | "some-pending"

const make_result_id_key = (result: SearchResult): string => `${result.installation?.name}::${result.application}`

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/pending_page.ui" })
export class PendingPage extends from(Adw.Bin, {
	stack_page: Property.readwrite.string("none-pending").as<StackPages>(),
	n_pending: Property.readwrite.uint32(),
	queue_remove: Signal([SearchResult, Remote]),
	_group_page: Child<Adw.PreferencesPage>(),
}) {
	readonly #remote_to_group = new Map<Remote, PendingGroup>()
	readonly #result_id_set = new Set<string>() // keys: `<installation.name::result.application>`

	readonly #on_result_remove = (group: PendingGroup | null, result: SearchResult | null): void => {
		if (!group) return
		if (group.n_results < 1) {
			group.remote && this.#remote_to_group.delete(group.remote)
			this._group_page.remove(group)
		}
		if (result) {
			this.#result_id_set.delete(make_result_id_key(result))
		}
		if (result) {
			this.n_pending -= 1
		}
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
		this.#result_id_set.add(make_result_id_key(result))
		this.n_pending += 1
	}

	has_result_by_id(installation: Installation, result_id: string): boolean {
		return this.#result_id_set.has(`${installation.name}::${result_id}`)
	}

	@WatchProp("n_pending")
	#on_n_pending_changed(): void {
		const has_any = this.n_pending > 0
		this.stack_page = has_any ? "some-pending" : "none-pending"
	}

	protected _get_stack_page(): StackPages {
		return this.n_pending > 0 ? "some-pending" : "none-pending"
	}

	protected _show_install_button(): boolean {
		return this.n_pending > 0
	}
}
