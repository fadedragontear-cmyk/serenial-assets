(function () {
  "use strict";

  // Prevent duplicate bootstraps when script is injected multiple times.
  if (window.__celdraCornerLoaded) return;
  window.__celdraCornerLoaded = true;

  const TOTAL_LOOP_MS = 5000;
  const TOTAL_FRAMES = 70;
  const FRAME_DURATION_MS = Math.round(TOTAL_LOOP_MS / TOTAL_FRAMES);

  const CONFIG = {
    id: "celdra-corner",
    motdSelector: "#motd",
    mountRetryLimit: 30,
    mountRetryDelayMs: 800,

    // Top-level tuning knobs for room owners.
    sizePx: 152,
    rightOffset: "3.5%",
    bottomOffset: "5.5%",
    scale: 1,

    // PNG sequence host.
    assetBaseUrl: "https://fadedragontear-cmyk.github.io/serenial-assets/"
  };

  const nodes = {
    root: null,
    frame: null
  };

  const runtime = {
    frameUrls: [],
    frameIndex: 0,
    frameTimer: null
  };

  function resolveUrl(name) {
    return CONFIG.assetBaseUrl + name;
  }

  function buildFrameFilenames() {
    return Array.from({ length: TOTAL_FRAMES }, (_, index) => {
      const frameNum = String(index + 1).padStart(2, "0");
      return `${frameNum}.png`;
    });
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
    const filenames = buildFrameFilenames();
    return Promise.all(filenames.map(preloadFrame)).then((urls) => urls.filter(Boolean));
  }

  function clearTimer(name) {
    if (runtime[name]) {
      clearTimeout(runtime[name]);
      runtime[name] = null;
    }
  }

  function playSequence() {
    clearTimer("frameTimer");

    const tick = () => {
      if (!nodes.frame || runtime.frameUrls.length === 0) {
        runtime.frameTimer = setTimeout(tick, FRAME_DURATION_MS);
        return;
      }

      nodes.frame.src = runtime.frameUrls[runtime.frameIndex];
      runtime.frameIndex = (runtime.frameIndex + 1) % runtime.frameUrls.length;
      runtime.frameTimer = setTimeout(tick, FRAME_DURATION_MS);
    };

    tick();
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

      setTimeout(() => mountWidget(root, tries + 1), CONFIG.mountRetryDelayMs);
      return;
    }

    if (window.getComputedStyle(host).position === "static") {
      host.style.position = "relative";
    }

    root.dataset.host = "motd";
    host.appendChild(root);
  }

  function buildWidgetDom() {
    const root = document.createElement("div");
    root.id = CONFIG.id;
    root.setAttribute("aria-hidden", "true");

    const glow = document.createElement("div");
    glow.className = "celdra-glow";

    const frameWrap = document.createElement("div");
    frameWrap.className = "celdra-frame-wrap celdra-anim";

    const frame = document.createElement("img");
    frame.className = "celdra-frame";
    frame.alt = "";
    frame.decoding = "async";

    frameWrap.appendChild(frame);
    root.appendChild(glow);
    root.appendChild(frameWrap);

    return { root, frame };
  }

  function applyRootTuningVars(root) {
    root.style.setProperty("--celdra-size", `${CONFIG.sizePx}px`);
    root.style.setProperty("--celdra-right", CONFIG.rightOffset);
    root.style.setProperty("--celdra-bottom", CONFIG.bottomOffset);
    root.style.setProperty("--celdra-scale", String(CONFIG.scale));
  }

  function init() {
    if (document.getElementById(CONFIG.id)) return;

    const widget = buildWidgetDom();
    nodes.root = widget.root;
    nodes.frame = widget.frame;

    applyRootTuningVars(nodes.root);
    mountWidget(nodes.root);

    preloadFrames().then((urls) => {
      runtime.frameUrls = urls;

      if (runtime.frameUrls.length === 0) {
        console.warn("[Celdra] No sequence frames loaded. Widget remains mounted.");
        return;
      }

      playSequence();
    });
  }

  function destroy() {
    clearTimer("frameTimer");

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
