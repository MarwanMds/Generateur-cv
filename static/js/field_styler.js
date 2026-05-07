/**
 * field_styler.js
 * ─────────────────────────────────────────────────────────────────
 * Per-field typography picker for Step 1.
 *
 * Responsibilities:
 *  1. Toggle popover open/close via the ✎ button next to each field.
 *  2. Read & write a shared `fieldStyles` object  { fieldKey: { prop: value } }.
 *  3. Apply styles to:
 *       a) The actual <input>/<textarea> (so user sees styled text while typing).
 *       b) The corresponding preview element in #cv-preview-panel.
 *  4. Persist fieldStyles into the hidden #id_field_styles input as JSON.
 *  5. Restore saved styles on page load (from window.FIELD_STYLES).
 *  6. Load required Google Fonts dynamically.
 * ─────────────────────────────────────────────────────────────────
 */

(function () {
  'use strict';

  /* ═══════════════════════ CONFIG ═══════════════════════ */

  // Maps field_key → id of the corresponding preview element.
  const FIELD_TO_PREVIEW = {
    title:       null,          // not shown in preview
    full_name:   'prev-name',
    job_title:   'prev-role',
    email:       'prev-email',
    phone:       'prev-phone',
    address:     null,
    city:        'prev-city',
    country:     'prev-country',
    postal_code: null,
    linkedin:    'prev-linkedin',
    github:      'prev-github',
    website:     'prev-website',
    summary:     'prev-summary',
  };

  // CSS props applied per field
  const CSS_PROPS = ['font_family', 'font_size', 'font_weight', 'font_style', 'color'];

  /* ═══════════════════════ STATE ════════════════════════ */

  // Initialised from window.FIELD_STYLES (set by Django template)
  let fieldStyles = (window.FIELD_STYLES && typeof window.FIELD_STYLES === 'object')
    ? window.FIELD_STYLES
    : {};

  const hiddenInput = document.getElementById('id_field_styles');

  /* ═══════════════════════ HELPERS ══════════════════════ */

  function persistStyles() {
    if (hiddenInput) {
      hiddenInput.value = JSON.stringify(fieldStyles);
    }
  }

  function cssProp(prop) {
    // Convert snake_case to camelCase for element.style
    return prop.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
  }

  function cssAttr(prop, value) {
    // Return the CSS attribute string for inline CSS
    if (prop === 'font_family') return `'${value}', sans-serif`;
    return value;
  }

  function getOrCreate(fieldKey) {
    if (!fieldStyles[fieldKey]) fieldStyles[fieldKey] = {};
    return fieldStyles[fieldKey];
  }

  function loadGoogleFont(family) {
    if (!family || ['Georgia', 'Courier New'].includes(family)) return;
    const id = 'gf-' + family.replace(/\s/g, '-');
    if (document.getElementById(id)) return;
    const link = document.createElement('link');
    link.id   = id;
    link.rel  = 'stylesheet';
    link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family)}:wght@300;400;500;600;700;800;900&display=swap`;
    document.head.appendChild(link);
  }

  /* ─── Apply styles to the actual <input> / <textarea> ─── */
  function applyToInput(fieldKey, styles) {
    // Django puts id="id_<fieldname>" on every form field
    const el = document.getElementById(`id_${fieldKey}`);
    if (!el) return;
    CSS_PROPS.forEach(prop => {
      const val = styles[prop] || '';
      if (prop === 'font_family') {
        el.style.fontFamily = val ? `'${val}', sans-serif` : '';
      } else {
        el.style[cssProp(prop)] = val;
      }
    });
  }

  /* ─── Apply styles to the preview element ─── */
  function applyToPreview(fieldKey, styles) {
    const previewId = FIELD_TO_PREVIEW[fieldKey];
    if (!previewId) return;
    const el = document.getElementById(previewId);
    if (!el) return;
    CSS_PROPS.forEach(prop => {
      const val = styles[prop] || '';
      if (prop === 'font_family') {
        el.style.fontFamily = val ? `'${val}', sans-serif` : '';
      } else {
        el.style[cssProp(prop)] = val;
      }
    });
  }

  /* ─── Update the mini preview text inside the popover ─── */
  function updateMiniPreview(fieldKey) {
    const mini = document.getElementById(`styler-preview-${fieldKey}`);
    if (!mini) return;
    const styles = fieldStyles[fieldKey] || {};
    // Get current input value as sample text
    const inputEl = document.getElementById(`id_${fieldKey}`);
    const sampleText = (inputEl && inputEl.value.trim()) || `Sample — ${fieldKey}`;
    mini.textContent = sampleText;
    // Apply typography
    if (styles.font_family) { mini.style.fontFamily = `'${styles.font_family}', sans-serif`; }
    else                     { mini.style.fontFamily = ''; }
    if (styles.font_size)   { mini.style.fontSize   = styles.font_size; }
    else                    { mini.style.fontSize    = ''; }
    if (styles.font_weight) { mini.style.fontWeight  = styles.font_weight; }
    else                    { mini.style.fontWeight   = ''; }
    if (styles.font_style)  { mini.style.fontStyle   = styles.font_style; }
    else                    { mini.style.fontStyle    = ''; }
    if (styles.color)       { mini.style.color        = styles.color; }
    else                    { mini.style.color         = ''; }
  }

  /* ─── Apply ALL saved styles on load ─── */
  function restoreAllStyles() {
    Object.entries(fieldStyles).forEach(([fieldKey, styles]) => {
      applyToInput(fieldKey, styles);
      applyToPreview(fieldKey, styles);
      if (styles.font_family) loadGoogleFont(styles.font_family);
    });
  }

  /* ─── Sync popover controls to current state ─── */
  function syncPopoverControls(popover, fieldKey) {
    const styles = fieldStyles[fieldKey] || {};
    CSS_PROPS.forEach(prop => {
      const ctrl = popover.querySelector(`.styler-control[data-prop="${prop}"]`);
      if (!ctrl) return;
      ctrl.value = styles[prop] || '';
    });
    // Sync hex text input with color picker
    const colorPicker = popover.querySelector(`.styler-control[data-prop="color"]`);
    const hexInput = popover.querySelector(`.styler-color-hex`);
    if (colorPicker && hexInput) {
      hexInput.value = styles.color || '';
      colorPicker.value = styles.color || '#000000';
    }
    updateMiniPreview(fieldKey);
  }

  /* ═══════════════════════ POPOVER TOGGLE ═══════════════ */

  function openPopover(fieldKey) {
    // Close any currently open popovers
    document.querySelectorAll('.field-styler-popover.open').forEach(p => {
      if (p.dataset.field !== fieldKey) closePopover(p.dataset.field);
    });
    const pop = document.getElementById(`styler-${fieldKey}`);
    const btn = document.querySelector(`.field-style-toggle[data-field="${fieldKey}"]`);
    if (!pop) return;
    syncPopoverControls(pop, fieldKey);
    pop.classList.add('open');
    if (btn) btn.classList.add('active');
  }

  function closePopover(fieldKey) {
    const pop = document.getElementById(`styler-${fieldKey}`);
    const btn = document.querySelector(`.field-style-toggle[data-field="${fieldKey}"]`);
    if (pop) pop.classList.remove('open');
    if (btn) btn.classList.remove('active');
  }

  function togglePopover(fieldKey) {
    const pop = document.getElementById(`styler-${fieldKey}`);
    if (!pop) return;
    if (pop.classList.contains('open')) { closePopover(fieldKey); }
    else { openPopover(fieldKey); }
  }

  /* ═══════════════════════ EVENT WIRING ═════════════════ */

  // ── Open/close buttons ──
  document.addEventListener('click', function (e) {
    const toggleBtn = e.target.closest('.field-style-toggle');
    if (toggleBtn) {
      e.preventDefault();
      e.stopPropagation();
      togglePopover(toggleBtn.dataset.field);
      return;
    }
    const closeBtn = e.target.closest('.styler-close');
    if (closeBtn) {
      e.preventDefault();
      closePopover(closeBtn.dataset.close);
      return;
    }
    // Click outside → close all
    if (!e.target.closest('.field-styler-popover') && !e.target.closest('.field-style-toggle')) {
      document.querySelectorAll('.field-styler-popover.open').forEach(p => closePopover(p.dataset.field));
    }
  });

  // ── Reset button ──
  document.addEventListener('click', function (e) {
    const resetBtn = e.target.closest('.styler-reset-btn');
    if (!resetBtn) return;
    e.preventDefault();
    const fieldKey = resetBtn.dataset.field;
    delete fieldStyles[fieldKey];
    persistStyles();
    // Reset input / preview styling
    applyToInput(fieldKey, {});
    applyToPreview(fieldKey, {});
    // Re-sync popover controls
    const pop = document.getElementById(`styler-${fieldKey}`);
    if (pop) syncPopoverControls(pop, fieldKey);
  });

  // ── Clear color button ──
  document.addEventListener('click', function (e) {
    const clearBtn = e.target.closest('.styler-clear-color');
    if (!clearBtn) return;
    e.preventDefault();
    const fieldKey = clearBtn.dataset.field;
    const styles = getOrCreate(fieldKey);
    delete styles.color;
    persistStyles();
    applyToInput(fieldKey, styles);
    applyToPreview(fieldKey, styles);
    const pop = document.getElementById(`styler-${fieldKey}`);
    if (pop) syncPopoverControls(pop, fieldKey);
  });

  // ── Styler control changes (select & color picker) ──
  document.addEventListener('change', function (e) {
    const ctrl = e.target.closest('.styler-control');
    if (!ctrl) return;
    const fieldKey = ctrl.dataset.field;
    const prop     = ctrl.dataset.prop;
    if (!fieldKey || !prop) return;

    const value = ctrl.value;
    const styles = getOrCreate(fieldKey);

    if (value === '') {
      delete styles[prop];
    } else {
      styles[prop] = value;
      if (prop === 'font_family') loadGoogleFont(value);
    }

    // Sync hex text if this was the color picker
    if (prop === 'color') {
      const pop = document.getElementById(`styler-${fieldKey}`);
      if (pop) {
        const hexInput = pop.querySelector('.styler-color-hex');
        if (hexInput) hexInput.value = value;
      }
    }

    persistStyles();
    applyToInput(fieldKey, styles);
    applyToPreview(fieldKey, styles);
    updateMiniPreview(fieldKey);
  });

  // ── Styler control live input (color picker drag) ──
  document.addEventListener('input', function (e) {
    const ctrl = e.target.closest('.styler-control');
    if (ctrl && ctrl.type === 'color') {
      const fieldKey = ctrl.dataset.field;
      const styles = getOrCreate(fieldKey);
      styles.color = ctrl.value;
      const pop = document.getElementById(`styler-${fieldKey}`);
      if (pop) {
        const hexInput = pop.querySelector('.styler-color-hex');
        if (hexInput) hexInput.value = ctrl.value;
      }
      persistStyles();
      applyToInput(fieldKey, styles);
      applyToPreview(fieldKey, styles);
      updateMiniPreview(fieldKey);
    }
  });

  // ── Hex text input → sync color picker ──
  document.addEventListener('input', function (e) {
    const hexInput = e.target.closest('.styler-color-hex');
    if (!hexInput) return;
    const fieldKey = hexInput.dataset.field;
    const val = hexInput.value.trim();
    // Only apply if it looks like a valid hex
    if (/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(val)) {
      const styles = getOrCreate(fieldKey);
      styles.color = val;
      persistStyles();
      applyToInput(fieldKey, styles);
      applyToPreview(fieldKey, styles);
      updateMiniPreview(fieldKey);
      const pop = document.getElementById(`styler-${fieldKey}`);
      if (pop) {
        const picker = pop.querySelector('.styler-control[data-prop="color"]');
        if (picker) picker.value = val;
      }
    }
  });

  // ── Keep mini-preview text in sync as user types in the field ──
  document.addEventListener('input', function (e) {
    const input = e.target;
    if (!input.id || !input.id.startsWith('id_')) return;
    const fieldKey = input.id.replace(/^id_/, '');
    // If a popover for this field is open, update its mini-preview text
    const pop = document.getElementById(`styler-${fieldKey}`);
    if (pop && pop.classList.contains('open')) {
      updateMiniPreview(fieldKey);
    }
  });

  /* ═══════════════════════ INIT ═════════════════════════ */

  restoreAllStyles();
  persistStyles(); // ensure hidden input is up to date on load

})();
