// lesson player — Fish seats (sadhguru/osho/gurudeep/vf_verse) + karaoke hook
(function () {
  var M = null;
  fetch("audio-manifest.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (m) { M = m; paintSeats(); })
    .catch(function () {});
  var au = document.getElementById("lesson-audio");
  if (!au) return;
  var lessonId = document.body.getAttribute("data-lesson") || "";
  var seat = null; // null = default from manifest

  function urlFor(kind) {
    if (!M) return null;
    var base = lessonId + "__" + kind;
    if (kind === "verse" && seat && M.clips_by_seat && M.clips_by_seat[base]) {
      return M.clips_by_seat[base][seat] || M.clips[base] || null;
    }
    return (M.clips && M.clips[base]) || null;
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
      if (n) n.textContent = "browser voice (Fish clip missing for this seat)";
    } catch (e) {}
  }
  function play(kind) {
    var src = urlFor(kind);
    if (src) {
      au.src = src;
      au.play().then(function () {
        mark(kind, true);
        var n = document.getElementById("play-note");
        if (n) n.textContent = "Fish " + kind + (seat ? " · " + seat : "");
      }).catch(function () { speak(kind); });
    } else {
      speak(kind);
    }
  }
  document.querySelectorAll(".vplay[data-play]").forEach(function (btn) {
    btn.addEventListener("click", function () { play(btn.getAttribute("data-play")); });
  });
  au.addEventListener("ended", function () { mark(null, false); });

  function paintSeats() {
    var host = document.getElementById("seat-row");
    if (!host || !M || !M.seats) return;
    host.innerHTML = "";
    ["sadhguru", "osho", "gurudeep", "vf_verse"].forEach(function (s) {
      if (!M.seats[s]) return;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "vplay seat" + ((seat || M.default_sanskrit_seat) === s ? " on" : "");
      b.textContent = s;
      b.addEventListener("click", function () {
        seat = s;
        host.querySelectorAll(".vplay").forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on");
        au.pause();
        mark(null, false);
        var n = document.getElementById("play-note");
        if (n) n.textContent = "seat " + s + " — hit recite";
      });
      host.appendChild(b);
    });
    var a = document.createElement("a");
    a.href = "http://127.0.0.1:8600/voice_shootout/";
    a.target = "_blank";
    a.className = "mut";
    a.style.marginLeft = ".5rem";
    a.textContent = "shootout";
    host.appendChild(a);
  }
})();
