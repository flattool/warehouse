pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'flattool_gui')
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('flattool-gui',
  'flattool-gui.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'flattool-gui.in',
  output: 'flattool-gui',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

flattool_gui_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'show_properties_window.py',
]

install_data(flattool_gui_sources, install_dir: moduledir)
