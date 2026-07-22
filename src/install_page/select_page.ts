import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { Child, Debounce, from, GClass, Property, Signal, WatchProp } from "../gobjectify/gobjectify.js"
import { Installation, Package, Remote, search_packages, SearchResult } from "../flatpak.js"
import { ArrayStore } from "../utils/array_store.js"
import { iterate_list_model, make_signal_factory } from "../utils/helper_funcs.js"
import { SelectableRemote, SelectableRemoteBox } from "./selectable_remote.js"
import { ResultRow } from "./result_row.js"
import { SwitchTask } from "../utils/switch_task.js"

import "../widgets/sidebar_button.js"
import "../widgets/loading_group.js"

type StackPages = "empty-search" | "results-list" | "no-results"

const make_selected_results_keys = (
	result: SearchResult,
): string => `${result.installation?.name}::${result.application}`

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/select_page.ui" })
export class SelectPage extends from(Adw.Bin, {
	installations: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Installation>>(),
	remotes: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	packages: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Package>>(),
	selected_remote: Property.readwrite.gobject(SelectableRemote),
	search_results: Property.readwrite.gobject(ArrayStore<SearchResult>),
	is_searching: Property.readwrite.bool(),
	visible_stack_page: Property.readwrite.string("empty-search").as<StackPages>(),

	queue_add: Signal([ResultRow, Array<Remote>]),
	row_created: Signal([ResultRow]),

	_available_remotes: Child<Gtk.MapListModel<SelectableRemote>>(),
	_searchable_installations: Child<Gtk.FilterListModel<Installation>>(),
	_sorted_results: Child<Gtk.SortListModel<SearchResult>>(),
	_search_entry: Child<Gtk.SearchEntry>(),
	_remote_dropdown: Child<Gtk.DropDown>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
	_results_box: Child<Adw.PreferencesGroup>(),
}) {
	readonly #search_task = new SwitchTask((running) => {
		if (!running) {
			this._scrolled_window.vadjustment.value = 0
		}
		this.is_searching = running
	})
	readonly #package_id_set = new Set<string>()
	readonly #selected_results = new Map<string, ResultRow>() // keys: `<installation.name>::<result.application>`

	constructor(params?: typeof SelectPage.$params) {
		super(params)
		this._available_remotes.set_map_func((item) => new SelectableRemote({ remote: item as Remote }))
		this._remote_dropdown.list_factory = make_signal_factory(SelectableRemoteBox, SelectableRemote, {
			setup: () => new SelectableRemoteBox(),
			bind: (box, s_remote) => box.selectable_remote = s_remote,
			unbind: (box) => box.selectable_remote = null,
		})
		this._results_box.bind_model(this._sorted_results, (item) => {
			const result = item as SearchResult
			const kind = this.#package_id_set.has(result.application) ? "installed" : "addable"
			const row = new ResultRow({ result, kind })
			this.$emit("row-created", row)
			row.$connect("queue-add", () => {
				this.#selected_results.set(make_selected_results_keys(result), row)
				this.$emit("queue-add", row, result.get_remotes())
			})
			return row
		})
		this._remote_selected()
	}

	result_deslected(inst_name: string, application: string): void {
		// const row = this.#selected_results.get(`${inst_name}::${application}`)
		// if (row?.kind !== "added") return
		// row.kind = "addable"
		for (const row of this._results_box) {
			if (!(row instanceof ResultRow)) continue
			const result = row.result
			const row_inst_name = result?.installation?.name
			const app = result?.application
			if (!result || !row_inst_name || !app) continue
			if (row_inst_name === inst_name && app === application && row.kind === "added") {
				row.kind = "addable"
				break
			}
		}
	}

	@WatchProp("packages")
	#on_packages_changed(): void {
		this.packages?.connect("items-changed", () => this.#on_packages_items_changed())
		this.#on_packages_items_changed()
	}

	@Debounce(200)
	#on_packages_items_changed(): void {
		this.#package_id_set.clear()
		if (!this.packages) return
		for (const pack of iterate_list_model(this.packages)) {
			this.#package_id_set.add(pack.application)
		}
	}

	@WatchProp("selected_remote")
	protected async _search_changed(): Promise<void> {
		this.search_results = new ArrayStore()
		this.#selected_results.clear()

		const search = this._search_entry.get_text().trim()
		if (!search || search.length < 4) {
			this.#search_task.cancel()
			this.visible_stack_page = "empty-search"
			return
		}

		const selected_inst = this.selected_remote?.remote?.installation
		const insts: Iterable<Installation> = (selected_inst
			? [selected_inst]
			: iterate_list_model(this._searchable_installations)
		)

		const tasks: ((cancellable: Gio.Cancellable) => Promise<SearchResult[]>)[] = []
		for (const inst of insts) {
			tasks.push((cancellable) => search_packages(search, inst, this.selected_remote?.remote?.name, cancellable))
		}
		const batches = await this.#search_task.run_batch(tasks, (e) => print("Error when searching:", e))

		if (!batches) return
		const results = batches.flat()
		this.search_results.swap_contents(results)
		this.visible_stack_page = results.length > 0 ? "results-list" : "no-results"
	}

	protected _remote_selected(): void {
		this.selected_remote?.set_selected(false)
		this.selected_remote = this._remote_dropdown.selected_item as SelectableRemote | null
		this.selected_remote?.set_selected(true)
	}
}
