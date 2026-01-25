import { GClass } from "../gobjectify/gobjectify.js"
import { BasePage } from "./base_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/pages/packages_page.ui" })
export class PackagesPage extends BasePage {}
