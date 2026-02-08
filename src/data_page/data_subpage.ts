import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_subpage.ui" })
export class DataSubpage extends from(Adw.Bin, {
	show_leftover: Property.bool(),
}) {}
