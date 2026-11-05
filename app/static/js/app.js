/**
 * MindTheSpec Client Interactions
 * Lightweight, accessible vanilla JS. No console errors or dependencies.
 */

document.addEventListener("DOMContentLoaded", function () {
  // Confirmation handler for critical actions (e.g., locking sessions)
  const confirmForms = document.querySelectorAll("form[data-confirm]");
  confirmForms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      const message = form.getAttribute("data-confirm") || "Are you sure you want to proceed?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
