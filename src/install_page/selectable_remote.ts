import GObject from "gi://GObject?version=2.0"

import { from, GClass, Property, WatchProp } from "../gobjectify/gobjectify.js"
import { Remote } from "../flatpak.js"
import Gtk from "gi://Gtk?version=4.0"

@GClass() export class SelectableRemote extends from(GObject.Object, {
	remote: Property.readwrite.gobject(Remote),
	selected: Property.readwrite.bool(),
	is_all: Property.readwrite.bool(),
}) {
	set_selected(to: boolean): void {
		this.selected = to
	}
}

@GClass({ template: "resource:///io/github/flattool/Warehouse/install_page/selectable_remote_box.ui" })
export class SelectableRemoteBox extends from(Gtk.Box, {
	selectable_remote: Property.readwrite.gobject(SelectableRemote),
	remote: Property.readwrite.gobject(SelectableRemote),
}) {
	protected _get_check_opacity(__: this, is_selected: boolean): number {
		return is_selected ? 1 : 0
	}

	protected _get_title_label(__: this, s_remote: SelectableRemote | null): string {
		return s_remote?.remote?.title ?? ""
	}

	protected _get_name_label(__: this, s_remote: SelectableRemote | null): string {
		return s_remote?.remote?.name ?? ""
	}

	protected _get_installation_label(__: this, s_remote: SelectableRemote | null): string {
		return _("Installation: %s").format(s_remote?.remote?.installation?.title ?? "")
	}
}
