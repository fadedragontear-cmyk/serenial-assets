(function () {
  "use strict";

  // Prevent duplicate bootstraps when script is injected multiple times.
  if (window.__celdraCornerLoaded) return;
  window.__celdraCornerLoaded = true;

  const TOTAL_LOOP_MS = 5600;
  const TOTAL_FRAMES = 70;
  const MIN_VIABLE_FRAMES = 24;
  const FRAME_TIME_MULTIPLIER = 2;

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
    frameA: null,
    frameB: null
  };

  const runtime = {
    frameUrls: [],
    frameIndex: 0,
    frameTimer: null,
    mountTimer: null,
    isAnimating: false,
    activeBuffer: "a"
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

  function decodeImage(img) {
    if (typeof img.decode === "function") {
      return img.decode().catch(() => undefined);
    }

    return Promise.resolve();
  }

  function preloadFrame(filename) {
    return new Promise((resolve) => {
      const img = new Image();
      img.decoding = "async";

      img.onload = async () => {
        await decodeImage(img);
        resolve(resolveUrl(filename));
      };

      img.onerror = () => {
        console.warn("[Celdra] Failed to load frame:", filename);
        resolve(null);
      };

      img.src = resolveUrl(filename);
    });
  }

  async function preloadFrames() {
    const filenames = buildFrameFilenames();
    const urls = await Promise.all(filenames.map(preloadFrame));
    return urls.filter(Boolean);
  }

  function clearTimer(name) {
    if (runtime[name]) {
      clearTimeout(runtime[name]);
      runtime[name] = null;
    }
  }

  function getFrameDurationMs(frameCount) {
    const safeCount = Math.max(1, frameCount || 0);
    return Math.max(16, Math.round((TOTAL_LOOP_MS / safeCount) * FRAME_TIME_MULTIPLIER));
  }

  function setVisibleBuffer(buffer) {
    if (!nodes.frameA || !nodes.frameB) return;

    if (buffer === "a") {
      nodes.frameA.classList.add("is-visible");
      nodes.frameB.classList.remove("is-visible");
    } else {
      nodes.frameB.classList.add("is-visible");
      nodes.frameA.classList.remove("is-visible");
    }

    runtime.activeBuffer = buffer;
  }

  function getBuffers() {
    if (runtime.activeBuffer === "a") {
      return {
        hidden: nodes.frameB,
        nextVisible: "b"
      };
    }

    return {
      hidden: nodes.frameA,
      nextVisible: "a"
    };
  }

  function showFrameInstant(url) {
    const { hidden, nextVisible } = getBuffers();

    if (!hidden) return;

    hidden.src = url;
    setVisibleBuffer(nextVisible);
  }

  function playSequence() {
    if (runtime.isAnimating) return;
    runtime.isAnimating = true;
    clearTimer("frameTimer");

    const frameCount = runtime.frameUrls.length;
    const frameDelay = getFrameDurationMs(frameCount);

    const tick = () => {
      if (!runtime.isAnimating || runtime.frameUrls.length === 0) {
        runtime.frameTimer = null;
        return;
      }

      showFrameInstant(runtime.frameUrls[runtime.frameIndex]);
      runtime.frameIndex = (runtime.frameIndex + 1) % runtime.frameUrls.length;
      runtime.frameTimer = setTimeout(tick, frameDelay);
    };

    tick();
  }

  function stopSequence() {
    runtime.isAnimating = false;
    clearTimer("frameTimer");
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

      clearTimer("mountTimer");
      runtime.mountTimer = setTimeout(() => mountWidget(root, tries + 1), CONFIG.mountRetryDelayMs);
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

    const frameA = document.createElement("img");
    frameA.className = "celdra-frame celdra-frame-a is-visible";
    frameA.alt = "";
    frameA.decoding = "async";

    const frameB = document.createElement("img");
    frameB.className = "celdra-frame celdra-frame-b";
    frameB.alt = "";
    frameB.decoding = "async";

    frameWrap.appendChild(frameA);
    frameWrap.appendChild(frameB);
    root.appendChild(glow);
    root.appendChild(frameWrap);

    return { root, frameA, frameB };
  }

  function applyRootTuningVars(root) {
    root.style.setProperty("--celdra-size", `${CONFIG.sizePx}px`);
    root.style.setProperty("--celdra-right", CONFIG.rightOffset);
    root.style.setProperty("--celdra-bottom", CONFIG.bottomOffset);
    root.style.setProperty("--celdra-scale", String(CONFIG.scale));
  }

  async function init() {
    if (document.getElementById(CONFIG.id) || runtime.isAnimating) return;

    const widget = buildWidgetDom();
    nodes.root = widget.root;
    nodes.frameA = widget.frameA;
    nodes.frameB = widget.frameB;

    applyRootTuningVars(nodes.root);
    mountWidget(nodes.root);

    const urls = await preloadFrames();
    runtime.frameUrls = urls;

    if (runtime.frameUrls.length < MIN_VIABLE_FRAMES) {
      console.warn(
        `[Celdra] Loaded ${runtime.frameUrls.length} frames, below minimum viable set (${MIN_VIABLE_FRAMES}). Animation not started.`
      );
      return;
    }

    runtime.frameIndex = 0;
    runtime.activeBuffer = "a";

    // Prime both buffers so the first swap cannot show an empty image.
    nodes.frameA.src = runtime.frameUrls[0];
    nodes.frameB.src = runtime.frameUrls[0];
    setVisibleBuffer("a");

    // Begin playback from the second frame.
    runtime.frameIndex = 1 % runtime.frameUrls.length;
    playSequence();
  }

  function destroy() {
    stopSequence();
    clearTimer("mountTimer");

    if (nodes.root && nodes.root.parentNode) {
      nodes.root.parentNode.removeChild(nodes.root);
    }

    nodes.root = null;
    nodes.frameA = null;
    nodes.frameB = null;

    runtime.frameUrls = [];
    runtime.frameIndex = 0;
    runtime.activeBuffer = "a";

    window.__celdraCornerLoaded = false;
  }

  window.__destroyCeldraCorner = destroy;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
