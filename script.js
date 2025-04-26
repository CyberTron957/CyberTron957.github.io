document.addEventListener('DOMContentLoaded', () => {
    // Navigation toggle for mobile
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('nav ul');

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
    }

    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a, .hero-buttons a').forEach(anchor => {
        anchor.addEventListener('click', function (event) {
            const targetId = this.getAttribute('href');
            
            if (targetId.startsWith('#') && targetId.length > 1) {
                event.preventDefault();
                const targetSection = document.getElementById(targetId.substring(1));
                
                if (targetSection) {
                    const headerHeight = document.querySelector('header').offsetHeight;
                    const targetPosition = targetSection.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                    
                    // Close mobile menu if open
                    if (navLinks.classList.contains('active')) {
                        navLinks.classList.remove('active');
                        menuToggle.classList.remove('active');
                    }
                }
            }
        });
    });

    // Dark mode toggle
    setupDarkMode();
    
    // Accordion functionality
    setupAccordion();
    
    // Animate skill bars on scroll
    animateSkillBars();
});

function setupDarkMode() {
    // Create dark mode toggle if it doesn't exist
    let darkModeToggle = document.querySelector('.dark-mode-toggle');
    
    if (!darkModeToggle) {
        darkModeToggle = document.createElement('button');
        darkModeToggle.classList.add('dark-mode-toggle');
        document.body.appendChild(darkModeToggle);
    }
    
    // Set initial state based on localStorage or user preference
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const storedDarkMode = localStorage.getItem('darkMode');
    
    if (storedDarkMode === 'enabled' || (storedDarkMode === null && prefersDarkMode)) {
        document.body.classList.add('dark-mode');
        darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        darkModeToggle.setAttribute('aria-label', 'Switch to Light Mode');
    } else {
        darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        darkModeToggle.setAttribute('aria-label', 'Switch to Dark Mode');
    }

    // Toggle dark mode on click
    darkModeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            darkModeToggle.setAttribute('aria-label', 'Switch to Light Mode');
        } else {
            localStorage.setItem('darkMode', 'disabled');
            darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            darkModeToggle.setAttribute('aria-label', 'Switch to Dark Mode');
        }
    });
}

function setupAccordion() {
    document.querySelectorAll('.accordion-item').forEach(item => {
        const header = item.querySelector('.accordion-header');
        
        if (header) {
            header.addEventListener('click', () => {
                const openItem = document.querySelector('.accordion-item.open');
                toggleAccordionItem(item);

                if (openItem && openItem !== item) {
                    toggleAccordionItem(openItem);
                }
            });
        }
    });
}

function toggleAccordionItem(item) {
    const content = item.querySelector('.accordion-content');
    
    if (!content) return;

    if (item.classList.contains('open')) {
        content.style.height = '0';
        item.classList.remove('open');
    } else {
        content.style.height = content.scrollHeight + 'px';
        item.classList.add('open');
    }
}

function animateSkillBars() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const skillLevels = entry.target.querySelectorAll('.skill-level');
                skillLevels.forEach(level => {
                    setTimeout(() => {
                        level.style.width = level.getAttribute('data-level');
                    }, 200);
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });

    const skillsSection = document.querySelector('.skills');
    if (skillsSection) {
        observer.observe(skillsSection);
    }
}

// Animate elements on scroll
const animateOnScroll = () => {
    const elements = document.querySelectorAll('.about-text, .skills, .project-item, .testimonial-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    elements.forEach(element => {
        element.classList.add('animate-element');
        observer.observe(element);
    });
};

// Call animate on scroll when DOM is loaded
document.addEventListener('DOMContentLoaded', (event) => {
    animateOnScroll();
});
