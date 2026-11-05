/**
 * MindTheSpec Client Interactions
 * Lightweight, accessible vanilla JS. No console errors or external dependencies.
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Confirmation handler for critical actions (e.g., project deletion, locking sessions)
  const confirmForms = document.querySelectorAll("form[data-confirm]");
  confirmForms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      const message = form.getAttribute("data-confirm") || "Are you sure you want to proceed?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // 2. Responsive Workspace Sidebar Toggle (Mobile / Tablet)
  const sidebar = document.getElementById("appSidebar");
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const closeBtn = document.getElementById("sidebarCloseBtn");

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  if (closeBtn && sidebar) {
    closeBtn.addEventListener("click", function () {
      sidebar.classList.remove("open");
    });
  }

  // Close sidebar on click outside when open on small screens
  document.addEventListener("click", function (e) {
    if (sidebar && sidebar.classList.contains("open")) {
      if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    }
  });

  // 3. Form Submission Loading States (Form validation & double-submit prevention)
  const allForms = document.querySelectorAll("form:not([data-async])");
  allForms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (form.checkValidity && !form.checkValidity()) {
        return; // Native HTML5 validation will display error
      }
      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.dataset.originalText = submitBtn.innerText;
        submitBtn.disabled = true;
        submitBtn.classList.add("btn-loading");
        const loadingText = submitBtn.getAttribute("data-loading-text") || "Processing...";
        submitBtn.innerText = loadingText;
        // Safety re-enable after 8 seconds in case of slow network or cancel
        setTimeout(function () {
          if (submitBtn.disabled) {
            submitBtn.disabled = false;
            submitBtn.innerText = submitBtn.dataset.originalText || "Submit";
          }
        }, 8000);
      }
    });
  });
});
