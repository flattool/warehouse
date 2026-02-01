export type PopularRemote = {
	readonly title: string,
	readonly name: string,
	readonly link: string,
	readonly description: string,
}

export const popular_remotes: PopularRemote[] = [
	{
		title: "AppCenter",
		name: "appcenter",
		link: "https://flatpak.elementary.io/repo.flatpakrepo",
		description: _("The open source, pay-what-you-want app store from elementary"),
	},
	{
		title: "Flathub",
		name: "flathub",
		link: "https://dl.flathub.org/repo/flathub.flatpakrepo",
		description: _("Central repository of Flatpak applications"),
	},
	{
		title: "Flathub beta",
		name: "flathub-beta",
		link: "https://flathub.org/beta-repo/flathub-beta.flatpakrepo",
		description: _("Beta builds of Flatpak applications"),
	},
	{
		title: "Fedora",
		name: "fedora",
		link: "oci+https://registry.fedoraproject.org",
		description: _("Flatpaks packaged by Fedora Linux"),
	},
	{
		title: "GNOME Nightly",
		name: "gnome-nightly",
		link: "https://nightly.gnome.org/gnome-nightly.flatpakrepo",
		description: _("The latest beta GNOME Apps and Runtimes"),
	},
	{
		title: "WebKit Developer SDK",
		name: "webkit-sdk",
		link: "https://software.igalia.com/flatpak-refs/webkit-sdk.flatpakrepo",
		description: _("Central repository of the WebKit Developer and Runtime SDK"),
	},
] as const
