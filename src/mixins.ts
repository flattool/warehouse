import GLib from "gi://GLib?version=2.0"

declare global {
	interface String {
		markup_escape_text(this: string): string
	}
}

String.prototype.markup_escape_text = function (): string {
	return GLib.markup_escape_text(this, -1)
}
