#!/bin/sh
#
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020 Christian Hergert <christian@hergert.me>
# Reference: https://gitlab.gnome.org/GNOME/gnome-builder/-/blob/main/build-aux/flatpak/fusermount-wrapper.sh?ref_type=heads

if [ -z "$_FUSE_COMMFD" ]; then
    FD_ARGS=
else
    FD_ARGS="--env=_FUSE_COMMFD=${_FUSE_COMMFD} --forward-fd=${_FUSE_COMMFD}"
fi

exec flatpak-spawn --host --forward-fd=1 --forward-fd=2 --forward-fd=3 $FD_ARGS fusermount "$@"
