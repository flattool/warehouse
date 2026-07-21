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
		this._select_page.$connect(
			"queue-add",
			(__, result, remotes) => {
				const remote = remotes?.[0]
				if (!result || !remote) return
				this._pending_page.add(result, remote)
			},
		)
	}

	protected _get_visible_page(__: this, loading: boolean, installing: boolean): PageNamges {
		if (loading) return "loading-page"
		if (installing) return "installing-page"
		return "content-page"
	}
}
