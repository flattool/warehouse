import Gtk from "gi://Gtk?version=4.0"

import { GClass, PostInit, Property, from } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/dropdown_button.ui" })
export class DropdownButton extends from(Gtk.Button, {
	collapsed_text: Property.readwrite.string("Show"),
	expanded_text: Property.readwrite.string("Hide"),
	active: Property.readwrite.bool(),
}) {
	protected _on_clicked(): void {
		this.active = !this.active
	}

	@PostInit
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
