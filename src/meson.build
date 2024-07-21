pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'Warehouse')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'packages_page/app_row.blp',
    'gtk/help-overlay.blp',
    'main_window/window.blp',
    'packages_page/packages_page.blp',
    'packages_page/filters_page.blp',
    'properties_page/properties_page.blp',
    'user_data_page/data_box.blp',
    'user_data_page/user_data_page.blp',
    'user_data_page/data_subpage.blp',
    'remotes_page/remotes_page.blp',
    'remotes_page/remote_row.blp',
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
  'packages_page/app_row.py',
  'gtk/error_toast.py',
  'main_window/window.py',
  'packages_page/packages_page.py',
  'packages_page/filters_page.py',
  'properties_page/properties_page.py',
  'change_version_page/change_version_page.py',
  'user_data_page/data_box.py',
  'user_data_page/user_data_page.py',
  'user_data_page/data_subpage.py',
  'remotes_page/remotes_page.py',
  'remotes_page/remote_row.py',
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
