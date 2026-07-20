import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gio from "gi://Gio?version=2.0"

import { Child, from, GClass, Property, WatchProp } from "../gobjectify/gobjectify.js"
import { Installation, Remote, search_packages, SearchResult } from "../flatpak.js"
import { ArrayStore } from "../utils/array_store.js"
import { iterate_list_model, make_signal_factory } from "../utils/helper_funcs.js"
import { SelectableRemote, SelectableRemoteBox } from "./selectable_remote.js"
import { ResultRow } from "./result_row.js"
import { SwitchTask } from "../utils/switch_task.js"

import "../widgets/sidebar_button.js"
import "../widgets/loading_group.js"

type StackPages = "empty-search" | "results-list" | "no-results"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/select_page.ui" })
export class SelectPage extends from(Adw.Bin, {
	installations: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Installation>>(),
	remotes: Property.readwrite.gobject(Gio.ListModel).as<Gio.ListModel<Remote>>(),
	selected_remote: Property.readwrite.gobject(SelectableRemote),
	search_results: Property.readwrite.gobject(ArrayStore<SearchResult>),
	is_searching: Property.readwrite.bool(),
	visible_stack_page: Property.readwrite.string("empty-search").as<StackPages>(),
	_available_remotes: Child<Gtk.MapListModel<SelectableRemote>>(),
	_sorted_results: Child<Gtk.SortListModel<SearchResult>>(),
	_search_entry: Child<Gtk.SearchEntry>(),
	_remote_dropdown: Child<Gtk.DropDown>(),
	_results_box: Child<Adw.PreferencesGroup>(),
}) {
	readonly #search_task = new SwitchTask<SearchResult[]>((running) => this.is_searching = running)

	constructor(params?: typeof SelectPage.$params) {
		super(params)
		this._available_remotes.set_map_func((item) => new SelectableRemote({ remote: item as Remote }))
		this._remote_dropdown.list_factory = make_signal_factory(SelectableRemoteBox, SelectableRemote, {
			setup: () => new SelectableRemoteBox(),
			bind: (box, s_remote) => box.selectable_remote = s_remote,
			unbind: (box) => box.selectable_remote = null,
		})
		this._results_box.bind_model(this._sorted_results, (item) => new ResultRow({ result: item as SearchResult }))
		this._remote_selected()
	}

	@WatchProp("selected_remote")
	protected async _search_changed(): Promise<void> {
		this.search_results = new ArrayStore()

		const search = this._search_entry.get_text().trim()
		if (!search || search.length < 4) {
			this.#search_task.cancel()
			this.visible_stack_page = "empty-search"
			return
		}

		const selected_inst = this.selected_remote?.remote?.installation
		let insts: IterableIterator<Installation>
		if (selected_inst) {
			insts = [selected_inst][Symbol.iterator]()
		} else if (this.installations) {
			insts = iterate_list_model(this.installations)
		} else {
			insts = [][Symbol.iterator]()
		}

		let results: SearchResult[] = []
		for (const inst of insts) {
			const inst_result = await this.#search_task.run(
				(cancellable) => search_packages(search, inst, this.selected_remote?.remote?.name, cancellable),
			).catch(
				(e) => print("Error when searching:", e),
			)
			if (!inst_result || inst_result.length < 1) continue
			results.push(...inst_result)
		}

		this.search_results.swap_contents(results)
		this.visible_stack_page = results.length > 0 ? "results-list" : "no-results"
	}

	protected _remote_selected(): void {
		this.selected_remote?.set_selected(false)
		this.selected_remote = this._remote_dropdown.selected_item as SelectableRemote | null
		this.selected_remote?.set_selected(true)
	}
}
