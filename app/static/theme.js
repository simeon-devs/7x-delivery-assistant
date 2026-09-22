/* Theme switch, shared by every page.

   Loaded in <head> and run immediately so the attribute is on <html> before the
   first paint. Doing it after render gives a visible flash of the wrong theme.

   LIGHT IS THE DEFAULT and the device setting is deliberately ignored. This gets
   recorded and presented on machines whose settings are unknown, and the theme
   has to be a decision rather than a surprise. The choice is remembered per
   browser; localStorage can throw in a private window, so every access is
   wrapped. */
(function () {
  var KEY = "7x-theme";
  var theme = "light";
  try { theme = localStorage.getItem(KEY) || "light"; } catch (e) { /* private window */ }
  document.documentElement.setAttribute("data-theme", theme);

  function label() {
    var dark = document.documentElement.getAttribute("data-theme") === "dark";
    document.querySelectorAll("[data-theme-label]").forEach(function (el) {
      el.textContent = dark ? "Light" : "Dark";
    });
  }

  window.toggleTheme = function () {
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
    label();
  };

  document.addEventListener("DOMContentLoaded", label);
})();
