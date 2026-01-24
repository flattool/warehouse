import type Adw from "gi://Adw?version=1"
import type Gio from "gi://Gio?version=2.0"

import type { Installation } from "../flatpak.js"

export interface BasePage extends Adw.NavigationPage {
	readonly installations: Gio.ListStore<Installation> | null
	sidebar_title: string
	icon_name: string
}
