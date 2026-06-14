// This exists due to Blueprint's Menus being limited, and GtkBuilder menus being initialized in the wrong context
import Gio from "gi://Gio?version=2.0"
import GLib from "gi://GLib?version=2.0"

type MenuTarget = GLib.Variant | string | boolean | number

export type MenuItemConfig = {
	label: string,
	action?: string,
	target?: MenuTarget,
	icon?: string | Gio.Icon,
	hidden_when?: "action-disabled" | "action-missing" | "action-and-target-absent",
}

const resolve_variant = (target: MenuTarget): GLib.Variant => {
	switch (typeof target) {
		case "string": return GLib.Variant.new_string(target)
		case "number": return GLib.Variant.new_double(target)
		case "boolean": return GLib.Variant.new_boolean(target)
	}
	return target
}

class MenuBuilder {
	readonly #menu = new Gio.Menu()

	build(): Gio.Menu { return this.#menu }

	item(config: MenuItemConfig): this {
		const item = Gio.MenuItem.new(config.label, config.action || null)
		if (config.target !== undefined) {
			item.set_attribute_value("target", resolve_variant(config.target))
		}
		if (config.icon) {
			item.set_icon(typeof config.icon === "string" ? Gio.ThemedIcon.new(config.icon) : config.icon)
		}
		if (config.hidden_when) {
			item.set_attribute_value("hidden-when", GLib.Variant.new_string(config.hidden_when))
		}
		this.#menu.append_item(item)
		return this
	}

	section(label: string | null, a_section: MenuBuilder | Gio.MenuModel): this {
		this.#menu.append_section(label, a_section instanceof MenuBuilder ? a_section.build() : a_section)
		return this
	}

	submenu(label: string | null, a_submenu: MenuBuilder | Gio.MenuModel): this {
		this.#menu.append_submenu(label, a_submenu instanceof MenuBuilder ? a_submenu.build() : a_submenu)
		return this
	}
}

export const make_menu = (): MenuBuilder => new MenuBuilder()
