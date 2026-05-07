/**
 * cv_preview.js  — v2.0
 * ─────────────────────────────────────────────────────────────────────────────
 * Live preview engine shared across ALL 5 steps.
 *
 * Step 1 : personal info  → name, role, email, phone, city/country, links,
 *           summary, photo, initials, colors, font, template switch
 * Step 2 : education      → degree, institution, dates (live rebuild)
 * Step 3 : experience     → position, company, location, dates (live rebuild)
 * Step 4 : skills, langs  → skill pills, language level badges
 * Step 5 : review         → read-only, no live updates needed
 *
 * Works alongside field_styler.js for per-field typography.
 * ─────────────────────────────────────────────────────────────────────────────
 */
(function() {
    'use strict';

    const preview = document.getElementById('cv-preview-panel');
    if (!preview) return;

    /* ═══════════════════════════════════════════════════════════
       UTILITY HELPERS
    ══════════════════════════════════════════════════════════════ */

    function bindText(inputId, targetId, fallback) {
        const input = document.getElementById(inputId);
        const target = document.getElementById(targetId);
        if (!input || !target) return;
        input.addEventListener('input', function() {
            target.textContent = this.value.trim() || fallback || '';
        });
    }

    function bindVisibility(inputId, wrapperId) {
        const input = document.getElementById(inputId);
        const wrapper = document.getElementById(wrapperId);
        if (!input || !wrapper) return;
        const toggle = () => { wrapper.style.display = input.value.trim() ? '' : 'none'; };
        toggle();
        input.addEventListener('input', toggle);
    }

    function bindCSSVar(inputId, cssVar, labelId) {
        const input = document.getElementById(inputId);
        if (!input) return;
        preview.style.setProperty(cssVar, input.value);
        input.addEventListener('input', function() {
            preview.style.setProperty(cssVar, this.value);
            if (labelId) {
                const lbl = document.getElementById(labelId);
                if (lbl) lbl.textContent = this.value;
            }
        });
    }

    function fmtDate(val) {
        if (!val) return '';
        const d = new Date(val + 'T00:00:00');
        if (isNaN(d)) return val;
        return d.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
    }

    function esc(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function loadGFont(family) {
        if (!family || ['Georgia', 'Courier New'].includes(family)) return;
        const id = 'gf-' + family.replace(/\s/g, '-');
        if (document.getElementById(id)) return;
        const link = document.createElement('link');
        link.id = id;
        link.rel = 'stylesheet';
        link.href = 'https://fonts.googleapis.com/css2?family=' + encodeURIComponent(family) + ':wght@300;400;500;600;700;800;900&display=swap';
        document.head.appendChild(link);
    }

    /* ═══════════════════════════════════════════════════════════
       STEP 1 — PERSONAL INFO
    ══════════════════════════════════════════════════════════════ */

    // Name + initials
    const nameInput = document.getElementById('id_full_name');
    const prevInitials = document.getElementById('prev-initials');

    if (nameInput) {
        nameInput.addEventListener('input', function() {
            const val = this.value.trim();
            const parts = val.split(/\s+/).filter(Boolean);
            const el = document.getElementById('prev-name');
            if (el) el.textContent = val || 'Your Name';
            if (prevInitials) {
                prevInitials.textContent = parts.length >= 2 ?
                    parts[0][0].toUpperCase() + parts[parts.length - 1][0].toUpperCase() :
                    (parts[0] ? parts[0][0].toUpperCase() : '?');
            }
        });
    }

    // Job title
    bindText('id_job_title', 'prev-role', '');
    bindVisibility('id_job_title', 'wrap-role');

    // Email (sidebar + classic row)
    const emailIn = document.getElementById('id_email');
    if (emailIn) {
        emailIn.addEventListener('input', function() {
            ['prev-email', 'prev-email-classic'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = this.value.trim();
            });
            const w = document.getElementById('wrap-email');
            if (w) w.style.display = this.value.trim() ? '' : 'none';
        });
    }

    // Phone (sidebar + classic row)
    const phoneIn = document.getElementById('id_phone');
    if (phoneIn) {
        phoneIn.addEventListener('input', function() {
            ['prev-phone', 'prev-phone-classic'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = this.value.trim();
            });
            const w = document.getElementById('wrap-phone');
            if (w) w.style.display = this.value.trim() ? '' : 'none';
        });
    }

    // City (sidebar + classic row)
    const cityIn = document.getElementById('id_city');
    if (cityIn) {
        cityIn.addEventListener('input', function() {
            ['prev-city', 'prev-city-classic'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = this.value.trim();
            });
            const w = document.getElementById('wrap-city');
            if (w) w.style.display = this.value.trim() ? '' : 'none';
        });
    }

    // Country (appended to city in sidebar)
    const countryIn = document.getElementById('id_country');
    const countrySpan = document.getElementById('prev-country');
    if (countryIn && countrySpan) {
        countryIn.addEventListener('input', function() {
            countrySpan.textContent = this.value.trim() ? ', ' + this.value.trim() : '';
        });
    }

    // Summary
    bindText('id_summary', 'prev-summary', '');
    bindVisibility('id_summary', 'wrap-summary');

    // Social links
    ['linkedin', 'github', 'website'].forEach(function(field) {
        const el = document.getElementById('id_' + field);
        const span = document.getElementById('prev-' + field);
        const wrap = document.getElementById('wrap-' + field);
        if (!el) return;
        el.addEventListener('input', function() {
            if (span) span.textContent = this.value.trim();
            if (wrap) wrap.style.display = this.value.trim() ? '' : 'none';
        });
    });

    // Colours
    bindCSSVar('id_primary_color', '--cv-primary', 'lbl-primary-color');
    bindCSSVar('id_secondary_color', '--cv-secondary', 'lbl-secondary-color');

    // Global font family
    const fontSelect = document.getElementById('id_font_family');
    if (fontSelect) {
        const applyFont = function() {
            preview.style.fontFamily = fontSelect.value ? ("'" + fontSelect.value + "', sans-serif") : '';
            loadGFont(fontSelect.value);
        };
        applyFont();
        fontSelect.addEventListener('change', applyFont);
    }

    // Global font size
    const fontSizeSelect = document.getElementById('id_font_size');
    if (fontSizeSelect) {
        const sizeMap = { small: '11px', medium: '12.5px', large: '14px' };
        const applySize = function() { preview.style.fontSize = sizeMap[fontSizeSelect.value] || '12.5px'; };
        applySize();
        fontSizeSelect.addEventListener('change', applySize);
    }

    // Template switcher
    const templateSelect = document.getElementById('id_template');
    if (templateSelect) {
        const applyTemplate = function() {
            preview.classList.remove('tmpl-modern', 'tmpl-classic', 'tmpl-minimal');
            preview.classList.add('tmpl-' + templateSelect.value);
        };
        applyTemplate();
        templateSelect.addEventListener('change', applyTemplate);
    }

    // Profile photo
    const photoInput = document.getElementById('id_profile_photo');
    const prevPhoto = document.getElementById('prev-photo');
    if (photoInput && prevPhoto) {
        photoInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function(e) {
                prevPhoto.src = e.target.result;
                prevPhoto.style.display = 'block';
                if (prevInitials) prevInitials.style.display = 'none';
            };
            reader.readAsDataURL(file);
        });
    }

    /* ═══════════════════════════════════════════════════════════
       STEP 2 — EDUCATION
    ══════════════════════════════════════════════════════════════ */

    function refreshEduPreview() {
        var block = document.getElementById('prev-edu-block');
        if (!block) return;

        var entries = document.querySelectorAll('#education-entries .formset-entry');
        var html = '<div class="prev-section-label">Education</div>';
        var count = 0;

        entries.forEach(function(entry) {
            var delCb = entry.querySelector('input[name$="-DELETE"]');
            if (delCb && delCb.checked) return;

            var degreeEl = entry.querySelector('select[name$="-degree"]');
            var fieldEl = entry.querySelector('input[name$="-field_of_study"]');
            var instEl = entry.querySelector('input[name$="-institution"]');
            var locEl = entry.querySelector('input[name$="-institution_location"]');
            var startEl = entry.querySelector('input[name$="-start_date"]');
            var endEl = entry.querySelector('input[name$="-end_date"]');
            var currEl = entry.querySelector('input[name$="-is_current"]');

            var degree = degreeEl ? (degreeEl.options[degreeEl.selectedIndex] ? degreeEl.options[degreeEl.selectedIndex].text : '') : '';
            var field = fieldEl ? fieldEl.value.trim() : '';
            var inst = instEl ? instEl.value.trim() : '';
            var loc = locEl ? locEl.value.trim() : '';
            var start = startEl ? startEl.value : '';
            var end = endEl ? endEl.value : '';
            var isCurr = currEl ? currEl.checked : false;

            // Skip empty rows & placeholder "-------" degree
            if (!inst && (!degree || degree === '---------')) return;
            count++;

            var titleLine = degree && degree !== '---------' ? degree : '';
            if (field) titleLine += (titleLine ? ' — ' : '') + field;

            var subLine = esc(inst);
            if (loc) subLine += ' · ' + esc(loc);

            var dateLine = '';
            if (start) dateLine = fmtDate(start) + ' — ' + (isCurr ? 'Present' : (end ? fmtDate(end) : '…'));

            html += '<div class="prev-data-row">' +
                '<div class="prev-data-title">' + esc(titleLine) + '</div>' +
                '<div class="prev-data-sub">' + subLine + '</div>' +
                (dateLine ? '<div class="prev-data-date">' + esc(dateLine) + '</div>' : '') +
                '</div>';
        });

        if (count === 0) {
            html += '<div class="prev-placeholder-line" style="width:70%"></div>' +
                '<div class="prev-placeholder-line" style="width:85%"></div>';
        }
        block.innerHTML = html;
    }

    var eduContainer = document.getElementById('education-entries');
    if (eduContainer) {
        eduContainer.addEventListener('input', refreshEduPreview);
        eduContainer.addEventListener('change', refreshEduPreview);
        refreshEduPreview();
    }
    window.refreshEduPreview = refreshEduPreview;

    /* ═══════════════════════════════════════════════════════════
       STEP 3 — EXPERIENCE
    ══════════════════════════════════════════════════════════════ */

    function refreshExpPreview() {
        var block = document.getElementById('prev-exp-block');
        if (!block) return;

        var entries = document.querySelectorAll('#experience-entries .formset-entry');
        var html = '<div class="prev-section-label">Experience</div>';
        var count = 0;

        entries.forEach(function(entry) {
            var delCb = entry.querySelector('input[name$="-DELETE"]');
            if (delCb && delCb.checked) return;

            var posEl = entry.querySelector('input[name$="-position"]');
            var coEl = entry.querySelector('input[name$="-company"]');
            var locEl = entry.querySelector('input[name$="-company_location"]');
            var typeEl = entry.querySelector('select[name$="-employment_type"]');
            var startEl = entry.querySelector('input[name$="-start_date"]');
            var endEl = entry.querySelector('input[name$="-end_date"]');
            var currEl = entry.querySelector('input[name$="-is_current"]');

            var pos = posEl ? posEl.value.trim() : '';
            var co = coEl ? coEl.value.trim() : '';
            var loc = locEl ? locEl.value.trim() : '';
            var start = startEl ? startEl.value : '';
            var end = endEl ? endEl.value : '';
            var isCurr = currEl ? currEl.checked : false;
            var type = typeEl && typeEl.selectedIndex >= 0 ? typeEl.options[typeEl.selectedIndex].text : '';

            if (!pos && !co) return;
            count++;

            var subLine = esc(co);
            if (loc) subLine += ' · ' + esc(loc);
            if (type && type !== '---------') subLine += ' <span style="opacity:.6;font-size:.85em;">(' + esc(type) + ')</span>';

            var dateLine = '';
            if (start) dateLine = fmtDate(start) + ' — ' + (isCurr ? 'Present' : (end ? fmtDate(end) : '…'));

            html += '<div class="prev-data-row">' +
                '<div class="prev-data-title">' + esc(pos) + '</div>' +
                '<div class="prev-data-sub">' + subLine + '</div>' +
                (dateLine ? '<div class="prev-data-date">' + esc(dateLine) + '</div>' : '') +
                '</div>';
        });

        if (count === 0) {
            html += '<div class="prev-placeholder-line" style="width:60%"></div>' +
                '<div class="prev-placeholder-line" style="width:90%"></div>';
        }
        block.innerHTML = html;
    }

    var expContainer = document.getElementById('experience-entries');
    if (expContainer) {
        expContainer.addEventListener('input', refreshExpPreview);
        expContainer.addEventListener('change', refreshExpPreview);
        refreshExpPreview();
    }
    window.refreshExpPreview = refreshExpPreview;

    /* ═══════════════════════════════════════════════════════════
       STEP 4 — SKILLS, LANGUAGES, INTERESTS
    ══════════════════════════════════════════════════════════════ */

    function refreshSkillPreview() {
        var block = document.getElementById('prev-skills-block');
        if (!block) return;
        var entries = document.querySelectorAll('#skill-entries .formset-entry');
        var html = '<div class="prev-section-label">Skills</div>';
        var count = 0;
        entries.forEach(function(entry) {
            var delCb = entry.querySelector('input[name$="-DELETE"]');
            if (delCb && delCb.checked) return;
            var nameEl = entry.querySelector('input[name$="-name"]');
            var val = nameEl ? nameEl.value.trim() : '';
            if (!val) return;
            count++;
            html += '<div class="prev-skill-item">' + esc(val) + '</div>';
        });
        if (count === 0) {
            html += '<div class="prev-placeholder-line" style="width:80%"></div>' +
                '<div class="prev-placeholder-line" style="width:65%"></div>' +
                '<div class="prev-placeholder-line" style="width:75%"></div>';
        }
        block.innerHTML = html;
    }

    function refreshLangPreview() {
        var block = document.getElementById('prev-langs-block');
        if (!block) return;
        var entries = document.querySelectorAll('#language-entries .formset-entry');
        var html = '';
        var count = 0;
        entries.forEach(function(entry) {
            var delCb = entry.querySelector('input[name$="-DELETE"]');
            if (delCb && delCb.checked) return;
            var nameEl = entry.querySelector('input[name$="-name"]');
            var lvlEl = entry.querySelector('select[name$="-level"]');
            var val = nameEl ? nameEl.value.trim() : '';
            var lvl = lvlEl && lvlEl.selectedIndex >= 0 ? lvlEl.options[lvlEl.selectedIndex].text : '';
            if (!val) return;
            if (count === 0) html += '<div class="prev-section-label">Languages</div>';
            count++;
            html += '<div class="prev-skill-item">' + esc(val) +
                ' <span style="opacity:.55;font-size:.75em;">' + esc(lvl) + '</span></div>';
        });
        block.innerHTML = html;
    }

    function refreshInterestPreview() {
        var block = document.getElementById('prev-interests-block');
        if (!block) return;
        var inputs = document.querySelectorAll('#interest-entries input[name$="-name"]');
        var parts = [];
        inputs.forEach(function(input) {
            var val = input.value.trim();
            if (val) parts.push(esc(val));
        });
        if (parts.length) {
            block.innerHTML = '<div class="prev-section-label">Interests</div>' +
                parts.map(function(p) { return '<div class="prev-skill-item">' + p + '</div>'; }).join('');
        } else {
            block.innerHTML = '';
        }
    }

    var skillContainer = document.getElementById('skill-entries');
    var langContainer = document.getElementById('language-entries');
    var interestContainer = document.getElementById('interest-entries');

    if (skillContainer) {
        skillContainer.addEventListener('input', refreshSkillPreview);
        skillContainer.addEventListener('change', refreshSkillPreview);
        refreshSkillPreview();
    }
    if (langContainer) {
        langContainer.addEventListener('input', refreshLangPreview);
        langContainer.addEventListener('change', refreshLangPreview);
        refreshLangPreview();
    }
    if (interestContainer) {
        interestContainer.addEventListener('input', refreshInterestPreview);
        interestContainer.addEventListener('change', refreshInterestPreview);
        refreshInterestPreview();
    }

    window.refreshSkillPreview = refreshSkillPreview;
    window.refreshLangPreview = refreshLangPreview;
    window.refreshInterestPreview = refreshInterestPreview;

    /* ═══════════════════════════════════════════════════════════
       MUTATION OBSERVER — re-fire refresh after "Add" inserts rows
    ══════════════════════════════════════════════════════════════ */
    var _obs = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
                if (node.nodeType !== 1) return;
                var ids = ['education-entries', 'experience-entries', 'skill-entries', 'language-entries', 'interest-entries'];
                ids.forEach(function(cid) {
                    var c = document.getElementById(cid);
                    if (!c || !c.contains(node)) return;
                    if (cid === 'education-entries') refreshEduPreview();
                    if (cid === 'experience-entries') refreshExpPreview();
                    if (cid === 'skill-entries') refreshSkillPreview();
                    if (cid === 'language-entries') refreshLangPreview();
                    if (cid === 'interest-entries') refreshInterestPreview();
                });
            });
        });
    });
    _obs.observe(document.body, { childList: true, subtree: true });

})();