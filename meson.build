project(
	'warehouse',
	version: '2.3.0',
	meson_version: '>= 1.0.0',
	default_options: ['warning_level=2', 'werror=false'],
)

blueprint_compiler = find_program('blueprint-compiler')
gnome = import('gnome')
i18n = import('i18n')
python = find_program('python3')
tsc = find_program('tsc')
find_program('du')

pkgdatadir = get_option('datadir') / meson.project_name()
profile = get_option('profile')

subdir('data')
subdir('src')
subdir('po')
if get_option('tests')
	jasmine = find_program('jasmine')
	subdir('tests')
endif
gnome.post_install(
	glib_compile_schemas: true,
	gtk_update_icon_cache: true,
	update_desktop_database: true,
)
