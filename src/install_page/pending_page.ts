import Adw from "gi://Adw?version=1"

import { from, GClass } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/pending_page.ui" })
export class PendingPage extends from(Adw.NavigationPage, {}) {}
