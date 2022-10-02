{ lib
, buildPythonPackage
, fetchPypi
, pyaudio
, google-cloud-speech
, flac
, callPackage
, python
, fetchurl
}:
let
  cmusphinx-data = fetchurl {
    url = "https://deac-riga.dl.sourceforge.net/project/cmusphinx/Acoustic%20and%20Language%20Models/German/cmusphinx-de-voxforge-5.2.tar.gz";
      sha256 = "0gci1k26ziysqmn5jjhsr6dlwrn9yhdnwnamibvx15x69nbyvkg9";
    };
in
buildPythonPackage rec {
  pname = "speech_recognition";
  version = "3.8.1";

  src = ./speech_recognition;
  buildInputs = [
    flac
  ];
  postInstall = ''
    datadir=$out/lib/${python.libPrefix}/site-packages/speech_recognition/pocketsphinx-data/de-DE/
    mkdir -p "$datadir"
  '';
  doCheck = false;
  propagatedBuildInputs = [
    pyaudio
    google-cloud-speech
  ];
}
