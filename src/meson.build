pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'flattool_gui')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'gtk/help-overlay.blp',
    '../data/ui/window.blp',
    '../data/ui/orphans.blp',
    '../data/ui/filter.blp',
    '../data/ui/popular_remotes.blp',
    '../data/ui/remotes.blp',
    '../data/ui/downgrade.blp',
    '../data/ui/search_install.blp',
    '../data/ui/snapshots.blp',
    '../data/ui/properties.blp',
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
  'common.py',
  'window.py',
  'popular_remotes_window.py',
  'app_row_widget.py',
  '../data/style.css',
  
  'properties_window.py',
  '../data/ui/properties.blp',
  
  'orphans_window.py',
  '../data/ui/orphans.blp',
  
  'remotes_window.py',
  '../data/ui/remotes.blp',
  
  'filter_window.py',
  '../data/ui/filter.blp',
  
  'downgrade_window.py',
  '../data/ui/downgrade.blp',
  
  'search_install_window.py',
  '../data/ui/search_install.blp',
  
  'snapshots_window.py',
  '../data/ui/snapshots.blp',
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
