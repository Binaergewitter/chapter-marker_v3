{ pkgs ? import <nixpkgs> {}}:

pkgs.mkShell {
  buildInputs = with pkgs; [ 
    flac
    ffmpeg
    gcc
    python3.pkgs.torchaudio-bin
    python3.pkgs.pytorch-bin
    python3.pkgs.docopt
    python3.pkgs.pip
    python3.pkgs.pydub
    pkgs.stdenv.cc.cc.lib
    (python3.pkgs.callPackage ./speech_recognition.nix {})
    (python3.pkgs.callPackage ./stft.nix {})
  ];
  LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";

  shellHook = ''
    # Tells pip to put packages into $PIP_PREFIX instead of the usual locations.
    # See https://pip.pypa.io/en/stable/user_guide/#environment-variables.
    export PIP_PREFIX=$(pwd)/_build/pip_packages
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python3.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    unset SOURCE_DATE_EPOCH
  '';
}
