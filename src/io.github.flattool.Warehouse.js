#!@GJS@ -m

import Gio from "gi://Gio?version=2.0"

import { exit, programArgs, programInvocationName } from "system"

imports.package.init({
	name: "@PACKAGE_NAME@",
	version: "@VERSION@",
	prefix: "@prefix@",
	libdir: "@libdir@",
	datadir: "@datadir@",
})

pkg.profile = "@PROFILE@"
pkg.app_id = "@APP_ID@"
pkg.package_version = "@PACKAGE_VERSION@"

// Initialize translations and formatting
pkg.initGettext()
pkg.initFormat()

// Load GResources
const ui_resource = Gio.Resource.load(`${pkg.pkgdatadir}/ui.gresource`)
Gio.resources_register(ui_resource)
const icon_resource = Gio.Resource.load(`${pkg.pkgdatadir}/icons.gresource`)
Gio.resources_register(icon_resource)

const { main } = await import(`file://${pkg.pkgdatadir}/src/main.js`)
const exit_code = await main([programInvocationName, ...programArgs])
exit(exit_code)
