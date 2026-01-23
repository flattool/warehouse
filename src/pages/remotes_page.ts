import { GClass } from "../gobjectify/gobjectify.js"
import { BasePage } from "./base_page.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/pages/remotes_page.ui" })
export class RemotesPage extends BasePage {}
