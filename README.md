# chapter-marker v3
The third iteration of [chapter-marker](https://github.com/Binaergewitter/chapter-marker) to find the chapter marks for the binärgewitter podcast.
It utilizes state-of-the-art speech-to-text algorithms (google translate) to
transfer ingos voice to text which in a post-processing step is used by a
sophisticated heuristic (state machine) to calculate the chapters in the
[podlove simple-chapters format](https://github.com/podlove/podlove-specifications/blob/master/podlove-simple-chapters.md)

## Usage

`./doit.sh` should do it all. It assumes ingos chapters being stored in the
share `BGT<TODAY>/local.flac`


# Footnote
This page was previously blank
