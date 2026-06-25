import './style.css';

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Aggressive AOS Initialization - Zero Latency Experience
  if (window.AOS) {
    window.AOS.init({
      duration: 400, // Instant snap reveal
      once: true,
      easing: 'ease-in-out',
      offset: 0, // Load as soon as section enters viewport
      delay: 0,
      disable: false
    });
  }

  // --- MOBILE PRICING LOOP (REMOVED) ---



  // Header Scroll Effect
  const header = document.getElementById('header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });

  // --- MOBILE HAMBURGER MENU ---
  const menuBtn = document.getElementById('mobile-menu-btn');
  const closeBtn = document.getElementById('close-btn');
  const mobileNav = document.getElementById('mobile-nav');

  const openMenu = () => {
    mobileNav.classList.add('open');
    document.body.style.overflow = 'hidden'; // Prevent scroll when menu open
  };

  const closeMenu = () => {
    mobileNav.classList.remove('open');
    document.body.style.overflow = '';
  };

  if (menuBtn) menuBtn.addEventListener('click', openMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMenu);

  // Close menu when any nav link is clicked
  if (mobileNav) {
    mobileNav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', closeMenu);
    });

    // Close when clicking backdrop (outside the nav content)
    mobileNav.addEventListener('click', (e) => {
      if (e.target === mobileNav) closeMenu();
    });
  }

  // --- PARTICLE CONVERGENCE INTRO (Version Reverted) ---
  const preloaderCanvas = document.getElementById('preloader-canvas');
  const introLogoElement = document.getElementById('preloader-logo');

  // Skip intro animation if already seen this session
  const introSeen = sessionStorage.getItem('aloria_intro_seen');
  if (introSeen) {
    document.body.classList.add('loaded');
    document.body.classList.remove('loading-active');
  } else {
    sessionStorage.setItem('aloria_intro_seen', '1');
  }

    if (preloaderCanvas && !introSeen) {
    const ctx = preloaderCanvas.getContext('2d');
    // PERFORMANCE BOOSTER: Cap DPR at 2.0 for buttery smoothness on 2GB RAM phones
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let width = preloaderCanvas.width = window.innerWidth * dpr;
    let height = preloaderCanvas.height = window.innerHeight * dpr;
    preloaderCanvas.style.width = window.innerWidth + 'px';
    preloaderCanvas.style.height = window.innerHeight + 'px';
    ctx.scale(dpr, dpr);

    let particles = [];
    let convergenceComplete = false;
    
    const vCanvas = document.createElement('canvas');
    const vCtx = vCanvas.getContext('2d');
    vCanvas.width = width;
    vCanvas.height = height;
    
    const setupLogoData = () => {
      const isMobile = window.innerWidth < 768;
      const fontSize = isMobile ? Math.min(window.innerWidth * 0.18, 70) : Math.min(window.innerWidth * 0.1, 100);
      
      vCtx.clearRect(0,0, width, height);
      vCtx.save();
      vCtx.scale(dpr, dpr);
      vCtx.font = `800 ${fontSize}px Outfit`;
      vCtx.fillStyle = 'white';
      vCtx.textAlign = 'center';
      vCtx.textBaseline = 'middle';
      
      if (isMobile) {
          vCtx.fillText('ALORIA', window.innerWidth / 2, (window.innerHeight / 2) - (fontSize / 2));
          vCtx.fillText('LABS', window.innerWidth / 2, (window.innerHeight / 2) + (fontSize / 2));
      } else {
          vCtx.fillText('ALORIA LABS', window.innerWidth / 2, window.innerHeight / 2);
      }
      vCtx.restore();
      
      const imageData = vCtx.getImageData(0, 0, width, height);
      const data = imageData.data;
      
      // AUTO-SCALING PERFORMANCE: Larger step means fewer particles (better for 2GB RAM)
      // On mobile we use a slightly larger step (3) to keep it lightning fast
      const step = isMobile ? 4 : 5; 
      
      for(let y = 0; y < window.innerHeight; y += step) {
        for(let x = 0; x < window.innerWidth; x += step) {
          const index = (Math.floor(y * dpr) * width + Math.floor(x * dpr)) * 4;
          if(data[index + 3] > 128) {
             particles.push(new Particle(x, y));
          }
        }
      }
    };

    class Particle {
      constructor(tx, ty) {
        this.x = Math.random() * window.innerWidth;
        this.y = Math.random() * window.innerHeight;
        this.tx = tx;
        this.ty = ty;
        this.size = Math.random() * 2 + 0.5;
        this.color = '#ffffff';
        this.ease = 0.015 + Math.random() * 0.02; // Slower ease for cinematic feel
        this.opacity = 0.8;
        this.isMetallic = false;
        this.shimmerVal = 0;
      }

      update() {
        const dx = this.tx - this.x;
        const dy = this.ty - this.y;
        this.x += dx * this.ease;
        this.y += dy * this.ease;
        
        if (this.isMetallic) {
           this.shimmerVal += 0.02;
           this.size = 1.8 + Math.sin(this.shimmerVal) * 0.4;
        }
      }

      draw(shimmerPos) {
        if (this.isMetallic) {
          const distToShimmer = Math.abs(this.x - shimmerPos);
          const shimmerIntensify = Math.max(0, 1 - (distToShimmer / 120));
          
          ctx.fillStyle = shimmerIntensify > 0.5 ? '#ffffff' : '#b0b0b0'; 
          ctx.shadowBlur = 12 * shimmerIntensify;
          ctx.shadowColor = 'white';
          ctx.globalAlpha = 0.8 + (shimmerIntensify * 0.2);
        } else {
          ctx.fillStyle = this.color;
          ctx.globalAlpha = this.opacity;
        }

        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    let shimmerPos = -200;
    const animatePreloader = () => {
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      let allConverged = true;
      shimmerPos += (window.innerWidth < 768 ? 10 : 15);
      if(shimmerPos > window.innerWidth + 200) shimmerPos = -200;

      particles.forEach(p => {
        p.update();
        p.draw(shimmerPos);
        const dist = Math.sqrt((p.tx - p.x)**2 + (p.ty - p.y)**2);
        if (dist > 3) allConverged = false;
      });

      if (allConverged && !convergenceComplete) {
         convergenceComplete = true;
         particles.forEach(p => p.isMetallic = true);
         setTimeout(revealSite, 2500); 
      }

      if (state !== 'DONE') {
          requestAnimationFrame(animatePreloader);
      }
    };

    const revealSite = () => {
       document.body.classList.add('loaded');
       setTimeout(() => {
            if (window.AOS) window.AOS.init();
            document.body.classList.remove('loading-active');
            state = 'DONE';
       }, 1500);
    };

    let state = 'ACTIVE';
    document.fonts.ready.then(() => {
        setupLogoData();
        animatePreloader();
    });
  }

  // Fallback
  if (!preloaderCanvas && document.body.classList.contains('loading-active')) {
      setTimeout(() => document.body.classList.add('loaded'), 2500);
  }

  // Three.js Antigravity Core
  const initHero3D = () => {
    if (typeof THREE === 'undefined') return;

    const canvas = document.querySelector('#hero-canvas');
    if (!canvas) return;

    const dpr = window.innerWidth < 768 ? 1.5 : (window.devicePixelRatio || 1);
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: window.innerWidth > 768
    });

    renderer.setPixelRatio(dpr);
    renderer.setSize(window.innerWidth, window.innerHeight);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = window.innerWidth < 768 ? 7 : 5;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    const mainLight = new THREE.DirectionalLight(0xffffff, 2);
    mainLight.position.set(5, 5, 5);
    scene.add(mainLight);

    const fillLight = new THREE.DirectionalLight(0xaaaaaa, 2);
    fillLight.position.set(-5, 0, 2);
    scene.add(fillLight);

    const topLight = new THREE.DirectionalLight(0xffffff, 2.5);
    topLight.position.set(0, 5, 0);
    scene.add(topLight);

    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Liquid Metal Core (PBR) - Highly Defined
    const sphereSize = window.innerWidth < 768 ? 1.2 : 1.6;
    const sphereGeometry = new THREE.IcosahedronGeometry(sphereSize, 12);

    // Base solid core
    const sphereMaterial = new THREE.MeshStandardMaterial({
      color: 0xdddddd, // Bright silver
      metalness: 1.0,
      roughness: 0.15,
      emissive: 0x111111,
      emissiveIntensity: 1
    });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);

    // Outer wireframe HUD shell for strict premium definition
    const shellGeometry = new THREE.IcosahedronGeometry(sphereSize + 0.1, 1); // Low poly outline
    const shellMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      wireframe: true,
      transparent: true,
      opacity: 0.2
    });
    const shell = new THREE.Mesh(shellGeometry, shellMaterial);

    coreGroup.add(sphere);
    coreGroup.add(shell);

    // Orbit rings - Thicker, more pronounced
    const orbitSize = window.innerWidth < 768 ? 1.5 : 2.6;
    const torusGeometry = new THREE.TorusGeometry(orbitSize, 0.015, 16, 150);
    const torusMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      metalness: 1.0,
      roughness: 0.1,
      emissive: 0x333333 // Gives a sharp white inner glow
    });

    const rings = [];
    for (let i = 0; i < 3; i++) {
      const ring = new THREE.Mesh(torusGeometry, torusMaterial);
      ring.rotation.x = Math.random() * Math.PI;
      ring.rotation.y = Math.random() * Math.PI;
      coreGroup.add(ring);
      rings.push(ring);
    }

    // Physics Particles
    const particlesCount = 1500;
    const posArray = new Float32Array(particlesCount * 3);
    const velocityArray = new Float32Array(particlesCount * 3);
    for (let i = 0; i < particlesCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 15;
      velocityArray[i] = (Math.random() - 0.5) * 0.01;
    }
    const particlesGeometry = new THREE.BufferGeometry();
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particlesMaterial = new THREE.PointsMaterial({
      size: 0.015,
      color: 0xffffff,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending
    });
    const particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);

    let mouseX = 0, mouseY = 0;
    let targetX = 0, targetY = 0;
    window.addEventListener('mousemove', (e) => {
      targetX = (e.clientX - window.innerWidth / 2) / 200;
      targetY = (e.clientY - window.innerHeight / 2) / 200;
    });

    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    const animate = () => {
      requestAnimationFrame(animate);

      const time = Date.now() * 0.001; // For pulsating physics

      mouseX += (targetX - mouseX) * 0.05;
      mouseY += (targetY - mouseY) * 0.05;

      coreGroup.rotation.y += 0.005;
      coreGroup.rotation.x += 0.002;
      coreGroup.position.x = mouseX;
      coreGroup.position.y = -mouseY;

      // Dynamic Pulse Effect on Core & Shell
      const pulse = 1 + Math.sin(time * 2) * 0.03;
      sphere.scale.set(pulse, pulse, pulse);
      shell.scale.set(pulse * 1.02, pulse * 1.02, pulse * 1.02);
      shell.rotation.y = -time * 0.2; // Spin outer shell slowly opposite

      rings.forEach((ring, i) => {
        ring.rotation.z += 0.01 * (i + 1);
        ring.rotation.x += 0.002 * (i + 1); // Tumbling effect
      });

      const positions = particles.geometry.attributes.position.array;
      for (let i = 0; i < particlesCount; i++) {
        const ix = i * 3;
        const iy = i * 3 + 1;
        positions[ix] += velocityArray[ix] + (mouseX * 0.001);
        positions[iy] += velocityArray[iy] - (mouseY * 0.001);
        if (Math.abs(positions[ix]) > 8) positions[ix] *= -0.9;
        if (Math.abs(positions[iy]) > 8) positions[iy] *= -0.9;
      }
      particles.geometry.attributes.position.needsUpdate = true;
      renderer.render(scene, camera);
    };
    animate();
  };

  initHero3D();



  // 3D Tilt Effect for All Cards
  const handleTilt = (e, card) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -10; // Max tilt 10deg
    const rotateY = ((x - centerX) / centerX) * 10;

    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
  };

  const resetTilt = (card) => {
    card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)`;
  };

  const cardsToTilt = document.querySelectorAll('.card-glass, .service-card, .project-card');
  cardsToTilt.forEach(card => {
    card.addEventListener('mousemove', (e) => handleTilt(e, card));
    card.addEventListener('mouseleave', () => resetTilt(card));
  });

  // Typewriter for CTA
  const typewriter = (element, text, speed = 80) => {
    let j = 0;
    element.textContent = '';
    const type = () => {
      if (j < text.length) {
        element.textContent += text.charAt(j);
        j++;
        setTimeout(type, speed);
      }
    };
    type();
  };
  const ctaHeading = document.getElementById('typewriter-cta');
  if (ctaHeading) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          typewriter(ctaHeading, "Ready to Automate your Success?");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    observer.observe(ctaHeading);
  }

  // Mouse Follow Glow for Hero
  const hero = document.getElementById('home');
  if (hero) {
    hero.addEventListener('mousemove', (e) => {
      const blob1 = document.querySelector('.blob-1');
      const blob2 = document.querySelector('.blob-2');
      if (blob1) blob1.style.transform = `translate(${e.clientX * 0.05}px, ${e.clientY * 0.05}px)`;
      if (blob2) blob2.style.transform = `translate(${-e.clientX * 0.05}px, ${-e.clientY * 0.05}px)`;
    });
  }

  // Smooth Scroll
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const hrefValue = this.getAttribute('href');
      if (hrefValue === '#') return;
      e.preventDefault();
      const targetElement = document.querySelector(hrefValue);
      if (targetElement) targetElement.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // Interactive Capabilities Carousel
  const servicesContainer = document.querySelector('.services-container');
  if (servicesContainer) {
    const toggleInteractive = () => {
      servicesContainer.classList.add('interactive');
    };

    servicesContainer.addEventListener('touchstart', toggleInteractive, { passive: true });
    servicesContainer.addEventListener('mousedown', toggleInteractive);
  }

  // --- ELITE ANIMATIONS OVERHAUL ---

  // 1. Magnetic Buttons (Pull distance based on cursor)
  const buttons = document.querySelectorAll('.btn');
  buttons.forEach(btn => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const h = rect.width / 2;
      const v = rect.height / 2;
      const x = e.clientX - rect.left - h;
      const y = e.clientY - rect.top - v;
      // Magnet pull intensity: 0.2
      btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'translate(0px, 0px)';
    });
  });

  // 2. Spotlight Tracking on Cards
  const trackCards = document.querySelectorAll('.card-glass, .vertical-card, .result-card');
  trackCards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });

  // 3. Hacker/Terminal Text Reveal
  const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
  const hackerElements = document.querySelectorAll('.hacker-text');

  const hackerObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        let iterations = 0;
        const target = entry.target;
        const originalText = target.dataset.original || target.innerText;
        target.dataset.original = originalText;

        clearInterval(target.interval);

        target.interval = setInterval(() => {
          target.innerText = originalText.split("").map((letter, index) => {
            if (index < iterations) {
              return originalText[index];
            }
            return letters[Math.floor(Math.random() * 42)];
          }).join("");

          if (iterations >= originalText.length) {
            clearInterval(target.interval);
          }
          iterations += 1 / 3; // Decode speed
        }, 30);

        hackerObserver.unobserve(target);
      }
    });
  }, { threshold: 0.5 });

  hackerElements.forEach(el => hackerObserver.observe(el));

  // --- FOOTER DUST PARTICLES ---
  const footerCanvas = document.getElementById('footer-canvas');
  if (footerCanvas) {
    const ctx = footerCanvas.getContext('2d');
    let width = footerCanvas.width = footerCanvas.offsetWidth;
    let height = footerCanvas.height = footerCanvas.offsetHeight;

    let particles = [];
    const particleCount = window.innerWidth > 768 ? 80 : 30; // Responsive count

    let mouse = { x: -1000, y: -1000 };
    const footer = document.getElementById('footer');

    footer.addEventListener('mousemove', (e) => {
      const rect = footer.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });

    footer.addEventListener('mouseleave', () => {
      mouse.x = -1000;
      mouse.y = -1000;
    });

    window.addEventListener('resize', () => {
      width = footerCanvas.width = footerCanvas.offsetWidth;
      height = footerCanvas.height = footerCanvas.offsetHeight;
      initParticles();
    });

    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.size = Math.random() * 1.5 + 0.5; // Tiny dots
        this.baseX = this.x;
        this.baseY = this.y;
        this.density = (Math.random() * 20) + 1;
        this.opacity = Math.random() * 0.4 + 0.1;
        this.speedY = Math.random() * 0.5 + 0.1;
      }

      update() {
        // Slow float up loosely imitating anti-gravity
        this.y -= this.speedY;

        if (this.y < -10) {
          this.y = height + 10;
          this.x = Math.random() * width;
          this.baseX = this.x;
        }

        // Mouse interaction (Repel physics)
        let dx = mouse.x - this.x;
        let dy = mouse.y - this.y;
        let distance = Math.sqrt(dx * dx + dy * dy);
        let forceDirectionX = dx / distance;
        let forceDirectionY = dy / distance;
        let maxDistance = 120;
        let force = (maxDistance - distance) / maxDistance;
        let directionX = forceDirectionX * force * this.density;
        let directionY = forceDirectionY * force * this.density;

        if (distance < maxDistance) {
          this.x -= directionX;
          this.y -= directionY;
        } else {
          // Slow elastic return to original trajectory
          if (this.x !== this.baseX) {
            let dx2 = this.x - this.baseX;
            this.x -= dx2 / 40;
          }
        }
      }

      draw() {
        ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fill();
      }
    }

    const initParticles = () => {
      particles = [];
      for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
      }
    };

    const animateParticles = () => {
      ctx.clearRect(0, 0, width, height);
      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
      }
      requestAnimationFrame(animateParticles);
    };

    initParticles();
    animateParticles();
  }

  // --- FLOATING COMM NODE ---
  const contactToggle = document.querySelector('.contact-toggle');
  const floatingContact = document.querySelector('.floating-contact');

  if (contactToggle && floatingContact) {
    contactToggle.addEventListener('click', () => {
      floatingContact.classList.toggle('active');
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!floatingContact.contains(e.target)) {
        floatingContact.classList.remove('active');
      }
    });

    // Email display interaction
    const emailToggle = document.getElementById('email-btn-toggle');
    const emailPopup = document.getElementById('email-popup');

    if (emailToggle && emailPopup) {
      emailToggle.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation(); // Prevent closing when clicking toggle
        emailPopup.classList.toggle('active');

        // Silently copy to clipboard
        if (emailPopup.classList.contains('active')) {
          navigator.clipboard.writeText('alorialabs@gmail.com');
          // Reset text just in case, but keep it as the email
          emailPopup.innerText = 'alorialabs@gmail.com';
        }
      });

      // Close email popup if clicking document body but not toggle or popup
      document.addEventListener('click', (e) => {
        if (!emailToggle.contains(e.target) && !emailPopup.contains(e.target)) {
          emailPopup.classList.remove('active');
        }
      });
    }
  }

});
