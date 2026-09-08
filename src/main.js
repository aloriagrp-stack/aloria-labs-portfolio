import { ParticleTextSimulation } from './particle-text.js';

document.addEventListener('DOMContentLoaded', () => {
  // Initialize the particle text simulation
  const particleSim = new ParticleTextSimulation('particle-canvas');

  // Mobile Navigation Drawer Toggle
  const menuToggle = document.getElementById('menu-toggle');
  const menuClose = document.getElementById('menu-close');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileLinks = document.querySelectorAll('.mobile-nav-link, .mobile-cta-btn');

  const openMobileMenu = () => {
    if (!mobileMenu) return;
    mobileMenu.classList.add('open');
    mobileMenu.setAttribute('aria-hidden', 'false');
    if (menuToggle) menuToggle.setAttribute('aria-expanded', 'true');
    document.documentElement.classList.add('menu-open');
    document.body.classList.add('menu-open');
  };

  const closeMobileMenu = () => {
    if (!mobileMenu) return;
    mobileMenu.classList.remove('open');
    mobileMenu.setAttribute('aria-hidden', 'true');
    if (menuToggle) menuToggle.setAttribute('aria-expanded', 'false');
    document.documentElement.classList.remove('menu-open');
    document.body.classList.remove('menu-open');
  };

  if (menuToggle) {
    menuToggle.addEventListener('click', () => {
      if (mobileMenu?.classList.contains('open')) {
        closeMobileMenu();
      } else {
        openMobileMenu();
      }
    });
  }

  if (menuClose) {
    menuClose.addEventListener('click', closeMobileMenu);
  }

  mobileLinks.forEach((link) => {
    link.addEventListener('click', () => {
      closeMobileMenu();
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileMenu?.classList.contains('open')) {
      closeMobileMenu();
    }
  });

  // Completely prevent background scrolling when mobile menu drawer is open
  const preventBackgroundScroll = (e) => {
    if (mobileMenu?.classList.contains('open')) {
      if (!mobileMenu.contains(e.target)) {
        e.preventDefault();
      }
    }
  };
  window.addEventListener('touchmove', preventBackgroundScroll, { passive: false });
  window.addEventListener('wheel', preventBackgroundScroll, { passive: false });

  // Scroll Indicator click to smoothly scroll to first section
  const scrollIndicator = document.getElementById('scroll-indicator');
  if (scrollIndicator) {
    scrollIndicator.addEventListener('click', () => {
      const targetSection = document.getElementById('about-aloria') || document.getElementById('systems');
      if (targetSection) {
        targetSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  // Subtle interactive cursor ambient glow follower
  const glowOrbCyan = document.querySelector('.glow-orb-cyan');
  const glowOrbViolet = document.querySelector('.glow-orb-violet');

  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;
  let currentX = mouseX;
  let currentY = mouseY;

  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  const updateAmbientGlow = () => {
    currentX += (mouseX - currentX) * 0.05;
    currentY += (mouseY - currentY) * 0.05;

    if (glowOrbCyan) {
      glowOrbCyan.style.transform = `translate(${currentX * 0.08}px, ${currentY * 0.08}px)`;
    }
    if (glowOrbViolet) {
      glowOrbViolet.style.transform = `translate(${-currentX * 0.05}px, ${-currentY * 0.05}px)`;
    }
    requestAnimationFrame(updateAmbientGlow);
  };

  requestAnimationFrame(updateAmbientGlow);

  // URL query parameter handler for plan selection (e.g. /contact.html?plan=sprint)
  const urlParams = new URLSearchParams(window.location.search);
  const requestedPlan = urlParams.get('plan');
  const intakePlanSelect = document.getElementById('intake-plan');
  if (requestedPlan && intakePlanSelect) {
    const matchingOption = Array.from(intakePlanSelect.options).find(
      opt => opt.value.toLowerCase() === requestedPlan.toLowerCase()
    );
    if (matchingOption) {
      intakePlanSelect.value = matchingOption.value;
    }
  }

  // Intake Form Submission Handler
  const intakeForm = document.getElementById('intake-form');
  const intakeStatus = document.getElementById('intake-status');
  const submitBtn = document.getElementById('intake-submit-btn');

  if (intakeForm) {
    intakeForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Encrypting & Transmitting...</span>`;
      }

      const formData = new FormData(intakeForm);
      const data = Object.fromEntries(formData.entries());

      // Simulate enterprise secure transmission or POST to backend
      setTimeout(() => {
        if (intakeStatus) {
          intakeStatus.style.display = 'block';
          intakeStatus.className = 'form-status success';
          intakeStatus.innerHTML = `
            <div class="status-success-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
              <div>
                <strong>Technical Brief Transmitted Successfully.</strong>
                <p>Receipt acknowledged under mutual NDA. Our Lead AI Architect is reviewing your requirements and will respond within 24 hours at <strong>${data.email || 'your email'}</strong>.</p>
              </div>
            </div>
          `;
        }

        intakeForm.reset();

        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span>Transmission Complete // Sent</span>`;
          setTimeout(() => {
            submitBtn.innerHTML = `
              <span>Transmit System Brief</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            `;
          }, 4000);
        }
      }, 1200);
    });
  }

  console.log('Aloria Labs Autonomous Systems Engine Online.');
});
