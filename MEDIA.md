# Scholar essay → private book and video drafts

The reader's **Prepare video and book** button saves the selected essay first,
then downloads a `scholar-media/1` JSON packet from that exact account revision.
The packet is a local download containing the essay, citation records, revision
and hashes. No paper or audio is sent to the public `/api/read` endpoint. A packet
is private, editable data; its hashes detect changes, not identity or approval.

The matching `codex/scholar-media` changes in `prx0r/svread`, `prx0r/visuals`
and `prx0r/bookfactory` are required together. After deploying the reader,
render a downloaded packet on a trusted machine:

```sh
python3 -m pip install -r requirements-paper.txt
# Also install ffmpeg/ffprobe built with libflite, libx264 and AAC.
python3 paper.py render --input /private/downloads/essay-media.json \
  --visuals ../visuals --output /private/outputs/essay-draft
python3 paper.py verify --output /private/outputs/essay-draft
```

This produces an A5 book HTML and PDF, H.264/AAC MP4, SRT captions, reading
transcript, source packet, per-segment offsets/hashes, and a result manifest.
The output directory is private (mode 0700); an existing destination is never
overwritten. Markdown formatting is rendered safely for the book. External
images are shown as references: the book renderer never fetches external URLs.
Video and speech remove common Markdown decoration. The packet keeps the
original text; the segment index records source offsets and hashes, and the
manifest hashes both files.

The voice is **offline Flite SLT**, a basic machine voice for a quick proof. It
can mispronounce Sanskrit, mathematical notation and names. Captions are timed
per generated speech segment; the still-image video runs at 1 fps, so the visual
cut can differ slightly from the caption boundary. Review the full video and
captions; this does not use the video factory's approved voices, golden seal or
publication gates. The A5 PDF is also a draft: review its text, fonts, layout,
rights, page count, cover and KDP preflight before using it for print.

**Current boundary:** the button downloads a packet; it does not trigger a
server-side render or publish to the web. The trusted local runner does the
render, and all outputs remain private until the author chooses to share them.
Do not commit a scholar's private packet or output, or upload it to a public
bucket. A real hosted queue and high-quality provider would need explicit
consent, private storage, account-scoped access, cost controls, and separate
review before public publication.

## Reproduce the real example

From sibling checkouts of `prx0r/ipvv`, `prx0r/bookfactory` and `prx0r/visuals`:

```sh
python3 paper.py package-git --repo ../ipvv \
  --file ../ipvv/site/data/essays/ESSAY-RECOGNITION-AND-FORMAL-PROOFS.md \
  --repository prx0r/ipvv --work ipvv --output /tmp/recognition-packet.json
python3 paper.py render --input /tmp/recognition-packet.json \
  --visuals ../visuals --output /tmp/recognition-draft
python3 paper.py verify --output /tmp/recognition-draft
```

`package-git` refuses a file that differs from its committed Git revision or a
repository name that differs from the remote. The example is the complete
1,486-word essay, not an invented or shortened text. Git provenance, not a
Scholar account sign-off, is recorded for this example.

The source-pinned packet, draft PDF, captions and segment index from a real run
are also checked in under `examples/recognition-and-formal-proofs/`. That
example uses an essay already committed in Git; do not commit private Scholar
packets or outputs.

Tests: `python3 -m unittest discover -s tests -p 'test_paper.py' -v` in this
repository, and `node --test tests/scholar-media.test.cjs` in svread.
