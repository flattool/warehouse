#!/usr/bin/env sh
set -euo pipefail

rm -rf _build

# Needed to escape weird envvars provided mainly by Nix flakes
flatpak run \
	--unset-env=GDK_PIXBUF_MODULE_FILE \
	--unset-env=GIO_EXTRA_MODULES \
	--unset-env=GI_TYPELIB_PATH \
	org.flatpak.Builder --install --user --force-clean _build build-aux/io.github.flattool.Warehouse.json

flatpak run io.github.flattool.Warehouse//master
