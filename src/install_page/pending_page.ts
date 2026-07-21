import Adw from "gi://Adw?version=1"

import { from, GClass } from "../gobjectify/gobjectify.js"
import { Remote, type SearchResult } from "../flatpak.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/pending_page.ui" })
export class PendingPage extends from(Adw.Bin, {}) {
	add(result: SearchResult, remote: Remote): void {
		print(result, remote)
	}
}
