/* ==========================================================================
   JNPHS (JNP High School) - Master JavaScript
   Interactive functionality: Theme Switcher, Counter Animation, Gallery Filter,
   Lightbox Modal, Form Validation, and Responsive Navigation.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize all interactive modules
  initThemeSwitcher();
  initNavigation();
  initStatCounters();
  initGalleryLightbox();
  initFormValidation();
  initBackToTop();
  initAccordions();
});

/* --------------------------------------------------------------------------
   1. Dark / Light Mode Switcher
   -------------------------------------------------------------------------- */
function initThemeSwitcher() {
  const themeToggleBtn = document.getElementById('theme-toggle');
  if (!themeToggleBtn) return;

  const currentTheme = localStorage.getItem('jnphs_theme') || 'light';
  document.documentElement.setAttribute('data-theme', currentTheme);
  updateThemeIcon(themeToggleBtn, currentTheme);

  themeToggleBtn.addEventListener('click', () => {
    const activeTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('jnphs_theme', newTheme);
    updateThemeIcon(themeToggleBtn, newTheme);

    showToast(`Switched to ${newTheme.toUpperCase()} mode`);
  });
}

function updateThemeIcon(btn, theme) {
  const icon = btn.querySelector('i');
  if (!icon) return;
  if (theme === 'dark') {
    icon.className = 'fas fa-sun';
    btn.setAttribute('title', 'Switch to Light Mode');
  } else {
    icon.className = 'fas fa-moon';
    btn.setAttribute('title', 'Switch to Dark Mode');
  }
}

/* --------------------------------------------------------------------------
   2. Sticky Navigation & Mobile Menu
   -------------------------------------------------------------------------- */
function initNavigation() {
  const navbar = document.querySelector('.navbar');
  const hamburger = document.querySelector('.hamburger');
  const navMenu = document.querySelector('.nav-menu');
  const navLinks = document.querySelectorAll('.nav-link');

  // Sticky navbar shadow on scroll
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar?.classList.add('scrolled');
    } else {
      navbar?.classList.remove('scrolled');
    }
  });

  // Mobile menu toggle
  if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      navMenu.classList.toggle('active');
    });

    // Close menu when link is clicked
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
      });
    });
  }

  // Active navigation highlight based on current HTML page
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

/* --------------------------------------------------------------------------
   3. Animated Statistics Counter
   -------------------------------------------------------------------------- */
function initStatCounters() {
  const statNumbers = document.querySelectorAll('.stat-number');
  if (statNumbers.length === 0) return;

  let hasAnimated = false;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !hasAnimated) {
        hasAnimated = true;
        statNumbers.forEach(stat => {
          const target = parseInt(stat.getAttribute('data-target'), 10);
          const suffix = stat.getAttribute('data-suffix') || '';
          const duration = 2000;
          const stepTime = 30;
          const steps = duration / stepTime;
          const increment = target / steps;
          let current = 0;

          const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
              stat.textContent = target + suffix;
              clearInterval(timer);
            } else {
              stat.textContent = Math.floor(current) + suffix;
            }
          }, stepTime);
        });
      }
    });
  }, { threshold: 0.3 });

  const statsSection = document.querySelector('.stats-section');
  if (statsSection) observer.observe(statsSection);
}

/* --------------------------------------------------------------------------
   4. Gallery Filtering & Lightbox Viewer
   -------------------------------------------------------------------------- */
function initGalleryLightbox() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const galleryItems = document.querySelectorAll('.gallery-item');
  const lightbox = document.getElementById('lightbox');

  if (!galleryItems.length) return;

  // Filter functionality
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');

      galleryItems.forEach(item => {
        const category = item.getAttribute('data-category');
        if (filter === 'all' || category === filter) {
          item.style.display = 'flex';
          item.style.animation = 'fadeUp 0.4s ease forwards';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });

  // Lightbox Modal functionality
  if (!lightbox) return;

  const lightboxImg = lightbox.querySelector('.lightbox-img');
  const lightboxCaption = lightbox.querySelector('.lightbox-caption');
  const closeBtn = lightbox.querySelector('.lightbox-close');
  const prevBtn = lightbox.querySelector('.lightbox-prev');
  const nextBtn = lightbox.querySelector('.lightbox-next');

  let currentIndex = 0;
  const visiblePhotoItems = () => Array.from(galleryItems).filter(item => item.style.display !== 'none' && !item.classList.contains('empty-category-card') && item.querySelector('img'));

  function openLightbox(index) {
    const items = visiblePhotoItems();
    if (!items.length) return;
    if (index < 0) index = items.length - 1;
    if (index >= items.length) index = 0;
    currentIndex = index;

    const item = items[currentIndex];
    if (!item) return;
    const img = item.querySelector('img');
    if (!img) return;
    const title = item.querySelector('h4')?.textContent || '';
    const category = item.querySelector('p')?.textContent || '';

    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt || title;
    lightboxCaption.textContent = `${title} — ${category}`;
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  galleryItems.forEach((item) => {
    if (item.classList.contains('empty-category-card') || !item.querySelector('img')) return;
    item.addEventListener('click', () => {
      const items = visiblePhotoItems();
      const itemIndex = items.indexOf(item);
      if (itemIndex !== -1) {
        openLightbox(itemIndex);
      }
    });
  });

  closeBtn?.addEventListener('click', () => {
    lightbox.classList.remove('active');
    document.body.style.overflow = 'auto';
  });

  prevBtn?.addEventListener('click', () => openLightbox(currentIndex - 1));
  nextBtn?.addEventListener('click', () => openLightbox(currentIndex + 1));

  // Close on outer click or Escape key
  lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) {
      lightbox.classList.remove('active');
      document.body.style.overflow = 'auto';
    }
  });

  document.addEventListener('keydown', (e) => {
    if (!lightbox.classList.contains('active')) return;
    if (e.key === 'Escape') {
      lightbox.classList.remove('active');
      document.body.style.overflow = 'auto';
    } else if (e.key === 'ArrowLeft') {
      openLightbox(currentIndex - 1);
    } else if (e.key === 'ArrowRight') {
      openLightbox(currentIndex + 1);
    }
  });
}

/* --------------------------------------------------------------------------
   5. Form Validation & Direct Backend Submission
   -------------------------------------------------------------------------- */
function initFormValidation() {
  const contactForm = document.getElementById('contact-form');
  const inquiryForm = document.getElementById('inquiry-form');

  // Handle Admission Inquiry Form -> Open in Gmail Compose
  if (inquiryForm) {
    inquiryForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const studentName = document.getElementById('student_name')?.value.trim();
      const parentName = document.getElementById('parent_name')?.value.trim();
      const phoneNumber = document.getElementById('phone_number')?.value.trim();
      const emailAddress = document.getElementById('email_address')?.value.trim();
      const classApplying = document.getElementById('class_applying')?.value.trim();
      const enquiryMessage = document.getElementById('enquiry_message')?.value.trim() || 'N/A';

      // Validate required fields
      if (!studentName || !parentName || !phoneNumber || !emailAddress || !classApplying) {
        showToast('Please fill out all required fields marked with *.', 'error');
        return;
      }

      const bodyText = `JNPHS NEW ADMISSION ENQUIRY\n\nStudent Name: ${studentName}\nParent/Guardian Name: ${parentName}\nPhone: ${phoneNumber}\nEmail: ${emailAddress}\nClass/Grade: ${classApplying}\nMessage/Enquiry: ${enquiryMessage}`;

      const subjectText = 'JNPHS New Admission Enquiry';

      const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=jnpschool@gmail.com&su=${encodeURIComponent(subjectText)}&body=${encodeURIComponent(bodyText)}`;

      // Open Gmail compose in a new tab
      window.open(gmailUrl, '_blank');

      // Feedback message to user
      showToast('Your enquiry has been prepared in Gmail. Please review and press Send.');
    });
  }

  // Handle General Contact Form
  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const contactName = document.getElementById('contact_name')?.value.trim();
      const contactEmail = document.getElementById('contact_email')?.value.trim();
      const contactSubject = document.getElementById('contact_subject')?.value.trim();
      const contactMessage = document.getElementById('contact_message')?.value.trim();

      if (!contactName || !contactEmail || !contactSubject || !contactMessage) {
        showToast('Please fill out all required fields marked with *.', 'error');
        return;
      }

      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const originalBtnHtml = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
      }

      const payload = {
        contact_name: contactName,
        contact_email: contactEmail,
        contact_subject: contactSubject,
        contact_message: contactMessage,
        submission_time: new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'full', timeStyle: 'medium' })
      };

      try {
        const response = await fetch('/api/contact', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok && data.success === true) {
          contactForm.reset();
          showToast('Thank you. Your message has been sent successfully.', 'success');
        } else {
          console.error('Contact submission error:', data.error || response.statusText);
          showToast('Unable to send your message right now. Please try again or contact the school directly.', 'error');
        }
      } catch (err) {
        console.error('Contact network error:', err);
        showToast('Unable to send your message right now. Please try again or contact the school directly.', 'error');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnHtml;
        }
      }
    });
  }
}

function showToast(message, type = 'info') {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  const icon = type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle';
  toast.innerHTML = `<i class="fas ${icon}" style="color: var(--gold); font-size: 1.3rem;"></i> <span>${message}</span>`;
  
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 4500);
}

/* --------------------------------------------------------------------------
   6. Back to Top Button
   -------------------------------------------------------------------------- */
function initBackToTop() {
  const backBtn = document.getElementById('back-to-top');
  if (!backBtn) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
      backBtn.classList.add('visible');
    } else {
      backBtn.classList.remove('visible');
    }
  });

  backBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* --------------------------------------------------------------------------
   7. Accordions for FAQ
   -------------------------------------------------------------------------- */
function initAccordions() {
  const accordionHeaders = document.querySelectorAll('.accordion-header');

  accordionHeaders.forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const content = item.querySelector('.accordion-content');
      const isOpen = item.classList.contains('active');

      // Close all other accordions
      document.querySelectorAll('.accordion-item').forEach(i => {
        i.classList.remove('active');
        const c = i.querySelector('.accordion-content');
        if (c) c.style.maxHeight = null;
      });

      if (!isOpen) {
        item.classList.add('active');
        content.style.maxHeight = content.scrollHeight + 'px';
      }
    });
  });
}
