(function() {
    'use strict';

    const THEME_KEY = 'ai-evaluation-theme';
    const LIGHT_THEME = 'light-theme';
    const DARK_THEME = 'dark-theme';
    const TRANSITION_CLASS = 'theme-transition';
    const TRANSITION_DURATION = 300;

    function getCurrentTheme() {
        return localStorage.getItem(THEME_KEY) || DARK_THEME;
    }

    function setTheme(theme) {
        const root = document.documentElement;
        const body = document.body;
        
        body.classList.add(TRANSITION_CLASS);
        
        root.classList.remove(LIGHT_THEME, DARK_THEME);
        
        if (theme === LIGHT_THEME) {
            root.classList.add(LIGHT_THEME);
        }
        
        localStorage.setItem(THEME_KEY, theme);
        
        updateThemeSwitcher(theme);
        
        setTimeout(() => {
            body.classList.remove(TRANSITION_CLASS);
        }, TRANSITION_DURATION);
        
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    function updateThemeSwitcher(theme) {
        const switcher = document.querySelector('.theme-switcher');
        if (!switcher) return;
        
        const sunIcon = switcher.querySelector('.theme-icon.sun');
        const moonIcon = switcher.querySelector('.theme-icon.moon');
        const themeText = switcher.querySelector('.theme-text');
        
        if (theme === LIGHT_THEME) {
            sunIcon.style.display = 'flex';
            moonIcon.style.display = 'none';
            if (themeText) themeText.textContent = '浅色模式';
        } else {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'flex';
            if (themeText) themeText.textContent = '深色模式';
        }
    }

    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === LIGHT_THEME ? DARK_THEME : LIGHT_THEME;
        setTheme(newTheme);
    }

    function createThemeSwitcher() {
        const switcher = document.createElement('div');
        switcher.className = 'theme-switcher';
        switcher.setAttribute('role', 'button');
        switcher.setAttribute('aria-label', '切换主题');
        switcher.setAttribute('tabindex', '0');
        
        switcher.innerHTML = `
            <div class="theme-icon sun">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
            </div>
            <div class="theme-icon moon">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
            </div>
            <span class="theme-text">深色模式</span>
        `;
        
        switcher.addEventListener('click', toggleTheme);
        
        switcher.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleTheme();
            }
        });
        
        document.body.appendChild(switcher);
    }

    function applySavedTheme() {
        const savedTheme = getCurrentTheme();
        const root = document.documentElement;
        
        if (savedTheme === LIGHT_THEME) {
            root.classList.add(LIGHT_THEME);
        }
    }

    function watchSystemTheme() {
        if (!window.matchMedia) return;
        
        const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
        
        if (!localStorage.getItem(THEME_KEY)) {
            const systemTheme = mediaQuery.matches ? LIGHT_THEME : DARK_THEME;
            setTheme(systemTheme);
        }
        
        mediaQuery.addEventListener('change', (e) => {
            if (!localStorage.getItem(THEME_KEY)) {
                const systemTheme = e.matches ? LIGHT_THEME : DARK_THEME;
                setTheme(systemTheme);
            }
        });
    }

    function getEChartsTheme() {
        const currentTheme = getCurrentTheme();
        
        if (currentTheme === LIGHT_THEME) {
            return {
                color: [
                    '#0ea5e9',
                    '#8b5cf6',
                    '#10b981',
                    '#f59e0b',
                    '#f43f5e',
                    '#3b82f6',
                    '#a855f7',
                    '#14b8a6',
                    '#eab308',
                    '#ec4899'
                ],
                backgroundColor: 'transparent',
                textStyle: {
                    color: '#1e293b'
                },
                title: {
                    textStyle: {
                        color: '#0f172a'
                    }
                },
                legend: {
                    textStyle: {
                        color: '#1e293b'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    borderColor: 'rgba(203, 213, 225, 0.7)',
                    textStyle: {
                        color: '#0f172a'
                    }
                },
                grid: {
                    borderColor: 'rgba(203, 213, 225, 0.3)'
                },
                categoryAxis: {
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(203, 213, 225, 0.7)'
                        }
                    },
                    axisTick: {
                        lineStyle: {
                            color: 'rgba(203, 213, 225, 0.7)'
                        }
                    },
                    axisLabel: {
                        color: '#1e293b'
                    },
                    splitLine: {
                        lineStyle: {
                            color: ['rgba(203, 213, 225, 0.3)']
                        }
                    }
                },
                valueAxis: {
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(203, 213, 225, 0.7)'
                        }
                    },
                    axisTick: {
                        lineStyle: {
                            color: 'rgba(203, 213, 225, 0.7)'
                        }
                    },
                    axisLabel: {
                        color: '#475569'
                    },
                    splitLine: {
                        lineStyle: {
                            color: ['rgba(203, 213, 225, 0.3)']
                        }
                    }
                }
            };
        } else {
            return {
                color: [
                    '#00d9ff',
                    '#7c3aed',
                    '#10b981',
                    '#f59e0b',
                    '#ec4899',
                    '#3b82f6',
                    '#8b5cf6',
                    '#06b6d4',
                    '#84cc16',
                    '#f43f5e'
                ],
                backgroundColor: 'transparent',
                textStyle: {
                    color: '#e2e8f0'
                },
                title: {
                    textStyle: {
                        color: '#f8fafc'
                    }
                },
                legend: {
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 31, 58, 0.95)',
                    borderColor: 'rgba(148, 163, 184, 0.2)',
                    textStyle: {
                        color: '#ffffff'
                    }
                },
                grid: {
                    borderColor: 'rgba(148, 163, 184, 0.1)'
                },
                categoryAxis: {
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(148, 163, 184, 0.2)'
                        }
                    },
                    axisTick: {
                        lineStyle: {
                            color: 'rgba(148, 163, 184, 0.2)'
                        }
                    },
                    axisLabel: {
                        color: '#cbd5e1'
                    },
                    splitLine: {
                        lineStyle: {
                            color: ['rgba(148, 163, 184, 0.1)']
                        }
                    }
                },
                valueAxis: {
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(148, 163, 184, 0.2)'
                        }
                    },
                    axisTick: {
                        lineStyle: {
                            color: 'rgba(148, 163, 184, 0.2)'
                        }
                    },
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    splitLine: {
                        lineStyle: {
                            color: ['rgba(148, 163, 184, 0.1)']
                        }
                    }
                }
            };
        }
    }

    function addSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    function init() {
        applySavedTheme();
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', onDOMReady);
        } else {
            onDOMReady();
        }
    }

    function onDOMReady() {
        createThemeSwitcher();
        
        const savedTheme = getCurrentTheme();
        updateThemeSwitcher(savedTheme);
        
        watchSystemTheme();
        
        addSmoothScroll();
    }

    window.ThemeSwitcher = {
        toggle: toggleTheme,
        setTheme: setTheme,
        getCurrentTheme: getCurrentTheme,
        getEChartsTheme: getEChartsTheme
    };

    init();
})();
