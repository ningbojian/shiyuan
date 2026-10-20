(function () {
    "use strict";

    var root = document.documentElement;
    var storageKey = "shiyuan-theme";
    var media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

    function storedTheme() {
        try {
            return window.localStorage.getItem(storageKey);
        } catch (error) {
            return null;
        }
    }

    function preferredTheme() {
        var saved = storedTheme();
        if (saved === "paper" || saved === "night") {
            return saved;
        }
        return media && media.matches ? "night" : "paper";
    }

    function applyTheme(theme, persist) {
        root.setAttribute("data-theme", theme);
        if (persist) {
            try {
                window.localStorage.setItem(storageKey, theme);
            } catch (error) {
                /* Storage may be unavailable in private modes. */
            }
        }
        document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
            var isNight = theme === "night";
            button.setAttribute("aria-pressed", isNight ? "true" : "false");
            button.setAttribute("aria-label", isNight ? "切换到日间模式" : "切换到夜间模式");
            var label = button.querySelector("[data-theme-label]");
            if (label) {
                label.textContent = isNight ? "日间" : "夜间";
            }
            var icon = button.querySelector("[data-theme-icon]");
            if (icon) {
                icon.textContent = isNight ? "☀" : "☾";
            }
        });
        window.dispatchEvent(new CustomEvent("themechange", { detail: { theme: theme } }));
    }

    applyTheme(preferredTheme(), false);

    document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
        button.addEventListener("click", function () {
            var next = root.getAttribute("data-theme") === "night" ? "paper" : "night";
            applyTheme(next, true);
        });
    });

    document.querySelectorAll("[data-print]").forEach(function (button) {
        button.addEventListener("click", function () {
            window.print();
        });
    });

    document.querySelectorAll("[data-copy-link]").forEach(function (button) {
        button.addEventListener("click", function () {
            var original = button.textContent;
            function done(message) {
                button.textContent = message;
                window.setTimeout(function () {
                    button.textContent = original;
                }, 1800);
            }
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(window.location.href).then(function () {
                    done("已复制");
                }).catch(function () {
                    done("复制失败");
                });
            } else {
                done("请复制地址栏");
            }
        });
    });

    var navToggle = document.querySelector("[data-nav-toggle]");
    var siteNav = document.querySelector("#site-nav");
    if (navToggle && siteNav) {
        navToggle.addEventListener("click", function () {
            var open = navToggle.getAttribute("aria-expanded") === "true";
            navToggle.setAttribute("aria-expanded", open ? "false" : "true");
            siteNav.classList.toggle("is-open", !open);
        });
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && siteNav.classList.contains("is-open")) {
                siteNav.classList.remove("is-open");
                navToggle.setAttribute("aria-expanded", "false");
                navToggle.focus();
            }
        });
    }
})();
