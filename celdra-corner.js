(function () {
  "use strict";

  // Prevent duplicate initialization if script is re-run.
  if (window.__celdraCornerLoaded || document.getElementById("celdra-corner")) {
    return;
  }
  window.__celdraCornerLoaded = true;

  var CONFIG = {
    id: "celdra-corner",
    spriteSheetUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/celdra-16bit-sheet.png",
    speechLines: [
      "Celdra is watching...",
      "The hatchling stirs.",
      "Chat energy rising.",
      "Serenial feels alive tonight."
    ],
    quietAfterMs: 90000,
    minBlinkDelayMs: 2500,
    maxBlinkDelayMs: 6500,
    speakingDurationMs: 4500,
    minSpeechGapMs: 24000,
    maxSpeechGapMs: 46000,
    motdSelector: "#motd",
    mountRetryLimit: 25
  };

  // Canvas draw tuning. Keep near the top so placement can be adjusted quickly.
  var DRAW_SCALE = 0.92;
  var DRAW_OFFSET_X = 0;
  var DRAW_OFFSET_Y = 8;
  var STATE_OFFSETS = {
    idle: { x: 0, y: 0 },
    blink: { x: 0, y: 0 },
    sleep: { x: 0, y: 5 },
    sleepy: { x: 0, y: 4 },
    excited: { x: 0, y: -2 },
    default: { x: 0, y: 0 }
  };

  // Sprite-sheet background masking tuning.
  // These values target the light neutral checkerboard while preserving colored art.
  var MASK_BRIGHTNESS_MIN = 212;
  var MASK_NEUTRAL_TOLERANCE = 22;
  var MASK_ALPHA = 0;

  // NOTE: Update these source rectangles when improved sprite sheets are added.
  // Assumes a 256x256 frame grid on a 1536x1024 sheet.
  var ANIMS = {
    idle: [
      { x: 0, y: 0, w: 256, h: 256, d: 240 },
      { x: 256, y: 0, w: 256, h: 256, d: 240 },
      { x: 512, y: 0, w: 256, h: 256, d: 280 },
      { x: 768, y: 0, w: 256, h: 256, d: 280 }
    ],
    blink: [
      { x: 0, y: 256, w: 256, h: 256, d: 95 },
      { x: 256, y: 256, w: 256, h: 256, d: 75 },
      { x: 0, y: 256, w: 256, h: 256, d: 95 }
    ],
    sleep: [
      { x: 0, y: 512, w: 256, h: 256, d: 450 },
      { x: 256, y: 512, w: 256, h: 256, d: 450 },
      { x: 512, y: 512, w: 256, h: 256, d: 520 },
      { x: 768, y: 512, w: 256, h: 256, d: 520 }
    ],
    sleepy: [
      { x: 0, y: 768, w: 256, h: 256, d: 360 },
      { x: 256, y: 768, w: 256, h: 256, d: 360 },
      { x: 512, y: 768, w: 256, h: 256, d: 420 },
      { x: 768, y: 768, w: 256, h: 256, d: 420 }
    ],
    excited: [
      { x: 1024, y: 0, w: 256, h: 256, d: 170 },
      { x: 1280, y: 0, w: 256, h: 256, d: 170 },
      { x: 1024, y: 256, w: 256, h: 256, d: 190 },
      { x: 1280, y: 256, w: 256, h: 256, d: 190 }
    ]
  };

  var animState = "idle";
  var lastMessageAt = Date.now();
  var stateTimeout = null;
  var speechTimeout = null;
  var heartbeatTimer = null;
  var blinkTimer = null;
  var rafId = null;

  var sprite = {
    image: null,
    loaded: false,
    frameIndex: 0,
    frameStartedAt: 0,
    frameCache: {}
  };

  var nodes = {
    root: null,
    bubble: null,
    canvas: null,
    context: null
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

  function clearBlinkTimer() {
    if (blinkTimer) {
      clearTimeout(blinkTimer);
      blinkTimer = null;
    }
  }

  function applyState(nextState) {
    animState = nextState;
    if (nodes.root) {
      nodes.root.dataset.state = nextState;
    }
    sprite.frameIndex = 0;
    sprite.frameStartedAt = now();
  }

  function setState(nextState, durationMs) {
    applyState(nextState);

    clearStateTimeout();
    if (durationMs) {
      stateTimeout = setTimeout(function () {
        applyState("idle");
      }, durationMs);
    }
  }

  function setSpeaking(visible) {
    if (!nodes.root) return;
    nodes.root.dataset.speaking = visible ? "true" : "false";
  }

  function speak(line, durationMs) {
    if (!nodes.root || !nodes.bubble) return;

    nodes.bubble.textContent = line || pickSpeechLine();
    setSpeaking(true);

    setTimeout(function () {
      setSpeaking(false);
    }, durationMs || CONFIG.speakingDurationMs);
  }

  function scheduleRandomSpeech() {
    if (speechTimeout) clearTimeout(speechTimeout);

    speechTimeout = setTimeout(function () {
      if (animState !== "sleep" && Math.random() < 0.65) {
        speak();
      }
      scheduleRandomSpeech();
    }, randomRange(CONFIG.minSpeechGapMs, CONFIG.maxSpeechGapMs));
  }

  function scheduleBlink() {
    clearBlinkTimer();

    blinkTimer = setTimeout(function () {
      if (animState === "idle") {
        setState("blink", 280);
      }
      scheduleBlink();
    }, randomRange(CONFIG.minBlinkDelayMs, CONFIG.maxBlinkDelayMs));
  }

  function heartbeat() {
    var ts = now();

    if (ts - lastMessageAt > CONFIG.quietAfterMs && animState !== "sleep") {
      setState("sleep");
      return;
    }

    if (animState === "sleep" && ts - lastMessageAt <= CONFIG.quietAfterMs) {
      setState("idle");
    }
  }

  function onChatActivity() {
    lastMessageAt = now();

    if (animState === "sleep") {
      setState("idle");
    }

    // Future hook: increment XP based on activity cadence.
    // Future hook: parse commands like !feed or !pet from chat entries.
  }

  function findChatBuffer() {
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
  }

  function drawFrame(frame) {
    if (!nodes.context || !nodes.canvas || !sprite.loaded || !frame) return;

    var ctx = nodes.context;
    var canvas = nodes.canvas;
    var processedFrame = getProcessedFrame(frame);
    var stateOffset = STATE_OFFSETS[animState] || STATE_OFFSETS.default;
    var fitScale = Math.min(canvas.width / frame.w, canvas.height / frame.h);
    var finalScale = fitScale * DRAW_SCALE;
    var drawWidth = Math.round(frame.w * finalScale);
    var drawHeight = Math.round(frame.h * finalScale);
    var drawX = Math.round((canvas.width - drawWidth) / 2 + DRAW_OFFSET_X + stateOffset.x);
    var drawY = Math.round((canvas.height - drawHeight) / 2 + DRAW_OFFSET_Y + stateOffset.y);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(
      processedFrame,
      0,
      0,
      frame.w,
      frame.h,
      drawX,
      drawY,
      drawWidth,
      drawHeight
    );
  }

  function getFrameKey(frame) {
    return [frame.x, frame.y, frame.w, frame.h].join(":");
  }

  function buildOffscreenCanvas(width, height) {
    if (typeof OffscreenCanvas !== "undefined") {
      return new OffscreenCanvas(width, height);
    }
    var offscreen = document.createElement("canvas");
    offscreen.width = width;
    offscreen.height = height;
    return offscreen;
  }

  function getProcessedFrame(frame) {
    var frameKey = getFrameKey(frame);
    if (sprite.frameCache[frameKey]) {
      return sprite.frameCache[frameKey];
    }

    var offscreen = buildOffscreenCanvas(frame.w, frame.h);
    var offscreenCtx = offscreen.getContext("2d", { alpha: true });
    if (!offscreenCtx) {
      return sprite.image;
    }

    offscreenCtx.clearRect(0, 0, frame.w, frame.h);
    offscreenCtx.imageSmoothingEnabled = false;
    offscreenCtx.drawImage(
      sprite.image,
      frame.x,
      frame.y,
      frame.w,
      frame.h,
      0,
      0,
      frame.w,
      frame.h
    );

    var imageData = offscreenCtx.getImageData(0, 0, frame.w, frame.h);
    var pixels = imageData.data;

    for (var i = 0; i < pixels.length; i += 4) {
      var r = pixels[i];
      var g = pixels[i + 1];
      var b = pixels[i + 2];
      var a = pixels[i + 3];

      if (a <= 8) continue;

      var min = Math.min(r, g, b);
      var max = Math.max(r, g, b);
      var brightness = (r + g + b) / 3;
      var channelSpread = max - min;

      // Mask out bright neutral checkerboard tones.
      if (brightness >= MASK_BRIGHTNESS_MIN && channelSpread <= MASK_NEUTRAL_TOLERANCE) {
        pixels[i + 3] = Math.min(a, MASK_ALPHA);
      }
    }

    offscreenCtx.putImageData(imageData, 0, 0);
    sprite.frameCache[frameKey] = offscreen;
    return offscreen;
  }

  function stepSprite(ts) {
    if (!sprite.loaded) {
      rafId = requestAnimationFrame(stepSprite);
      return;
    }

    var timeline = ANIMS[animState] || ANIMS.idle;
    var frame = timeline[sprite.frameIndex] || timeline[0];

    if (!sprite.frameStartedAt) {
      sprite.frameStartedAt = ts;
    }

    if (ts - sprite.frameStartedAt >= frame.d) {
      sprite.frameIndex = (sprite.frameIndex + 1) % timeline.length;
      frame = timeline[sprite.frameIndex] || timeline[0];
      sprite.frameStartedAt = ts;
    }

    drawFrame(frame);
    rafId = requestAnimationFrame(stepSprite);
  }

  function createWidget() {
    var root = document.createElement("aside");
    root.id = CONFIG.id;
    root.setAttribute("aria-hidden", "true");
    root.dataset.state = "idle";
    root.dataset.speaking = "false";

    var glow = document.createElement("div");
    glow.className = "celdra-glow";

    var canvas = document.createElement("canvas");
    canvas.className = "celdra-canvas";
    canvas.width = 256;
    canvas.height = 256;

    var bubble = document.createElement("div");
    bubble.className = "celdra-bubble";
    bubble.textContent = "";

    root.appendChild(glow);
    root.appendChild(canvas);
    root.appendChild(bubble);

    return { root: root, bubble: bubble, canvas: canvas };
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
        document.body.appendChild(root);
        return;
      }

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

  function loadSpriteSheet() {
    var image = new Image();
    image.decoding = "async";
    image.src = CONFIG.spriteSheetUrl;
    image.onload = function () {
      sprite.loaded = true;
      sprite.frameCache = {};
      drawFrame(ANIMS.idle[0]);
    };
    sprite.image = image;
  }

  function init() {
    if (document.getElementById(CONFIG.id)) return;

    var widget = createWidget();
    nodes.root = widget.root;
    nodes.bubble = widget.bubble;
    nodes.canvas = widget.canvas;
    nodes.context = widget.canvas.getContext("2d", { alpha: true });

    mountWidget(nodes.root);
    loadSpriteSheet();

    setState("idle");
    watchChatBuffer();
    scheduleBlink();
    scheduleRandomSpeech();

    heartbeatTimer = setInterval(heartbeat, 2000);
    rafId = requestAnimationFrame(stepSprite);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }

  // Optional teardown for manual script reload workflows.
  window.__destroyCeldraCorner = function () {
    clearStateTimeout();
    clearBlinkTimer();

    if (speechTimeout) {
      clearTimeout(speechTimeout);
      speechTimeout = null;
    }

    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }

    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }

    if (nodes.root && nodes.root.parentNode) {
      nodes.root.parentNode.removeChild(nodes.root);
    }

    window.__celdraCornerLoaded = false;
  };
})();
