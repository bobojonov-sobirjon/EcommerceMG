/**
 * Jazzmin horizontal tabs + Bootstrap 5.
 * Jazzmin change_form.js uses jQuery .tab('show') (Bootstrap 4) — it does not work on BS5.
 */
(function () {
    'use strict';

    function findTabLink(tabList, href) {
        if (!tabList || !href) {
            return null;
        }
        return Array.prototype.find.call(
            tabList.querySelectorAll('a.nav-link'),
            function (link) {
                return link.getAttribute('href') === href;
            },
        );
    }

    function showTab(trigger) {
        if (!trigger) {
            return false;
        }

        var tabList = document.getElementById('jazzy-tabs');
        if (!tabList) {
            return false;
        }

        var href = trigger.getAttribute('href');
        if (!href || href.charAt(0) !== '#') {
            return false;
        }

        var pane = document.getElementById(href.slice(1));
        if (!pane) {
            return false;
        }

        tabList.querySelectorAll('.nav-link').forEach(function (link) {
            link.classList.remove('active');
            link.setAttribute('aria-selected', 'false');
        });
        trigger.classList.add('active');
        trigger.setAttribute('aria-selected', 'true');

        var tabContent = pane.closest('.tab-content');
        if (tabContent) {
            tabContent.querySelectorAll('.tab-pane').forEach(function (item) {
                item.classList.remove('show', 'active');
            });
        }
        pane.classList.add('show', 'active');

        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', href);
        }

        window.dispatchEvent(new Event('resize'));
        return true;
    }

    function bindAdminTabs() {
        var tabList = document.getElementById('jazzy-tabs');
        if (!tabList || tabList.dataset.emgTabsBound === '1') {
            return;
        }
        tabList.dataset.emgTabsBound = '1';

        tabList.querySelectorAll('a.nav-link').forEach(function (link) {
            link.removeAttribute('data-bs-toggle');
            link.addEventListener('click', function (event) {
                event.preventDefault();
                showTab(link);
            });
        });

        var hash = window.location.hash;
        if (hash) {
            showTab(findTabLink(tabList, hash));
        }
    }

    function boot() {
        bindAdminTabs();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }

    // Jazzmin change_form.js attaches broken handlers on jQuery ready — bind after it.
    if (window.jQuery) {
        window.jQuery(function () {
            window.setTimeout(boot, 0);
        });
    }
})();
