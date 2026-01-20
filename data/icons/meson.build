application_id = 'io.github.flattool.Warehouse'

scalable_dir = 'hicolor' / 'scalable' / 'apps'
install_data(
	scalable_dir / ('@0@.svg').format(application_id),
	install_dir: get_option('datadir') / 'icons' / scalable_dir,
)

symbolic_dir = 'hicolor' / 'symbolic' / 'apps'
install_data(
	symbolic_dir / ('@0@-symbolic.svg').format(application_id),
	install_dir: get_option('datadir') / 'icons' / symbolic_dir,
)

icons = custom_target(
	'icons',
	input: files('icons.gresource.xml'),
	output: 'icons.gresource.xml',
	build_by_default: true,
	build_always_stale: true,
	command: [
		python,
		files('meson_icon_compile.py'),
		meson.current_source_dir(),
		'@INPUT@',
		'@OUTPUT@',
	],
)

gnome.compile_resources(
	'icons',
	icons,
	gresource_bundle: true,
	install: true,
	install_dir: pkgdatadir,
	dependencies: [icons],
)
