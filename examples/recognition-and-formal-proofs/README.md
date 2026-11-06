# Real IPVV essay: draft media handover

This example uses the complete essay already committed to `prx0r/ipvv` at
`48f2a5c5fc757c3b620b0216c0901f519875d3e4`, path
`site/data/essays/ESSAY-RECOGNITION-AND-FORMAL-PROOFS.md`. It is a Git-source
example, not an export of a scholar's private account. See `MEDIA.md` before
handling any private Scholar packet; never commit a private packet or output.

The checked-in packet, nine-page A5 PDF, captions and segment index come from
one successful local run. The packet pins the exact source and text hashes;
each segment records offsets into that text. The result manifest records all
output hashes and the two renderer hashes for that run. The example generated
57 segments and about 10 minutes of offline narration. The video, fonts and
HTML are omitted from this small Git handover; consequently this folder alone
is not a complete output directory for `paper.py verify`.

To reproduce the full video, PDF, transcript and manifest, check out the
matching `codex/scholar-media` branches of `bookfactory` and `visuals`, install
the dependencies in `MEDIA.md`, then from `bookfactory` run:

```sh
python3 paper.py render \
  --input examples/recognition-and-formal-proofs/source-packet.json \
  --visuals ../visuals --output /tmp/recognition-draft
python3 paper.py verify --output /tmp/recognition-draft
```

Output bytes and timings can vary with system fonts, FFmpeg and library
versions; verify against the manifest produced by the same run. The existing
PDF and captions are draft proofs, not author sign-off or publication approval.
Review the basic voice's pronunciation and the nine-page book before use.
