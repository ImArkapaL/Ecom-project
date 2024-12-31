{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.postgresql
    pkgs.openssl
  ];
}
