# Copyright 2022-2025 TII (SSRC) and the Ghaf contributors
# SPDX-License-Identifier: Apache-2.0

{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShell {
  packages = with pkgs; [
    python313
    python313Packages.pygobject3
    python313Packages.virtualenv
    pkgs.python313Packages.setuptools
    pkgs.python313Packages.wheel
    pkgs.python313Packages.build
    gtk4
    gobject-introspection
    wayland
  ];

  shellHook = ''
    if [ ! -d .venv ]; then
      virtualenv .venv
      source .venv/bin/activate
    else
      source .venv/bin/activate
    fi
    echo "Welcome to usb-passthrough-manager development environment!"
  '';
}


