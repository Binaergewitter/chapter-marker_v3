{ lib
, buildPythonPackage
, fetchPypi
, pyaudio
, google-cloud-speech
, flac
, callPackage
, python
}:

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
    tar xf ${./cmusphinx-de-voxforge-5.2.tar.gz} -C /tmp
    indir=/tmp/cmusphinx-cont-voxforge-de-r20171217
    mv $indir/etc/voxforge.lm.bin $datadir/language-model.lm.bin
    mv $indir/etc/voxforge.dic $datadir/pronounciation-dictionary.dict
    mv $indir/model_parameters/voxforge.cd_cont_6000/ $datadir/acoustic-model
  '';
  doCheck = false;
  propagatedBuildInputs = [
    pyaudio
    (callPackage ./pocketsphinx.nix {})
    google-cloud-speech
  ];
}
