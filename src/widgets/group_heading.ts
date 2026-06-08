import Gtk from "gi://Gtk?version=4.0"

import { GClass, Property, Child, from, Signal } from "../gobjectify/gobjectify.js"

@GClass({ template: "resource:///io/github/flattool/Warehouse/widgets/group_heading.ui" })
export class GroupHeading extends from(Gtk.Box, {
	title: Property.readwrite.string(),
	subtitle: Property.readwrite.string(),
	header_child: Property.readwrite.gobject(Gtk.Widget),
	clicked: Signal(),
	_label_box: Child<Gtk.Box>(),
}) {
	constructor(params?: typeof GroupHeading.$params) {
		super(params)
		const gesture = new Gtk.GestureClick()
		gesture.$connect("released", () => this.emit("clicked"))
		this._label_box.add_controller(gesture)
	}
}
