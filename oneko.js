// oneko.js: https://github.com/adryd325/oneko.js
// Copyright (c) 2022 adryd. MIT License, see oneko-LICENSE.txt.
// Modified for this site:
// - z-index lowered from the maximum to 150 so the cat stays below the chat assistant (200)
// - smooth movement every animation frame (sprites still change at the classic 10 fps)
// - faster, closer, quicker to react (see the tunable constants below)
// - a soft grey circle that trails the mouse cursor

(function oneko() {
  // Tunable constants
  const NEKO_SPEED = 200;       // px per second while running (original: 100)
  const STOP_DISTANCE = 24;     // sits when this close to the cursor (original: 48)
  const ALERT_FRAMES = 3;       // alert pose before running, in 100 ms frames (original: up to 6)
  const ARRIVE_TOLERANCE = 0.5; // px; counts as arrived this close to STOP_DISTANCE
  const BLOB_SIZE = 28;         // px, the circle that trails the cursor
  const BLOB_LERP = 0.2;        // circle easing per 60 fps frame (lower = more lag)

  const isReducedMotion =
    window.matchMedia(`(prefers-reduced-motion: reduce)`) === true ||
    window.matchMedia(`(prefers-reduced-motion: reduce)`).matches === true;

  if (isReducedMotion) return;

  const nekoEl = document.createElement("div");
  const blobEl = document.createElement("div");
  let blobX = 0;
  let blobY = 0;
  let blobVisible = false;
  let persistPosition = true;

  let nekoPosX = 32;
  let nekoPosY = 32;
  
  let mousePosX = 0;
  let mousePosY = 0;

  let frameCount = 0;
  let idleTime = 0;
  let idleAnimation = null;
  let idleAnimationFrame = 0;

  let running = false;
  let runDirX = 0;
  let runDirY = 0;
  const spriteSets = {
    idle: [[-3, -3]],
    alert: [[-7, -3]],
    scratchSelf: [
      [-5, 0],
      [-6, 0],
      [-7, 0],
    ],
    scratchWallN: [
      [0, 0],
      [0, -1],
    ],
    scratchWallS: [
      [-7, -1],
      [-6, -2],
    ],
    scratchWallE: [
      [-2, -2],
      [-2, -3],
    ],
    scratchWallW: [
      [-4, 0],
      [-4, -1],
    ],
    tired: [[-3, -2]],
    sleeping: [
      [-2, 0],
      [-2, -1],
    ],
    N: [
      [-1, -2],
      [-1, -3],
    ],
    NE: [
      [0, -2],
      [0, -3],
    ],
    E: [
      [-3, 0],
      [-3, -1],
    ],
    SE: [
      [-5, -1],
      [-5, -2],
    ],
    S: [
      [-6, -3],
      [-7, -2],
    ],
    SW: [
      [-5, -3],
      [-6, -1],
    ],
    W: [
      [-4, -2],
      [-4, -3],
    ],
    NW: [
      [-1, 0],
      [-1, -1],
    ],
  };

  function init() {
    let nekoFile = "./oneko.gif"
    const curScript = document.currentScript
    if (curScript && curScript.dataset.cat) {
      nekoFile = curScript.dataset.cat
    }
    if (curScript && curScript.dataset.persistPosition) {
      if (curScript.dataset.persistPosition === "") {
        persistPosition = true;
      } else {
        persistPosition = JSON.parse(curScript.dataset.persistPosition.toLowerCase());
      }
    }
  
    if (persistPosition) {
      let storedNeko = JSON.parse(window.localStorage.getItem("oneko"));
      if (storedNeko !== null) {
        nekoPosX = storedNeko.nekoPosX;
        nekoPosY = storedNeko.nekoPosY;
        mousePosX = storedNeko.mousePosX;
        mousePosY = storedNeko.mousePosY;
        frameCount = storedNeko.frameCount;
        idleTime = storedNeko.idleTime;
        idleAnimation = storedNeko.idleAnimation;
        idleAnimationFrame = storedNeko.idleAnimationFrame;
        nekoEl.style.backgroundPosition = storedNeko.bgPos;
      }
    }
  
    nekoEl.id = "oneko";
    nekoEl.ariaHidden = true;
    nekoEl.style.width = "32px";
    nekoEl.style.height = "32px";
    nekoEl.style.position = "fixed";
    nekoEl.style.pointerEvents = "none";
    nekoEl.style.imageRendering = "pixelated";
    nekoEl.style.left = `${nekoPosX - 16}px`;
    nekoEl.style.top = `${nekoPosY - 16}px`;
    nekoEl.style.zIndex = 150;

    nekoEl.style.backgroundImage = `url(${nekoFile})`;
    
    document.body.appendChild(nekoEl);

    // Soft grey circle that trails the mouse cursor
    blobEl.ariaHidden = true;
    Object.assign(blobEl.style, {
      position: "fixed",
      left: "0",
      top: "0",
      width: `${BLOB_SIZE}px`,
      height: `${BLOB_SIZE}px`,
      borderRadius: "50%",
      background: "rgba(200, 200, 210, 0.45)",
      boxShadow: "0 1px 6px rgba(0, 0, 0, 0.12)",
      filter: "blur(1px)",
      pointerEvents: "none",
      zIndex: 149,
      opacity: "0",
      transition: "opacity 0.2s",
      willChange: "transform",
    });
    document.body.appendChild(blobEl);

    document.addEventListener("mousemove", function (event) {
      mousePosX = event.clientX;
      mousePosY = event.clientY;
      if (!blobVisible) {
        blobX = mousePosX;
        blobY = mousePosY;
        blobVisible = true;
        blobEl.style.opacity = "1";
      }
    });
    document.addEventListener("mouseout", function (event) {
      if (event.relatedTarget) return; // still inside the page
      blobVisible = false;
      blobEl.style.opacity = "0";
    });
    
    if (persistPosition) {
      window.addEventListener("beforeunload", function (event) {
        window.localStorage.setItem("oneko", JSON.stringify({
          nekoPosX: nekoPosX,
          nekoPosY: nekoPosY,
          mousePosX: mousePosX,
          mousePosY: mousePosY,
          frameCount: frameCount,
          idleTime: idleTime,
          idleAnimation: idleAnimation,
          idleAnimationFrame: idleAnimationFrame,
          bgPos: nekoEl.style.backgroundPosition
        }));
      });
    }
    
    window.requestAnimationFrame(onAnimationFrame);
  }

  let lastFrameTimestamp;
  let lastMoveTimestamp;

  function onAnimationFrame(timestamp) {
    // Stops execution if the neko element is removed from DOM
    if (!nekoEl.isConnected) {
      return;
    }
    if (!lastFrameTimestamp) {
      lastFrameTimestamp = timestamp;
    }
    if (!lastMoveTimestamp) {
      lastMoveTimestamp = timestamp;
    }
    const dt = Math.min((timestamp - lastMoveTimestamp) / 1000, 0.1);
    lastMoveTimestamp = timestamp;

    // Sprite and state changes keep the classic 10 fps rhythm
    if (timestamp - lastFrameTimestamp > 100) {
      lastFrameTimestamp = timestamp;
      frame();
    }
    // Position updates every frame, so running looks smooth
    if (running) {
      move(dt);
    }
    if (blobVisible) {
      const k = 1 - Math.pow(1 - BLOB_LERP, dt * 60);
      blobX += (mousePosX - blobX) * k;
      blobY += (mousePosY - blobY) * k;
      blobEl.style.transform = `translate(${blobX - BLOB_SIZE / 2}px, ${blobY - BLOB_SIZE / 2}px)`;
    }
    window.requestAnimationFrame(onAnimationFrame);
  }

  function move(dt) {
    const diffX = mousePosX - nekoPosX;
    const diffY = mousePosY - nekoPosY;
    const distance = Math.sqrt(diffX ** 2 + diffY ** 2);
    // Arrive within half a pixel; otherwise floating-point leftovers can keep it
    // "running" on the spot forever
    if (distance <= STOP_DISTANCE + ARRIVE_TOLERANCE) {
      running = false;
      return;
    }
    const step = Math.min(NEKO_SPEED * dt, distance - STOP_DISTANCE);
    nekoPosX += (diffX / distance) * step;
    nekoPosY += (diffY / distance) * step;

    nekoPosX = Math.min(Math.max(16, nekoPosX), window.innerWidth - 16);
    nekoPosY = Math.min(Math.max(16, nekoPosY), window.innerHeight - 16);

    nekoEl.style.left = `${nekoPosX - 16}px`;
    nekoEl.style.top = `${nekoPosY - 16}px`;
  }

  function setSprite(name, frame) {
    const sprite = spriteSets[name][frame % spriteSets[name].length];
    nekoEl.style.backgroundPosition = `${sprite[0] * 32}px ${sprite[1] * 32}px`;
  }

  function resetIdleAnimation() {
    idleAnimation = null;
    idleAnimationFrame = 0;
  }

  function idle() {
    idleTime += 1;

    // every ~ 20 seconds
    if (
      idleTime > 10 &&
      Math.floor(Math.random() * 200) == 0 &&
      idleAnimation == null
    ) {
      let avalibleIdleAnimations = ["sleeping", "scratchSelf"];
      if (nekoPosX < 32) {
        avalibleIdleAnimations.push("scratchWallW");
      }
      if (nekoPosY < 32) {
        avalibleIdleAnimations.push("scratchWallN");
      }
      if (nekoPosX > window.innerWidth - 32) {
        avalibleIdleAnimations.push("scratchWallE");
      }
      if (nekoPosY > window.innerHeight - 32) {
        avalibleIdleAnimations.push("scratchWallS");
      }
      idleAnimation =
        avalibleIdleAnimations[
          Math.floor(Math.random() * avalibleIdleAnimations.length)
        ];
    }

    switch (idleAnimation) {
      case "sleeping":
        if (idleAnimationFrame < 8) {
          setSprite("tired", 0);
          break;
        }
        setSprite("sleeping", Math.floor(idleAnimationFrame / 4));
        if (idleAnimationFrame > 192) {
          resetIdleAnimation();
        }
        break;
      case "scratchWallN":
      case "scratchWallS":
      case "scratchWallE":
      case "scratchWallW":
      case "scratchSelf":
        setSprite(idleAnimation, idleAnimationFrame);
        if (idleAnimationFrame > 9) {
          resetIdleAnimation();
        }
        break;
      default:
        setSprite("idle", 0);
        return;
    }
    idleAnimationFrame += 1;
  }

  function frame() {
    frameCount += 1;
    const diffX = nekoPosX - mousePosX;
    const diffY = nekoPosY - mousePosY;
    const distance = Math.sqrt(diffX ** 2 + diffY ** 2);

    // While sitting, ignore small cursor jitters (8px of slack) so it doesn't hop back and forth
    if (distance <= STOP_DISTANCE + (running ? ARRIVE_TOLERANCE : 8)) {
      running = false;
      idle();
      return;
    }

    idleAnimation = null;
    idleAnimationFrame = 0;

    if (idleTime > 1) {
      running = false;
      setSprite("alert", 0);
      // count down after being alerted before moving
      idleTime = Math.min(idleTime, ALERT_FRAMES + 1);
      idleTime -= 1;
      return;
    }

    let direction;
    direction = diffY / distance > 0.5 ? "N" : "";
    direction += diffY / distance < -0.5 ? "S" : "";
    direction += diffX / distance > 0.5 ? "W" : "";
    direction += diffX / distance < -0.5 ? "E" : "";
    setSprite(direction, frameCount);

    // Movement itself happens every animation frame in move()
    running = true;
  }

  init();
})();
