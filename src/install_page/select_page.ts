import Adw from "gi://Adw?version=1"

import { from, GClass } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/select_page.ui" })
export class SelectPage extends from(Adw.NavigationPage, {}) {}
