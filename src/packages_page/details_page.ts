import Adw from "gi://Adw?version=1"
import Gtk from "gi://Gtk?version=4.0"
import Gdk from "gi://Gdk?version=4.0"
import GLib from "gi://GLib?version=2.0"

import { GClass, Child, Property, from, OnSignal } from "../gobjectify/gobjectify.js"
import { SharedVars } from "../utils/shared_vars.js"
import { Package } from "../flatpak.js"

const BACKGROUND_PICTURE_OFFSET = -80

const css_provider = new Gtk.CssProvider()

function load_css_translation(y: number): void {
	css_provider.load_from_data(`
		.details-blurred {
			filter: blur(200px);
			transform: translateY(${y + BACKGROUND_PICTURE_OFFSET}px);
		}
		@media (prefers-color-scheme: dark) {
			.details-blurred {
				opacity: 0.5;
			}
		}
		@media (prefers-contrast: more) {
			.details-blurred {
				filter: none;
				opacity: 1;
			}
		}
	`, -1)
}

@GClass({ template: "resource:///io/github/flattool/Warehouse/packages_page/details_page.ui" })
export class DetailsPage extends from(Adw.NavigationPage, {
	flatpak: Property.gobject(Package),
	show_title: Property.bool(),
	_background_picture: Child<Gtk.Picture>(),
	_scrolled_window: Child<Gtk.ScrolledWindow>(),
}) {
	_ready(): void {
		load_css_translation(0)
		Gtk.StyleContext.add_provider_for_display(
			Gdk.Display.get_default()!,
			css_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		const vadjustment: Gtk.Adjustment = this._scrolled_window.vadjustment
		vadjustment.connect("value-changed", () => {
			const value = vadjustment.value
			this.show_title = value > 0
			load_css_translation(-value)
		})
	}
}
