(function () {
  "use strict";

  // Prevent duplicate bootstraps when script is injected multiple times.
  if (window.__celdraCornerLoaded) return;
  window.__celdraCornerLoaded = true;

  const FRAME_DURATION_MS = 400;

  const IDLE_FRAMES = [
    { src: "idle1.png", duration: FRAME_DURATION_MS },
    { src: "idle2.png", duration: FRAME_DURATION_MS },
    { src: "idle3.png", duration: FRAME_DURATION_MS },
    { src: "idle4.png", duration: FRAME_DURATION_MS },
    { src: "idle5.png", duration: FRAME_DURATION_MS },
    { src: "idle6.png", duration: FRAME_DURATION_MS },
    { src: "idle7.png", duration: FRAME_DURATION_MS },
    { src: "idle8.png", duration: FRAME_DURATION_MS }
  ];

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
    assetBaseUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/"
  };

  const nodes = {
    root: null,
    frame: null,
    bubble: null
  };

  const runtime = {
    mounted: false,
    frameIndex: 0,
    frameTimer: null,
    frameUrls: [],
    chatObserver: null
  };

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
      runtime[name] = null;
    }
  }

  function animateIdle() {
    clearTimer("frameTimer");

    const tick = () => {
      if (!nodes.frame || !runtime.frameUrls.length) {
        runtime.frameTimer = setTimeout(tick, FRAME_DURATION_MS);
        return;
      }

      const frameData = IDLE_FRAMES[runtime.frameIndex % IDLE_FRAMES.length];
      const frameUrl = runtime.frameUrls[runtime.frameIndex % runtime.frameUrls.length];
      nodes.frame.src = frameUrl;
      runtime.frameIndex = (runtime.frameIndex + 1) % IDLE_FRAMES.length;

      runtime.frameTimer = setTimeout(tick, frameData.duration);
    };

    tick();
  }

  function watchChatBuffer() {
    const attach = () => {
      const buffer = findChatBuffer();
      if (!buffer) {
        setTimeout(attach, 1500);
        return;
      }

      runtime.chatObserver = new MutationObserver(() => {
        // Chat observer intentionally retained for future state wiring.
        // Current behavior: ignore chat activity and keep idle loop running.
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

  function preloadFrame(filename) {
    return new Promise((resolve) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => resolve(resolveUrl(filename));
      img.onerror = () => {
        console.warn("[Celdra] Failed to load frame:", filename);
        resolve(null);
      };
      img.src = resolveUrl(filename);
    });
  }

  function preloadFrames() {
    return Promise.all(IDLE_FRAMES.map((frame) => preloadFrame(frame.src))).then((urls) =>
      urls.filter(Boolean)
    );
  }

  function bootBehavior() {
    nodes.root.dataset.state = "idle";
    animateIdle();
    watchChatBuffer();
  }

  function init() {
    if (document.getElementById(CONFIG.id)) return;

    const widget = buildWidgetDom();
    nodes.root = widget.root;
    nodes.frame = widget.frame;
    nodes.bubble = widget.bubble;

    applyRootTuningVars(nodes.root);
    mountWidget(nodes.root);

    preloadFrames().then((urls) => {
      runtime.frameUrls = urls;

      if (!runtime.frameUrls.length) {
        console.warn("[Celdra] All frame loads failed. Widget remains mounted but sprite is hidden.");
      }

      bootBehavior();
    });
  }

  function destroy() {
    clearTimer("frameTimer");

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
