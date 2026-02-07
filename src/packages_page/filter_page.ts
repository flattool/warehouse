import Adw from "gi://Adw?version=1"

import { GClass } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/filter_page.ui" })
export class FilterPage extends Adw.NavigationPage {}
