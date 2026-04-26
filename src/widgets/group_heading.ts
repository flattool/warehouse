import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, Child, from, Signal } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/group_heading.ui" })
@Signal("clicked")
export class GroupHeading extends from(Gtk.Box, {
	title: Property.string(),
	subtitle: Property.string(),
	header_child: Property.gobject(Gtk.Widget),
	_label_box: Child<Gtk.Box>(),
}) {
	_ready(): void {
		const gesture = new Gtk.GestureClick()
		gesture.connect("released", () => this.emit("clicked"))
		this._label_box.add_controller(gesture)
	}
}
