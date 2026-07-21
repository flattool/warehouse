import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gdk from "gi://Gdk?version=4.0"
import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"

import { from, GClass, Child, Property, Signal, SimplerAction } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"
import { SelectPage } from "./select_page.js"
import { PendingPage } from "./pending_page.js"

import "../widgets/sidebar_button.js"

type PageNamges = "installing-page" | "loading-page" | "content-page"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/install_page.ui" })
export class InstallPage extends from(BasePage, {
	installing: Property.readwrite.bool(),
	_select_page: Child<SelectPage>(),
	_pending_page: Child<PendingPage>(),
}) {
	constructor(params?: typeof InstallPage.$params) {
		params ??= {}
		params.icon_name = "warehouse:arrow-pointing-at-line-down-symbolic"
		params.sidebar_title = _("Install Packages")
		super(params)
		this._select_page.$connect("queue-add", (__, row, remotes) => {
			const remote = remotes?.[0]
			const result = row?.result
			const installation = result?.installation
			if (!result || !remote || !installation) return
			this._pending_page.add(result, remote)
			if (this._pending_page.has_result_by_id(installation, result.application)) {
				row.kind = "added"
			}
		})
		this._select_page.$connect("row-created", (__, row) => {
			const result = row?.result
			const installation = result?.installation
			if (!row || !result || !installation) return
			if (this._pending_page.has_result_by_id(installation, result.application)) {
				row.kind = "added"
			}
		})
		this._pending_page.$connect("queue-remove", (__, result) => {
			const inst_name = result?.installation?.name
			const app = result?.application
			if (!inst_name || !app) return
			this._select_page.result_deslected(inst_name, app)
		})
	}

	// TODO: reset select and pending pages when the loading prop changes

	protected _get_visible_page(__: this, loading: boolean, installing: boolean): PageNamges {
		if (loading) return "loading-page"
		if (installing) return "installing-page"
		return "content-page"
	}

	protected _get_reveal_bottom_bar(__: this, n_pending: number): boolean {
		return n_pending > 0
	}

	protected _get_pending_label(__: this, n_pending: number): string {
		return _("Pending Packages: %s").format(n_pending)
	}
}
