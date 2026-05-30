{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    git
    libopus                          # required by pymumble even with audio disabled
    (python3.withPackages (ps: [
      ps.tkinter                     # GUI toolkit
    ]))
  ];
}
