import Adw from "gi://Adw?version=1"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"

import "./data_subpage.js"
import "../widgets/search_button.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/data_page/data_page.ui" })
export class DataPage extends from(BasePage, {}) {}
