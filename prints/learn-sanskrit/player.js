// lesson player — videofactory Fish voice + karaoke hook (ipvv-style)
(function () {
  var AUDIO_MANIFEST = null;
  fetch("audio-manifest.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (m) { AUDIO_MANIFEST = m; })
    .catch(function () {});
  var au = document.getElementById("lesson-audio");
  if (!au) return;
  var lessonId = document.body.getAttribute("data-lesson") || "";
  function urlFor(kind) {
    if (!AUDIO_MANIFEST || !AUDIO_MANIFEST.clips) return null;
    return AUDIO_MANIFEST.clips[lessonId + "__" + kind] || null;
  }
  function mark(kind, on) {
    document.querySelectorAll(".vplay").forEach(function (b) {
      b.classList.toggle("on", !!on && b.getAttribute("data-play") === kind);
    });
  }
  function speak(kind) {
    try {
      speechSynthesis.cancel();
      var el = document.querySelector(".iast");
      var u = new SpeechSynthesisUtterance(String(el ? el.textContent : "").slice(0, 1200));
      u.rate = 0.95;
      u.onend = function () { mark(kind, false); };
      speechSynthesis.speak(u);
      mark(kind, true);
      var n = document.getElementById("play-note");
      if (n) n.textContent = "browser voice (Fish clip not rendered yet)";
    } catch (e) {}
  }
  document.querySelectorAll(".vplay[data-play]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var kind = btn.getAttribute("data-play");
      var src = urlFor(kind);
      if (src) {
        au.src = src;
        au.play().then(function () {
          mark(kind, true);
          var n = document.getElementById("play-note");
          if (n) n.textContent = "Fish " + kind + " clip";
        }).catch(function () { speak(kind); });
      } else {
        speak(kind);
      }
    });
  });
  au.addEventListener("ended", function () { mark(null, false); });
})();
