(function () {
  "use strict";

  // Prevent duplicate initialization if script is re-run.
  if (window.__celdraCornerLoaded || document.getElementById("celdra-corner")) {
    return;
  }
  window.__celdraCornerLoaded = true;

  var CONFIG = {
    id: "celdra-corner",
    imageUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/celdra.png",
    speechLines: [
      "Celdra is watching...",
      "The hatchling stirs.",
      "Chat energy rising.",
      "Serenial feels alive tonight."
    ],
    quietAfterMs: 90000,      // quiet room -> sleepy
    burstWindowMs: 20000,     // rolling chat window
    excitedThreshold: 4,      // messages in rolling window -> excited
    excitedDurationMs: 7000,
    speakingDurationMs: 4500,
    minSpeechGapMs: 24000,
    maxSpeechGapMs: 46000,
    motdSelector: "#motd",
    mountRetryLimit: 25
  };

  var state = "idle";
  var messageTimes = [];
  var lastMessageAt = Date.now();
  var stateTimeout = null;
  var speechTimeout = null;
  var heartbeatTimer = null;

  var nodes = {
    root: null,
    bubble: null
  };

  function now() {
    return Date.now();
  }

  function randomRange(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function pickSpeechLine() {
    return CONFIG.speechLines[Math.floor(Math.random() * CONFIG.speechLines.length)];
  }

  function clearStateTimeout() {
    if (stateTimeout) {
      clearTimeout(stateTimeout);
      stateTimeout = null;
    }
  }

  function setState(nextState, durationMs) {
    state = nextState;
    nodes.root.dataset.state = nextState;

    clearStateTimeout();
    if (durationMs) {
      stateTimeout = setTimeout(function () {
        setState("idle");
      }, durationMs);
    }
  }

  function speak(line, durationMs) {
    if (!nodes.root || !nodes.bubble) return;

    nodes.bubble.textContent = line || pickSpeechLine();
    setState("speaking", durationMs || CONFIG.speakingDurationMs);
  }

  function pruneMessages(ts) {
    var cutoff = ts - CONFIG.burstWindowMs;
    while (messageTimes.length && messageTimes[0] < cutoff) {
      messageTimes.shift();
    }
  }

  function onChatActivity() {
    var ts = now();
    lastMessageAt = ts;
    messageTimes.push(ts);
    pruneMessages(ts);

    if (messageTimes.length >= CONFIG.excitedThreshold) {
      setState("excited", CONFIG.excitedDurationMs);
    } else if (state === "sleepy") {
      setState("idle");
    }

    // Future hook: increment XP based on activity cadence.
    // Future hook: adjust mood affinity to specific users or emotes.
  }

  function scheduleRandomSpeech() {
    if (speechTimeout) clearTimeout(speechTimeout);

    speechTimeout = setTimeout(function () {
      // Keep speech occasional: skip during high excitement to reduce noise.
      if (state !== "excited" && Math.random() < 0.65) {
        speak();
      }
      scheduleRandomSpeech();
    }, randomRange(CONFIG.minSpeechGapMs, CONFIG.maxSpeechGapMs));
  }

  function heartbeat() {
    var ts = now();
    pruneMessages(ts);

    if (ts - lastMessageAt > CONFIG.quietAfterMs && state === "idle") {
      setState("sleepy");
    }

    if (state === "sleepy" && ts - lastMessageAt <= CONFIG.quietAfterMs) {
      setState("idle");
    }
  }

  function findChatBuffer() {
    // CyTube selectors can vary by theme; check common IDs/classes.
    return (
      document.getElementById("messagebuffer") ||
      document.getElementById("chatbuffer") ||
      document.querySelector(".chat-msg-buffer") ||
      document.querySelector(".chat-buffer") ||
      document.querySelector("#chatwrap .chatbuffer")
    );
  }

  function watchChatBuffer() {
    var buffer = findChatBuffer();
    if (!buffer) {
      // Retry until chat area is available.
      setTimeout(watchChatBuffer, 1500);
      return;
    }

    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        var mutation = mutations[i];
        if (mutation.type === "childList" && mutation.addedNodes.length) {
          onChatActivity();
          break;
        }
      }
    });

    observer.observe(buffer, { childList: true, subtree: true });

    // Future hook: capture message metadata for minigames (quests, reactions).
    // Future hook: parse commands like !feed or !pet from chat entries.
  }

  function createWidget() {
    var root = document.createElement("aside");
    root.id = CONFIG.id;
    root.setAttribute("aria-hidden", "true");
    root.dataset.state = "idle";

    var glow = document.createElement("div");
    glow.className = "celdra-glow";

    var img = document.createElement("img");
    img.className = "celdra-pet";
    img.src = CONFIG.imageUrl;
    img.alt = "Celdra";
    img.loading = "lazy";
    img.decoding = "async";

    var bubble = document.createElement("div");
    bubble.className = "celdra-bubble";
    bubble.textContent = "";

    root.appendChild(glow);
    root.appendChild(img);
    root.appendChild(bubble);

    // Future hook: enable pointer-events on img for click interactions (pet/feed).
    // Future hook: attach growth stages by swapping image URLs/class modifiers.

    return { root: root, bubble: bubble };
  }

  function findHostContainer() {
    return document.querySelector(CONFIG.motdSelector) || null;
  }

  function mountWidget(root, attempt) {
    var mountAttempt = attempt || 0;
    var host = findHostContainer();

    if (!host) {
      if (mountAttempt >= CONFIG.mountRetryLimit) {
        root.dataset.host = "viewport";
        document.body.appendChild(root); // fallback for custom themes without #motd
        return;
      }

      // If #motd has not been mounted yet, retry shortly.
      setTimeout(function () {
        mountWidget(root, mountAttempt + 1);
      }, 800);
      return;
    }

    var hostPosition = window.getComputedStyle(host).position;
    if (hostPosition === "static") {
      host.style.position = "relative";
    }

    root.dataset.host = "motd";
    host.appendChild(root);
  }

  function init() {
    if (document.getElementById(CONFIG.id)) return;

    var widget = createWidget();
    nodes.root = widget.root;
    nodes.bubble = widget.bubble;

    mountWidget(nodes.root);

    setState("idle");
    watchChatBuffer();
    scheduleRandomSpeech();

    heartbeatTimer = setInterval(heartbeat, 2000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
