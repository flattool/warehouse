import { GClass } from "../gobjectify/gobjectify.js"
import { BasePage } from "../widgets/base_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/packages_page.ui" })
export class PackagesPage extends BasePage {}
