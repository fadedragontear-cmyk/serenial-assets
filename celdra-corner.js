(function () {
  "use strict";

  // Prevent duplicate bootstraps when script is injected multiple times.
  if (window.__celdraCornerLoaded) return;
  window.__celdraCornerLoaded = true;

  const CONFIG = {
    id: "celdra-corner",
    motdSelector: "#motd",
    mountRetryLimit: 30,
    mountRetryDelayMs: 800,

    // Top-level tuning knobs for CyTube room owners.
    sizePx: 152,
    rightOffset: "3.5%",
    bottomOffset: "5.5%",
    scale: 1,

    // Use transparent PNG frames directly (no canvas pixel processing).
    assetBaseUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/",
    frames: {
      idle1: "idle1.png",
      idle2: "idle2.png",
      idle3: "idle3.png",
      blink: "blink.png",
      sleep1: "sleep1.png",
      sleep2: "sleep2.png"
    },

    speechLines: [
      "Celdra is watching...",
      "The hatchling stirs.",
      "Chat energy rising.",
      "Serenial feels alive tonight."
    ],

    // State timing.
    quietAfterMs: 90000,
    heartbeatIntervalMs: 2000,

    minBlinkDelayMs: 2800,
    maxBlinkDelayMs: 6200,
    blinkDurationMs: 230,

    minSpeechGapMs: 24000,
    maxSpeechGapMs: 46000,
    speechDurationMs: 4200,

    excitedDurationMs: 2800,
    speakingExcitedCooldownMs: 7000
  };

  // State machine frame maps.
  const STATE_FRAMES = {
    idle: ["idle1", "idle2", "idle3", "idle2"],
    sleep: ["sleep1", "sleep2"],
    blink: ["blink"],
    excited: ["idle1", "idle2", "idle3", "idle2"],
    speaking: ["idle1", "idle2", "idle3", "idle2"]
  };

  const FRAME_DELAYS = {
    idle: 320,
    sleep: 900,
    blink: 80,
    excited: 165,
    speaking: 260
  };

  const nodes = {
    root: null,
    frame: null,
    bubble: null
  };

  const runtime = {
    mounted: false,
    state: "idle",
    frameIndex: 0,
    frameTimer: null,
    stateTimer: null,
    heartbeatTimer: null,
    blinkTimer: null,
    speechLoopTimer: null,
    bubbleHideTimer: null,
    imageByKey: Object.create(null),
    loadedKeys: new Set(),
    missingKeys: new Set(),
    lastActivityAt: Date.now(),
    lastExcitedAt: 0,
    chatObserver: null
  };

  function randomRange(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function resolveUrl(name) {
    return CONFIG.assetBaseUrl + name;
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

  function clearTimer(name) {
    if (runtime[name]) {
      clearTimeout(runtime[name]);
      clearInterval(runtime[name]);
      runtime[name] = null;
    }
  }

  function clearAllTimers() {
    clearTimer("frameTimer");
    clearTimer("stateTimer");
    clearTimer("heartbeatTimer");
    clearTimer("blinkTimer");
    clearTimer("speechLoopTimer");
    clearTimer("bubbleHideTimer");
  }

  function setSpeaking(visible, text) {
    if (!nodes.root || !nodes.bubble) return;
    if (typeof text === "string") nodes.bubble.textContent = text;
    nodes.root.dataset.speaking = visible ? "true" : "false";
  }

  function speak(text, durationMs) {
    const line = text || CONFIG.speechLines[Math.floor(Math.random() * CONFIG.speechLines.length)];
    setSpeaking(true, line);

    clearTimer("bubbleHideTimer");
    runtime.bubbleHideTimer = setTimeout(() => {
      setSpeaking(false);
    }, durationMs || CONFIG.speechDurationMs);
  }

  function getVisualState() {
    // speaking state only controls frame cadence while bubble is visible.
    if (nodes.root && nodes.root.dataset.speaking === "true" && runtime.state === "idle") {
      return "speaking";
    }
    return runtime.state;
  }

  function getFirstAvailableKey(keys) {
    for (const key of keys) {
      if (runtime.loadedKeys.has(key)) return key;
    }
    return null;
  }

  function getStableFallbackKey() {
    const priority = ["idle1", "idle2", "idle3", "blink", "sleep1", "sleep2"];
    return getFirstAvailableKey(priority);
  }

  function renderFrame() {
    if (!nodes.frame) return;

    const visualState = getVisualState();
    const sequence = STATE_FRAMES[visualState] || STATE_FRAMES.idle;
    if (!sequence || !sequence.length) return;

    const idx = runtime.frameIndex % sequence.length;
    let key = sequence[idx];

    // If requested frame is missing, choose safest loaded frame.
    if (!runtime.loadedKeys.has(key)) {
      const sequenceFallback = getFirstAvailableKey(sequence);
      const stableFallback = getStableFallbackKey();
      key = sequenceFallback || stableFallback;
    }

    if (!key || !runtime.imageByKey[key]) {
      console.warn("[Celdra] No frame images were loaded; widget stays mounted without sprite.");
      nodes.frame.style.opacity = "0";
      return;
    }

    nodes.frame.style.opacity = "1";
    nodes.frame.src = runtime.imageByKey[key].src;
  }

  function scheduleFrameLoop() {
    clearTimer("frameTimer");

    const tick = () => {
      renderFrame();

      const visualState = getVisualState();
      const sequence = STATE_FRAMES[visualState] || STATE_FRAMES.idle;
      const delay = FRAME_DELAYS[visualState] || FRAME_DELAYS.idle;

      runtime.frameIndex = (runtime.frameIndex + 1) % Math.max(sequence.length, 1);
      runtime.frameTimer = setTimeout(tick, delay);
    };

    tick();
  }

  function applyState(nextState) {
    runtime.state = nextState;
    runtime.frameIndex = 0;
    if (nodes.root) nodes.root.dataset.state = nextState;
  }

  function setState(nextState, durationMs, returnToState) {
    applyState(nextState);

    clearTimer("stateTimer");
    if (durationMs) {
      runtime.stateTimer = setTimeout(() => {
        applyState(returnToState || "idle");
      }, durationMs);
    }
  }

  function maybeExciteFromChat() {
    const now = Date.now();
    if (now - runtime.lastExcitedAt < CONFIG.speakingExcitedCooldownMs) return;
    runtime.lastExcitedAt = now;
    setState("excited", CONFIG.excitedDurationMs, "idle");
  }

  function onChatActivity() {
    runtime.lastActivityAt = Date.now();

    if (runtime.state === "sleep") {
      setState("idle");
      speak("The hatchling wakes.", 2500);
    } else {
      maybeExciteFromChat();
    }
  }

  function heartbeat() {
    const idleFor = Date.now() - runtime.lastActivityAt;
    if (idleFor > CONFIG.quietAfterMs && runtime.state !== "sleep") {
      setState("sleep");
      return;
    }

    if (runtime.state === "sleep" && idleFor <= CONFIG.quietAfterMs) {
      setState("idle");
    }
  }

  function scheduleBlink() {
    clearTimer("blinkTimer");

    runtime.blinkTimer = setTimeout(function triggerBlink() {
      if (runtime.state === "idle") {
        setState("blink", CONFIG.blinkDurationMs, "idle");
      }

      runtime.blinkTimer = setTimeout(
        triggerBlink,
        randomRange(CONFIG.minBlinkDelayMs, CONFIG.maxBlinkDelayMs)
      );
    }, randomRange(CONFIG.minBlinkDelayMs, CONFIG.maxBlinkDelayMs));
  }

  function scheduleSpeechLoop() {
    clearTimer("speechLoopTimer");

    const loop = () => {
      if (runtime.state !== "sleep" && Math.random() < 0.65) {
        speak();
      }

      runtime.speechLoopTimer = setTimeout(
        loop,
        randomRange(CONFIG.minSpeechGapMs, CONFIG.maxSpeechGapMs)
      );
    };

    runtime.speechLoopTimer = setTimeout(
      loop,
      randomRange(CONFIG.minSpeechGapMs, CONFIG.maxSpeechGapMs)
    );
  }

  function watchChatBuffer() {
    const attach = () => {
      const buffer = findChatBuffer();
      if (!buffer) {
        setTimeout(attach, 1500);
        return;
      }

      runtime.chatObserver = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          if (mutation.type === "childList" && mutation.addedNodes && mutation.addedNodes.length) {
            onChatActivity();
            break;
          }
        }
      });

      runtime.chatObserver.observe(buffer, { childList: true, subtree: true });
    };

    attach();
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
        runtime.mounted = true;
        return;
      }

      setTimeout(() => mountWidget(root, tries + 1), CONFIG.mountRetryDelayMs);
      return;
    }

    if (window.getComputedStyle(host).position === "static") {
      host.style.position = "relative";
    }

    root.dataset.host = "motd";
    host.appendChild(root);
    runtime.mounted = true;
  }

  function buildWidgetDom() {
    const root = document.createElement("div");
    root.id = CONFIG.id;
    root.setAttribute("aria-hidden", "true");
    root.dataset.state = "idle";
    root.dataset.speaking = "false";

    const glow = document.createElement("div");
    glow.className = "celdra-glow";

    const frame = document.createElement("img");
    frame.className = "celdra-frame celdra-anim";
    frame.alt = "";
    frame.decoding = "async";

    const bubble = document.createElement("div");
    bubble.className = "celdra-bubble";

    root.appendChild(glow);
    root.appendChild(frame);
    root.appendChild(bubble);

    return { root, frame, bubble };
  }

  function applyRootTuningVars(root) {
    root.style.setProperty("--celdra-size", CONFIG.sizePx + "px");
    root.style.setProperty("--celdra-right", CONFIG.rightOffset);
    root.style.setProperty("--celdra-bottom", CONFIG.bottomOffset);
    root.style.setProperty("--celdra-scale", String(CONFIG.scale));
  }

  function preloadImage(key, filename) {
    return new Promise((resolve) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => {
        runtime.imageByKey[key] = img;
        runtime.loadedKeys.add(key);
        resolve();
      };
      img.onerror = () => {
        runtime.missingKeys.add(key);
        console.warn("[Celdra] Failed to load frame:", filename);
        resolve();
      };
      img.src = resolveUrl(filename);
    });
  }

  function preloadFrames() {
    const work = [];
    for (const key of Object.keys(CONFIG.frames)) {
      work.push(preloadImage(key, CONFIG.frames[key]));
    }
    return Promise.all(work);
  }

  function bootBehavior() {
    applyState("idle");
    scheduleFrameLoop();
    scheduleBlink();
    scheduleSpeechLoop();
    watchChatBuffer();
    runtime.heartbeatTimer = setInterval(heartbeat, CONFIG.heartbeatIntervalMs);
  }

  function init() {
    if (document.getElementById(CONFIG.id)) return;

    const widget = buildWidgetDom();
    nodes.root = widget.root;
    nodes.frame = widget.frame;
    nodes.bubble = widget.bubble;

    applyRootTuningVars(nodes.root);
    mountWidget(nodes.root);

    preloadFrames().then(() => {
      if (!runtime.loadedKeys.size) {
        console.warn("[Celdra] All frame loads failed. Widget remains mounted but sprite is hidden.");
      }
      bootBehavior();
    });
  }

  function destroy() {
    clearAllTimers();

    if (runtime.chatObserver) {
      runtime.chatObserver.disconnect();
      runtime.chatObserver = null;
    }

    if (nodes.root && nodes.root.parentNode) {
      nodes.root.parentNode.removeChild(nodes.root);
    }

    window.__celdraCornerLoaded = false;
  }

  window.__destroyCeldraCorner = destroy;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
