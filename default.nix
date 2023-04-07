{
  pkgs ? import <nixpkgs> {},
  python ? "python3",
  pythonPackages ? builtins.getAttr (python + "Packages") pkgs,
}:
with pythonPackages;
  buildPythonApplication rec {
    pname = "qbpm";
    version = "1.0-rc2";
    pyproject = true;
    src = ./.;
    doCheck = true;

    build-system = [setuptools];
    nativeBuildInputs = [pkgs.scdoc];
    dependencies = [pyxdg click httpx pillow];
    nativeCheckInputs = [pytestCheckHook];

    postInstall = ''
      install -D -m644 completions/qbpm.fish $out/share/fish/vendor_completions.d/qbpm.fish

      install -vd $out/share/{bash-completion/completions,zsh/site-functions}
      _QBPM_COMPLETE=bash_source $out/bin/qbpm > $out/share/bash-completion/completions/qbpm
      _QBPM_COMPLETE=zsh_source $out/bin/qbpm > $out/share/zsh/site-functions/qbpm

      mkdir -p $out/share/man/man1
      scdoc < qbpm.1.scd > $out/share/man/man1/qbpm.1
    '';

    meta = {
      homepage = "https://github.com/pvsr/qbpm";
      changelog = "https://github.com/pvsr/qbpm/blob/main/CHANGELOG.md";
      description = "A profile manager for qutebrowser";
      license = lib.licenses.gpl3Plus;
    };
  }
