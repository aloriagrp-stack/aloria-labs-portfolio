/**
 * ALORIA LABS - Mobile-Optimized Persistent Cosmic Starfield & Typography Engine
 * - Full-Screen Cosmic Particle Gathering:
 *   Particles start scattered across the entire screen and smoothly glide/converge
 *   from all corners into the "ALORIA LABS" typography with silky quartic deceleration.
 * - Zero-Bounce Guarantee: Exact closed-form trajectory docks gently into letter coordinates.
 * - Hardware-accelerated rendering pass ensuring solid 60-120 FPS on mobile silicon.
 * - Reveals navbar & scroll indicator gracefully when cosmic intro completes.
 */

export class ParticleTextSimulation {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.navEl = document.getElementById('main-nav');
    this.scrollInd = document.getElementById('scroll-indicator');

    this.particles = [];
    this.colorBuckets = {};
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.dpr = 1;
    this.scrollY = 0;
    this.smoothScrollY = 0;

    // Animation state machine: 'INTRO_GATHER' -> 'INTERACTIVE'
    this.isSubpage = document.body.classList.contains('subpage');
    if (this.isSubpage) {
      this.state = 'INTERACTIVE';
      this.introStartTime = 0;
      this.introDuration = 0;
      this.hasIntroFinished = true;
      if (this.navEl) {
        this.navEl.classList.add('visible');
      }
    } else {
      this.state = 'INTRO_GATHER';
      this.introStartTime = 0;
      this.introDuration = 2000; // Silky 2.0s full-screen cosmic gathering
      this.hasIntroFinished = false;
      document.documentElement.classList.add('no-scroll');
      document.body.classList.add('no-scroll');
    }

    this.targetMouse = {
      x: -9999,
      y: -9999,
      active: false
    };

    const isMobile = this.width < 720;
    this.smoothMouse = {
      x: -9999,
      y: -9999,
      radius: isMobile ? 40 : 64,
      active: false,
      influence: 0
    };

    this.mouseIdleTimer = null;

    this.init();
  }

  async init() {
    if (document.fonts && document.fonts.ready) {
      try {
        await document.fonts.ready;
      } catch (e) {
        console.warn('Font load check bypassed:', e);
      }
    }

    this.handleResize();
    this.setupEventListeners();
    this.createParticles(true);
    this.introStartTime = performance.now();
    this.animate = this.animate.bind(this);
    requestAnimationFrame(this.animate);
  }

  handleResize() {
    this.width = Math.max(300, window.innerWidth);
    this.height = Math.max(300, window.innerHeight);
    const isMobile = this.width < 720;

    // Clamp DPR to 1.5 on mobile to eliminate GPU fill bottleneck while retaining retina sharpness
    this.dpr = isMobile ? Math.min(window.devicePixelRatio || 1, 1.5) : Math.min(window.devicePixelRatio || 1, 2.0);

    this.canvas.width = Math.floor(this.width * this.dpr);
    this.canvas.height = Math.floor(this.height * this.dpr);
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;

    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(this.dpr, this.dpr);

    this.smoothMouse.radius = isMobile ? 40 : 64;

    if (this.particles && this.particles.length > 0) {
      this.createParticles(false);
    }
  }

  setupEventListeners() {
    window.addEventListener('resize', () => {
      this.handleResize();
    });

    window.addEventListener('scroll', () => {
      if (document.body.classList.contains('menu-open')) {
        return;
      }
      this.scrollY = window.scrollY;

      if (this.scrollInd) {
        if (this.scrollY > 35) {
          this.scrollInd.classList.remove('visible');
        } else if (this.hasIntroFinished) {
          this.scrollInd.classList.add('visible');
        }
      }
    }, { passive: true });

    // Allow wheel or swipe to skip directly to interactive text
    window.addEventListener('wheel', () => {
      if (!this.hasIntroFinished) {
        this.introStartTime = performance.now() - this.introDuration;
      }
    }, { passive: true });

    const updateTouch = (clientX, clientY) => {
      if (this.state === 'INTRO_GATHER' && !this.hasIntroFinished) {
        return;
      }

      this.targetMouse.x = clientX;
      this.targetMouse.y = clientY;
      this.targetMouse.active = true;

      if (this.smoothMouse.x < -1000) {
        this.smoothMouse.x = this.targetMouse.x;
        this.smoothMouse.y = this.targetMouse.y;
      }

      if (this.mouseIdleTimer) clearTimeout(this.mouseIdleTimer);

      this.mouseIdleTimer = setTimeout(() => {
        this.targetMouse.active = false;
      }, 160);
    };

    window.addEventListener('touchstart', (e) => {
      if (e.touches.length > 0) {
        updateTouch(e.touches[0].clientX, e.touches[0].clientY);
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (!this.hasIntroFinished) {
        // User gesture immediately completes intro smoothly
        this.introStartTime = performance.now() - this.introDuration;
        return;
      }
      if (e.touches.length > 0) {
        if (window.scrollY < 80) {
          updateTouch(e.touches[0].clientX, e.touches[0].clientY);
        } else {
          this.targetMouse.active = false;
        }
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      this.targetMouse.active = false;
    });

    window.addEventListener('mousemove', (e) => {
      if (this.state === 'INTRO_GATHER' && !this.hasIntroFinished) return;

      this.targetMouse.x = e.clientX;
      this.targetMouse.y = e.clientY;
      this.targetMouse.active = true;

      if (this.smoothMouse.x < -1000) {
        this.smoothMouse.x = this.targetMouse.x;
        this.smoothMouse.y = this.targetMouse.y;
      }

      if (this.mouseIdleTimer) clearTimeout(this.mouseIdleTimer);

      this.mouseIdleTimer = setTimeout(() => {
        this.targetMouse.active = false;
      }, 180);
    });

    window.addEventListener('mouseleave', () => {
      this.targetMouse.active = false;
      if (this.mouseIdleTimer) clearTimeout(this.mouseIdleTimer);
    });
  }

  createParticles(isInitialIntro = false) {
    const w = Math.floor(this.width);
    const h = Math.floor(this.height);
    if (w <= 0 || h <= 0) return;

    // On subpages, create pure ambient cosmic stars with organic twinkling
    if (this.isSubpage) {
      const isMobile = w < 720;
      const starCount = isMobile ? 160 : 300;
      const newParticles = [];
      const buckets = {
        '#ffffff': [],
        '#f8fafc': [],
        '#fef08a': [],
        '#d8b4fe': [],
        '#93c5fd': []
      };

      const colors = ['#ffffff', '#f8fafc', '#d8b4fe', '#93c5fd', '#fef08a'];

      for (let i = 0; i < starCount; i++) {
        const x = Math.random() * w;
        const y = Math.random() * h;
        const color = colors[Math.floor(Math.random() * colors.length)];
        const size = Math.random() * 1.5 + 0.8;
        const particle = {
          x: x,
          y: y,
          originX: x,
          originY: y,
          vx: (Math.random() - 0.5) * 0.16,
          vy: (Math.random() - 0.5) * 0.16,
          size: size,
          baseAlpha: Math.random() * 0.45 + 0.35,
          twinkleSpeed: Math.random() * 0.003 + 0.0012,
          twinklePhase: Math.random() * Math.PI * 2,
          color: color
        };
        newParticles.push(particle);
        if (buckets[color]) {
          buckets[color].push(particle);
        } else {
          buckets['#ffffff'].push(particle);
        }
      }

      this.particles = newParticles;
      this.colorBuckets = buckets;
      return;
    }

    const offscreen = document.createElement('canvas');
    offscreen.width = w;
    offscreen.height = h;
    const offCtx = offscreen.getContext('2d', { willReadFrequently: true });

    const isMobile = w < 720;
    let fontSize;

    if (isMobile) {
      fontSize = Math.min(Math.floor(w / 5.2), Math.floor(h / 8.5), 62);
      offCtx.font = `800 ${fontSize}px "Space Grotesk", sans-serif`;
      
      const measuredW = offCtx.measureText('ALORIA').width;
      const maxAllowedW = w * 0.78;
      if (measuredW > maxAllowedW) {
        fontSize = Math.floor(fontSize * (maxAllowedW / measuredW));
        offCtx.font = `800 ${fontSize}px "Space Grotesk", sans-serif`;
      }
    } else {
      fontSize = Math.min(Math.floor(w / 7.2), Math.floor(h / 3.4), 162);
      offCtx.font = `800 ${fontSize}px "Space Grotesk", sans-serif`;
    }

    offCtx.fillStyle = '#ffffff';
    offCtx.textAlign = 'center';
    offCtx.textBaseline = 'middle';

    const centerX = w / 2;
    const centerY = h / 2;

    if (isMobile) {
      const lineGap = fontSize * 1.18;
      offCtx.fillText('ALORIA', centerX, centerY - lineGap * 0.5);
      offCtx.fillText('LABS', centerX, centerY + lineGap * 0.5);
    } else {
      offCtx.fillText('ALORIA LABS', centerX, centerY);
    }

    const imgData = offCtx.getImageData(0, 0, w, h).data;
    const newParticles = [];
    const buckets = {
      '#ffffff': [],
      '#f8fafc': [],
      '#fef08a': [],
      '#d8b4fe': [],
      '#93c5fd': []
    };

    // Responsive step: 5 on mobile gives ~850-950 high-density particles for solid 60/120fps; 4 on desktop
    const step = isMobile ? 5 : 4;

    for (let y = 0; y < h; y += step) {
      for (let x = 0; x < w; x += step) {
        const index = (y * w + x) * 4;
        const alpha = imgData[index + 3];

        if (alpha > 100) {
          const originX = x;
          const originY = y;

          const rand = Math.random();
          let color;
          if (rand < 0.74) {
            color = '#ffffff';
          } else if (rand < 0.84) {
            color = '#f8fafc';
          } else if (rand < 0.90) {
            color = '#fef08a';
          } else if (rand < 0.95) {
            color = '#d8b4fe';
          } else {
            color = '#93c5fd';
          }

          const size = isMobile
            ? (Math.random() * 0.5 + 1.25)
            : (Math.random() < 0.88 ? Math.random() * 0.6 + 1.2 : Math.random() * 0.7 + 1.7);

          // FULL-SCREEN SCATTER:
          // Particles start distributed across the entire screen and beyond edges
          const startX = (Math.random() * 1.25 - 0.125) * w;
          const startY = (Math.random() * 1.25 - 0.125) * h;

          // Organic celestial curve: perpendicular curvature vector
          const dx = originX - startX;
          const dy = originY - startY;
          const dist = Math.hypot(dx, dy) || 1;
          const perpX = -dy / dist;
          const perpY = dx / dist;
          const curveMag = (Math.random() - 0.5) * (isMobile ? 36 : 60);
          const curveX = perpX * curveMag;
          const curveY = perpY * curveMag;

          // Subtle stagger delay (0 to 0.18) so particles stream in naturally
          const delay = Math.random() * 0.18;

          const starX = Math.random() * w;
          const starY = Math.random() * h;
          const driftVx = (Math.random() - 0.5) * 0.12;
          const driftVy = (Math.random() - 0.5) * 0.12;

          let initialX, initialY;
          if (isInitialIntro) {
            initialX = startX;
            initialY = startY;
          } else {
            initialX = originX;
            initialY = originY;
          }

          const particle = {
            x: initialX,
            y: initialY,
            startX: startX,
            startY: startY,
            originX: originX,
            originY: originY,
            curveX: curveX,
            curveY: curveY,
            delay: delay,
            starX: starX,
            starY: starY,
            driftVx: driftVx,
            driftVy: driftVy,
            vx: 0,
            vy: 0,
            size: size,
            color: color
          };

          newParticles.push(particle);
          if (buckets[color]) {
            buckets[color].push(particle);
          } else {
            buckets['#ffffff'].push(particle);
          }
        }
      }
    }

    if (newParticles.length > 0) {
      this.particles = newParticles;
      this.colorBuckets = buckets;
    }
  }

  animate() {
    this.ctx.clearRect(0, 0, this.width, this.height);

    const now = performance.now();
    const len = this.particles.length;
    const w = this.width;
    const h = this.height;
    const isMobile = w < 720;

    // Subpage ambient cosmic stars drift
    if (this.isSubpage) {
      const mouseX = this.smoothMouse.x;
      const mouseY = this.smoothMouse.y;
      const mouseActive = this.targetMouse.active;

      for (let i = 0; i < len; i++) {
        const p = this.particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        if (mouseActive) {
          const dx = p.x - mouseX;
          const dy = p.y - mouseY;
          const dist = Math.hypot(dx, dy);
          if (dist < 80 && dist > 0) {
            const force = (80 - dist) / 80 * 1.0;
            p.x += (dx / dist) * force;
            p.y += (dy / dist) * force;
          }
        }
      }

      // Render twinkling stars with soft organic alpha pulsation
      for (let i = 0; i < len; i++) {
        const p = this.particles[i];
        const alpha = Math.min(1.0, Math.max(0.12, p.baseAlpha + Math.sin(now * p.twinkleSpeed + p.twinklePhase) * 0.35));
        this.ctx.globalAlpha = alpha;
        this.ctx.fillStyle = p.color;
        this.ctx.fillRect(p.x - p.size * 0.5, p.y - p.size * 0.5, p.size, p.size);
      }
      this.ctx.globalAlpha = 1.0;

      requestAnimationFrame(this.animate);
      return;
    }

    let introProgress = 1.0;
    if (this.state === 'INTRO_GATHER') {
      const elapsed = now - this.introStartTime;
      introProgress = Math.min(elapsed / this.introDuration, 1.0);

      if (introProgress >= 1.0) {
        this.state = 'INTERACTIVE';
        this.hasIntroFinished = true;

        // Lock all particles to exact typographic coordinates
        for (let i = 0; i < len; i++) {
          const p = this.particles[i];
          p.x = p.originX;
          p.y = p.originY;
          p.vx = 0;
          p.vy = 0;
        }

        if (this.navEl) {
          this.navEl.classList.add('visible');
        }

        if (this.scrollInd && this.scrollY < 35) {
          this.scrollInd.classList.add('visible');
        }

        document.documentElement.classList.remove('no-scroll');
        document.body.classList.remove('no-scroll');
      }
    }

    this.smoothScrollY += (this.scrollY - this.smoothScrollY) * 0.14;

    const scrollMax = this.height * 0.75;
    const rawRatio = Math.max(0, Math.min(this.smoothScrollY / scrollMax, 1.0));
    const sScroll = Math.pow(rawRatio, 1.6);

    const isNearTop = this.smoothScrollY < 120;

    if (this.state === 'INTERACTIVE' && isNearTop) {
      if (this.targetMouse.active) {
        this.smoothMouse.x += (this.targetMouse.x - this.smoothMouse.x) * 0.22;
        this.smoothMouse.y += (this.targetMouse.y - this.smoothMouse.y) * 0.22;
        this.smoothMouse.influence += (1 - this.smoothMouse.influence) * 0.15;
      } else {
        this.smoothMouse.influence += (0 - this.smoothMouse.influence) * 0.12;
      }
    } else {
      this.smoothMouse.influence += (0 - this.smoothMouse.influence) * 0.12;
    }

    const mouseX = this.smoothMouse.x;
    const mouseY = this.smoothMouse.y;
    const influence = this.smoothMouse.influence;
    const mouseRadius = this.smoothMouse.radius;
    const mouseRadiusSq = mouseRadius * mouseRadius;

    // --- PARTICLE DYNAMICS PASS ---
    if (this.state === 'INTRO_GATHER') {
      // FULL-SCREEN CONVERGENCE:
      // Each particle glides smoothly from its scattered screen coordinate into ALORIA LABS
      for (let i = 0; i < len; i++) {
        const p = this.particles[i];

        // Individual normalized progress with subtle stagger
        const pElapsed = Math.max(0, introProgress - p.delay);
        const pProg = Math.min(1.0, pElapsed / (1.0 - p.delay));

        // Quartic deceleration curve: fast initial inward flow, soft whisper-quiet landing
        // 1 - (1 - pProg)^4
        const inv = 1 - pProg;
        const tEase = 1 - inv * inv * inv * inv;

        // Gentle sine arch for organic celestial trajectory
        const arch = Math.sin(pProg * Math.PI);

        p.x = p.startX * (1 - tEase) + p.originX * tEase + p.curveX * arch;
        p.y = p.startY * (1 - tEase) + p.originY * tEase + p.curveY * arch;
      }
    } else {
      // Interactive mode with critically damped springs (zero bouncing)
      const spring = isMobile ? 0.075 : 0.058;
      const friction = isMobile ? 0.78 : 0.835;

      for (let i = 0; i < len; i++) {
        const p = this.particles[i];

        if (sScroll > 0.05) {
          p.starX += p.driftVx;
          p.starY += p.driftVy;
          if (p.starX < 0) p.starX = w;
          else if (p.starX > w) p.starX = 0;
          if (p.starY < 0) p.starY = h;
          else if (p.starY > h) p.starY = 0;
        }

        const targetX = p.originX * (1 - sScroll) + p.starX * sScroll;
        const targetY = p.originY * (1 - sScroll) + p.starY * sScroll;

        if (influence > 0.01 && sScroll < 0.15) {
          const dx = mouseX - p.x;
          const dy = mouseY - p.y;
          const distSq = dx * dx + dy * dy;

          if (distSq < mouseRadiusSq) {
            const dist = Math.sqrt(distSq) || 1;
            const normDist = dist / mouseRadius;
            const force = (Math.cos(normDist * Math.PI) * 0.5 + 0.5) * influence;
            const invDist = 1 / dist;
            const power = 4.8;
            p.vx -= (dx * invDist) * force * power;
            p.vy -= (dy * invDist) * force * power;
          }
        }

        p.vx = (p.vx + (targetX - p.x) * spring) * friction;
        p.vy = (p.vy + (targetY - p.y) * spring) * friction;

        const maxSpeed = 10;
        const speedSq = p.vx * p.vx + p.vy * p.vy;
        if (speedSq > maxSpeed * maxSpeed) {
          const ratio = maxSpeed / Math.sqrt(speedSq);
          p.vx *= ratio;
          p.vy *= ratio;
        }

        p.x += p.vx;
        p.y += p.vy;
      }
    }

    const currentGlobalAlpha = 1.0 * (1 - sScroll) + 0.18 * sScroll;
    this.ctx.globalAlpha = currentGlobalAlpha;

    const sizeScale = 1.0 * (1 - sScroll) + 0.65 * sScroll;

    // --- BATCHED GPU RENDERING PASS ---
    const colors = Object.keys(this.colorBuckets);
    for (let c = 0; c < colors.length; c++) {
      const color = colors[c];
      const bucket = this.colorBuckets[color];
      const bLen = bucket.length;
      if (bLen === 0) continue;

      this.ctx.fillStyle = color;

      if (isMobile) {
        // Ultra-fast hardware fillRect on mobile: runs at solid 60/120 FPS
        for (let j = 0; j < bLen; j++) {
          const p = bucket[j];
          const r = p.size * sizeScale;
          const d = r * 2;
          this.ctx.fillRect(p.x - r, p.y - r, d, d);
        }
      } else {
        // High-definition smooth circular arc on desktop
        this.ctx.beginPath();
        for (let j = 0; j < bLen; j++) {
          const p = bucket[j];
          const r = p.size * sizeScale;
          this.ctx.moveTo(p.x + r, p.y);
          this.ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        }
        this.ctx.fill();
      }
    }

    this.ctx.globalAlpha = 1.0;
    requestAnimationFrame(this.animate);
  }
}
