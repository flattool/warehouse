pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'Warehouse')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'widgets/app_row.blp',
    'widgets/status_box.blp',
    'gtk/help-overlay.blp',
    'main_window/window.blp',
    'packages_page/packages_page.blp',
    'filters_page/filters_page.blp',
    'properties_page/properties_page.blp',
    'change_version_page/change_version_page.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('warehouse',
  'warehouse.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('APPID', 'io.github.flattool.Warehouse') # TODO: dynamic version and appID
if get_option('profile') == 'development'
  vcs_tag = run_command('git', 'rev-parse', '--short', 'HEAD').stdout().strip()
  conf.set('DEVEL', 'Development')
  conf.set('VERSION', meson.project_version() + '.dev-' + vcs_tag)
else
  conf.set('DEVEL', 'Default')
  conf.set('VERSION', meson.project_version())
endif
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'warehouse.in',
  output: 'warehouse',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

warehouse_sources = [
  '__init__.py',
  'main.py',
  'host_info.py',
  'widgets/app_row.py',
  'widgets/error_toast.py',
  'widgets/status_box.py',
  'main_window/window.py',
  'packages_page/packages_page.py',
  'filters_page/filters_page.py',
  'properties_page/properties_page.py',
  'change_version_page/change_version_page.py',
  '../data/style.css',
]

configure_file(
  input: 'const.py.in',
  output: 'const.py',
  configuration: conf,
  install: true,
  install_dir: moduledir,
  install_mode: 'r-xr--r--',
)

install_data(warehouse_sources, install_dir: moduledir)
