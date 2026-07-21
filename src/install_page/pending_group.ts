import Adw from "gi://Adw?version=1"

import { Child, from, GClass, Property, Signal } from "../gobjectify/gobjectify.js"
import { ArrayStore } from "../utils/array_store.js"
import { Remote, SearchResult } from "../flatpak.js"
import { ResultRow } from "./result_row.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/pending_group.ui" })
export class PendingGroup extends from(Adw.PreferencesGroup, {
	remote: Property.readonly.gobject(Remote),
	queue_remove: Signal([SearchResult]),
	_results: Child<ArrayStore<SearchResult>>(),
}) {
	get n_results(): number { return this._results.length }

	constructor(params?: typeof PendingGroup.$params) {
		super(params)
		this.bind_model(this._results.with_implements, (item) => {
			const result = item as SearchResult
			const row = new ResultRow({ result, kind: "removable" })
			row.$connect("queue-remove", () => {
				this._results.remove(this._results.index_of(result))
				this.$emit("queue-remove", result)
			})
			return row
		})
	}

	add_result(result: SearchResult): void {
		this._results.append(result)
	}

	remove_all(): void {
		for (const result of this._results) {
			this.$emit("queue-remove", result)
		}
		this._results.remove_all()
		this.$emit("queue-remove", null)
	}

	protected _get_installation_text(): string {
		return _("Installation: %s").format(this.remote?.installation?.title ?? "")
	}
}
