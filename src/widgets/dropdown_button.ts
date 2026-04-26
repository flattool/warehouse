import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/dropdown_button.ui" })
export class DropdownButton extends from(Gtk.Button, {
	collapsed_text: Property.string({ default: "Show" }),
	expanded_text: Property.string({ default: "Hide" }),
	active: Property.bool(),
}) {
	_ready(): void {
		this._on_active_changed()
	}

	protected _on_clicked(): void {
		this.active = !this.active
	}

	protected _on_active_changed(): void {
		if (this.active) {
			this.add_css_class("expanded")
		} else {
			this.remove_css_class("expanded")
		}
	}

	protected _get_label(): string {
		return this.active ? this.expanded_text : this.collapsed_text
	}

	protected _get_icon_name(): string {
		return "adw-expander-arrow-symbolic"
	}
}
