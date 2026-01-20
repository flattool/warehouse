#!/usr/bin/env sh
flatpak run org.flatpak.Builder --install --user --force-clean _build build-aux/io.github.flattool.Warehouse.json \
&& flatpak run io.github.flattool.Warehouse//master
