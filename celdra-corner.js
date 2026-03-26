(function () {
  "use strict";

  if (window.__celdraCornerLoaded) return;
  window.__celdraCornerLoaded = true;

  const CONFIG = {
    id: "celdra-corner",
    motdSelector: "#motd",
    mountRetryLimit: 30,

    spriteSheetUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/celdra-16bit-sheet.png",
    fallbackImageUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/celdra.png",

    speechLines: [
      "Celdra is watching...",
      "The hatchling stirs.",
      "Chat energy rising.",
      "Serenial feels alive tonight."
    ],

    quietAfterMs: 90000,
    minBlinkDelayMs: 2800,
    maxBlinkDelayMs: 6200,
    speakingDurationMs: 4200,
    minSpeechGapMs: 24000,
    maxSpeechGapMs: 46000
  };

  // Drawing / centering controls
  const DRAW_SCALE = 0.78;
  const DRAW_OFFSET_X = -2;
  const DRAW_OFFSET_Y = 18;

  const STATE_OFFSETS = {
    idle: { x: 0, y: 0 },
    blink: { x: 0, y: 0 },
    sleep: { x: -2, y: 8 },
    excited: { x: 0, y: -2 },
    default: { x: 0, y: 0 }
  };

  // Very conservative prototype frame map.
  // Adjust only after confirming the file loads and appears.
  const ANIMS = {
    idle: [
      { x: 0, y: 0, w: 256, h: 256, d: 250 },
      { x: 256, y: 0, w: 256, h: 256, d: 250 },
      { x: 512, y: 0, w: 256, h: 256, d: 300 },
      { x: 768, y: 0, w: 256, h: 256, d: 300 }
    ],
    blink: [
      { x: 0, y: 256, w: 256, h: 256, d: 100 },
      { x: 256, y: 256, w: 256, h: 256, d: 80 },
      { x: 0, y: 256, w: 256, h: 256, d: 100 }
    ],
    sleep: [
      { x: 0, y: 512, w: 256, h: 256, d: 500 },
      { x: 256, y: 512, w: 256, h: 256, d: 500 },
      { x: 512, y: 512, w: 256, h: 256, d: 600 },
      { x: 768, y: 512, w: 256, h: 256, d: 600 }
    ],
    excited: [
      { x: 0, y: 0, w: 256, h: 256, d: 170 },
      { x: 256, y: 0, w: 256, h: 256, d: 170 },
      { x: 512, y: 0, w: 256, h: 256, d: 170 },
      { x: 768, y: 0, w: 256, h: 256, d: 170 }
    ]
  };

  // Checkerboard masking
  const MASK_BRIGHTNESS_MIN = 205;
  const MASK_NEUTRAL_TOLERANCE = 30;

  let animState = "idle";
  let lastMessageAt = Date.now();
  let stateTimeout = null;
  let speechTimeout = null;
  let heartbeatTimer = null;
  let blinkTimer = null;
  let rafId = null;

  const sprite = {
    image: null,
    loaded: false,
    failed: false,
    frameIndex: 0,
    frameStartedAt: 0,
    frameCache: {}
  };

  const nodes = {
    root: null,
    bubble: null,
    canvas: null,
    context: null,
    fallback: null
  };

  function randomRange(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function clearTimers() {
    if (stateTimeout) clearTimeout(stateTimeout);
    if (speechTimeout) clearTimeout(speechTimeout);
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    if (blinkTimer) clearTimeout(blinkTimer);
    if (rafId) cancelAnimationFrame(rafId);
    stateTimeout = null;
    speechTimeout = null;
    heartbeatTimer = null;
    blinkTimer = null;
    rafId = null;
  }

  function applyState(nextState) {
    animState = nextState;
    if (nodes.root) nodes.root.dataset.state = nextState;
    sprite.frameIndex = 0;
    sprite.frameStartedAt = 0;
  }

  function setState(nextState, durationMs) {
    applyState(nextState);
    if (stateTimeout) clearTimeout(stateTimeout);
    if (durationMs) {
      stateTimeout = setTimeout(() => applyState("idle"), durationMs);
    }
  }

  function setSpeaking(visible, text) {
    if (!nodes.root || !nodes.bubble) return;
    if (typeof text === "string") nodes.bubble.textContent = text;
    nodes.root.dataset.speaking = visible ? "true" : "false";
  }

  function speak(text, duration) {
    const line = text || CONFIG.speechLines[Math.floor(Math.random() * CONFIG.speechLines.length)];
    setSpeaking(true, line);
    if (speechTimeout) clearTimeout(speechTimeout);
    speechTimeout = setTimeout(() => setSpeaking(false), duration || CONFIG.speakingDurationMs);
  }

  function scheduleBlink() {
    if (blinkTimer) clearTimeout(blinkTimer);
    blinkTimer = setTimeout(() => {
      if (animState === "idle") setState("blink", 280);
      scheduleBlink();
    }, randomRange(CONFIG.minBlinkDelayMs, CONFIG.maxBlinkDelayMs));
  }

  function scheduleSpeech() {
    if (speechTimeout) clearTimeout(speechTimeout);
    speechTimeout = setTimeout(function loop() {
      if (animState !== "sleep" && Math.random() < 0.65) {
        speak();
      }
      speechTimeout = setTimeout(loop, randomRange(CONFIG.minSpeechGapMs, CONFIG.maxSpeechGapMs));
    }, randomRange(CONFIG.minSpeechGapMs, CONFIG.maxSpeechGapMs));
  }

  function onChatActivity() {
    lastMessageAt = Date.now();
    if (animState === "sleep") setState("idle");
  }

  function heartbeat() {
    const idleFor = Date.now() - lastMessageAt;
    if (idleFor > CONFIG.quietAfterMs && animState !== "sleep") {
      setState("sleep");
      return;
    }
    if (animState === "sleep" && idleFor <= CONFIG.quietAfterMs) {
      setState("idle");
    }
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
    const buffer = findChatBuffer();
    if (!buffer) {
      setTimeout(watchChatBuffer, 1500);
      return;
    }

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "childList" && mutation.addedNodes.length) {
          onChatActivity();
          break;
        }
      }
    });

    observer.observe(buffer, { childList: true, subtree: true });
  }

  function createWidget() {
    const root = document.createElement("aside");
    root.id = CONFIG.id;
    root.setAttribute("aria-hidden", "true");
    root.dataset.state = "idle";
    root.dataset.speaking = "false";

    const glow = document.createElement("div");
    glow.className = "celdra-glow";

    const canvas = document.createElement("canvas");
    canvas.className = "celdra-canvas celdra-anim";
    canvas.width = 256;
    canvas.height = 256;

    const fallback = document.createElement("img");
    fallback.className = "celdra-fallback celdra-anim";
    fallback.src = CONFIG.fallbackImageUrl;
    fallback.alt = "";
    fallback.style.display = "none";

    const bubble = document.createElement("div");
    bubble.className = "celdra-bubble";

    root.appendChild(glow);
    root.appendChild(canvas);
    root.appendChild(fallback);
    root.appendChild(bubble);

    return { root, canvas, bubble, fallback };
  }

  function findHostContainer() {
    return document.querySelector(CONFIG.motdSelector) || null;
  }

  function mountWidget(root, attempt) {
    const tries = attempt || 0;
    const host = findHostContainer();

    if (!host) {
      if (tries >= CONFIG.mountRetryLimit) {
        root.dataset.host = "viewport";
        document.body.appendChild(root);
        return;
      }
      setTimeout(() => mountWidget(root, tries + 1), 800);
      return;
    }

    if (window.getComputedStyle(host).position === "static") {
      host.style.position = "relative";
    }

    root.dataset.host = "motd";
    host.appendChild(root);
  }

  function useFallback() {
    sprite.failed = true;
    sprite.loaded = false;
    if (nodes.canvas) nodes.canvas.style.display = "none";
    if (nodes.fallback) nodes.fallback.style.display = "block";
    speak("Celdra is using fallback art.", 3200);
  }

  function loadSpriteSheet() {
    const image = new Image();
    image.decoding = "async";
    image.onload = function () {
      sprite.image = image;
      sprite.loaded = true;
      sprite.failed = false;
      sprite.frameCache = {};
      if (nodes.canvas) nodes.canvas.style.display = "block";
      if (nodes.fallback) nodes.fallback.style.display = "none";
    };
    image.onerror = function () {
      useFallback();
    };
    image.src = CONFIG.spriteSheetUrl;
  }

  function frameKey(frame) {
    return [frame.x, frame.y, frame.w, frame.h].join(":");
  }

  function buildOffscreenCanvas(width, height) {
    const c = document.createElement("canvas");
    c.width = width;
    c.height = height;
    return c;
  }

  function getProcessedFrame(frame) {
    const key = frameKey(frame);
    if (sprite.frameCache[key]) return sprite.frameCache[key];

    const offscreen = buildOffscreenCanvas(frame.w, frame.h);
    const octx = offscreen.getContext("2d", { alpha: true });
    octx.clearRect(0, 0, frame.w, frame.h);
    octx.imageSmoothingEnabled = false;
    octx.drawImage(sprite.image, frame.x, frame.y, frame.w, frame.h, 0, 0, frame.w, frame.h);

    const imageData = octx.getImageData(0, 0, frame.w, frame.h);
    const pixels = imageData.data;

    for (let i = 0; i < pixels.length; i += 4) {
      const r = pixels[i];
      const g = pixels[i + 1];
      const b = pixels[i + 2];
      const a = pixels[i + 3];
      if (a <= 8) continue;

      const min = Math.min(r, g, b);
      const max = Math.max(r, g, b);
      const brightness = (r + g + b) / 3;
      const spread = max - min;

      if (brightness >= MASK_BRIGHTNESS_MIN && spread <= MASK_NEUTRAL_TOLERANCE) {
        pixels[i + 3] = 0;
      }
    }

    octx.putImageData(imageData, 0, 0);
    sprite.frameCache[key] = offscreen;
    return offscreen;
  }

  function drawFrame(frame) {
    if (!nodes.context || !nodes.canvas || !sprite.loaded || !frame) return;

    const ctx = nodes.context;
    const canvas = nodes.canvas;
    const processed = getProcessedFrame(frame);
    const stateOffset = STATE_OFFSETS[animState] || STATE_OFFSETS.default;

    const fitScale = Math.min(canvas.width / frame.w, canvas.height / frame.h);
    const finalScale = fitScale * DRAW_SCALE;
    const drawWidth = Math.round(frame.w * finalScale);
    const drawHeight = Math.round(frame.h * finalScale);
    const drawX = Math.round((canvas.width - drawWidth) / 2 + DRAW_OFFSET_X + stateOffset.x);
    const drawY = Math.round((canvas.height - drawHeight) / 2 + DRAW_OFFSET_Y + stateOffset.y);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(processed, 0, 0, frame.w, frame.h, drawX, drawY, drawWidth, drawHeight);
  }

  function stepSprite(ts) {
    if (!sprite.loaded || sprite.failed) {
      rafId = requestAnimationFrame(stepSprite);
      return;
    }

    const timeline = ANIMS[animState] || ANIMS.idle;
    let frame = timeline[sprite.frameIndex] || timeline[0];

    if (!sprite.frameStartedAt) sprite.frameStartedAt = ts;

    if (ts - sprite.frameStartedAt >= frame.d) {
      sprite.frameIndex = (sprite.frameIndex + 1) % timeline.length;
      frame = timeline[sprite.frameIndex] || timeline[0];
      sprite.frameStartedAt = ts;
    }

    drawFrame(frame);
    rafId = requestAnimationFrame(stepSprite);
  }

  function init() {
    if (document.getElementById(CONFIG.id)) return;

    const widget = createWidget();
    nodes.root = widget.root;
    nodes.bubble = widget.bubble;
    nodes.canvas = widget.canvas;
    nodes.fallback = widget.fallback;
    nodes.context = widget.canvas.getContext("2d", { alpha: true });

    mountWidget(nodes.root);
    loadSpriteSheet();

    applyState("idle");
    watchChatBuffer();
    scheduleBlink();
    scheduleSpeech();
    heartbeatTimer = setInterval(heartbeat, 2000);
    rafId = requestAnimationFrame(stepSprite);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }

  window.__destroyCeldraCorner = function () {
    clearTimers();
    if (nodes.root && nodes.root.parentNode) {
      nodes.root.parentNode.removeChild(nodes.root);
    }
    window.__celdraCornerLoaded = false;
  };
})();
