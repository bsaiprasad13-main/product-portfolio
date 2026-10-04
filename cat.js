// Pixel-art cat that chases the mouse cursor, inspired by the classic Neko/oneko desktop cat.
// Original sprite: cat-sprite.png (drawn by tools/make-cat-sprite.py). Loaded once from index.html.
(() => {
  // ---- Tunable constants -------------------------------------------------
  const SPEED = 160;              // px per second while running
  const STOP_DISTANCE = 32;       // sits when this close to the cursor (about one sprite width)
  const RUN_FPS = 9;              // leg animation frame rate, independent of the movement loop
  const ALERT_MS = 600;           // how long the alert pose shows before it starts running
  const BLOB_LERP = 0.15;         // follower blob easing per 60 fps frame (lower = more lag)
  const BLOB_SIZE = 26;           // follower blob diameter in px
  const SLEEP_ENABLED = true;     // nap after sitting still for a while
  const SLEEP_AFTER_MS = 12000;   // idle time before the nap starts
  const SLEEP_FPS = 1.5;          // breathing animation rate while asleep
  const Z_INDEX = 150;            // above page content and nav (50-60), below the chat assistant (200)

  // ---- Sprite sheet layout (must match tools/make-cat-sprite.py) ---------
  const SPRITE = 32;
  const FRAMES = {
    idle: [0], alert: [1], sleep: [2, 3],
    E: [4, 5], NE: [6, 7], N: [8, 9], NW: [10, 11],
    W: [12, 13], SW: [14, 15], S: [16, 17], SE: [18, 19],
  };
  const DIRECTIONS = ['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE']; // clockwise from east, 45° each

  // No cursor to chase on touch screens
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const style = document.createElement('style');
  style.textContent = `
    .pixel-cat, .pixel-cat-blob {
      position: fixed;
      left: 0;
      top: 0;
      pointer-events: none;
      will-change: transform;
    }
    .pixel-cat {
      z-index: ${Z_INDEX};
      width: ${SPRITE}px;
      height: ${SPRITE}px;
      background: url("cat-sprite.png") 0 0 no-repeat;
      image-rendering: pixelated;
    }
    .pixel-cat-blob {
      z-index: ${Z_INDEX - 1};
      width: ${BLOB_SIZE}px;
      height: ${BLOB_SIZE}px;
      border-radius: 50%;
      background: rgba(232, 232, 238, 0.55);
      box-shadow: 0 1px 6px rgba(0, 0, 0, 0.12);
      filter: blur(1px);
      opacity: 0;
      transition: opacity 0.25s;
    }
  `;
  document.head.appendChild(style);

  const cat = document.createElement('div');
  cat.className = 'pixel-cat';
  cat.setAttribute('aria-hidden', 'true');
  document.body.appendChild(cat);

  // Cat position is its centre, in viewport coordinates. Spawn in the bottom-left corner
  // (the chat assistant owns the bottom-right).
  let catX = 24 + SPRITE / 2;
  let catY = window.innerHeight - 24 - SPRITE / 2;
  let frame = -1;

  function setFrame(index) {
    if (index === frame) return;
    frame = index;
    cat.style.backgroundPosition = `${-index * SPRITE}px 0`;
  }

  function placeCat() {
    catX = Math.min(Math.max(catX, SPRITE / 2), window.innerWidth - SPRITE / 2);
    catY = Math.min(Math.max(catY, SPRITE / 2), window.innerHeight - SPRITE / 2);
    cat.style.transform = `translate(${Math.round(catX - SPRITE / 2)}px, ${Math.round(catY - SPRITE / 2)}px)`;
  }

  setFrame(FRAMES.idle[0]);
  placeCat();

  if (reduceMotion) {
    // A static cat sitting in the corner; no chasing, no blob
    const onResize = () => { catY = window.innerHeight - 24 - SPRITE / 2; placeCat(); };
    window.addEventListener('resize', onResize);
    window.pixelCat = { destroy() { window.removeEventListener('resize', onResize); cat.remove(); style.remove(); } };
    return;
  }

  const blob = document.createElement('div');
  blob.className = 'pixel-cat-blob';
  blob.setAttribute('aria-hidden', 'true');
  document.body.appendChild(blob);

  let mouseX = 0, mouseY = 0, blobX = 0, blobY = 0;
  let hasMouse = false;   // stays idle in the corner until the first mouse move
  let mouseInside = false;
  let state = 'idle';
  let stateSince = performance.now();
  let animTime = 0;
  let direction = 'E';
  let rafId = 0;
  let last = performance.now();

  function setState(next, now = performance.now()) {
    if (state === next) return;
    state = next;
    stateSince = now;
    animTime = 0;
    if (next === 'idle') setFrame(FRAMES.idle[0]);
    if (next === 'alert') setFrame(FRAMES.alert[0]);
  }

  const distanceToMouse = () => Math.hypot(mouseX - catX, mouseY - catY);

  function onMouseMove(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
    if (!hasMouse) {
      hasMouse = true;
      blobX = mouseX;
      blobY = mouseY;
    }
    if (!mouseInside) {
      mouseInside = true;
      blob.style.opacity = '1';
    }
    // Moving again while it sits (or naps) startles it before it runs
    if ((state === 'idle' || state === 'sleep') && distanceToMouse() > STOP_DISTANCE) setState('alert');
  }

  function onMouseOut(e) {
    if (e.relatedTarget) return; // still inside the page
    mouseInside = false;
    blob.style.opacity = '0';
    if (state === 'run' || state === 'alert') setState('idle'); // settle where it is
  }

  function tick(now) {
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;

    if (hasMouse) {
      const k = 1 - Math.pow(1 - BLOB_LERP, dt * 60); // frame-rate independent easing
      blobX += (mouseX - blobX) * k;
      blobY += (mouseY - blobY) * k;
      blob.style.transform = `translate(${blobX - BLOB_SIZE / 2}px, ${blobY - BLOB_SIZE / 2}px)`;
    }

    if (state === 'alert' && now - stateSince >= ALERT_MS) {
      setState(mouseInside && distanceToMouse() > STOP_DISTANCE ? 'run' : 'idle', now);
    }

    if (state === 'run') {
      const dx = mouseX - catX;
      const dy = mouseY - catY;
      const dist = Math.hypot(dx, dy);
      if (dist <= STOP_DISTANCE) {
        setState('idle', now);
      } else {
        const step = Math.min(SPEED * dt, dist - STOP_DISTANCE);
        catX += (dx / dist) * step;
        catY += (dy / dist) * step;
        placeCat();
        const sector = Math.round(Math.atan2(dy, dx) / (Math.PI / 4));
        direction = DIRECTIONS[(sector + 8) % 8];
        animTime += dt;
        setFrame(FRAMES[direction][Math.floor(animTime * RUN_FPS) % 2]);
      }
    } else if (state === 'idle' && SLEEP_ENABLED && now - stateSince >= SLEEP_AFTER_MS) {
      setState('sleep', now);
    }

    if (state === 'sleep') {
      animTime += dt;
      setFrame(FRAMES.sleep[Math.floor(animTime * SLEEP_FPS) % 2]);
    }

    rafId = requestAnimationFrame(tick);
  }

  function start() {
    if (rafId) return;
    last = performance.now();
    rafId = requestAnimationFrame(tick);
  }

  function stop() {
    cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function onVisibility() {
    if (document.hidden) stop();
    else start();
  }

  function onResize() {
    placeCat();
  }

  document.addEventListener('mousemove', onMouseMove, { passive: true });
  document.addEventListener('mouseout', onMouseOut);
  document.addEventListener('visibilitychange', onVisibility);
  window.addEventListener('resize', onResize);
  if (!document.hidden) start();

  // Clean-up hook (the site is a single page, but this keeps the module removable)
  window.pixelCat = {
    destroy() {
      stop();
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseout', onMouseOut);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('resize', onResize);
      cat.remove();
      blob.remove();
      style.remove();
    },
  };
})();
