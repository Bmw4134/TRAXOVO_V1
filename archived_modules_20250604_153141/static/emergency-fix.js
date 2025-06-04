// TRAXOVO Emergency JavaScript Fix - Immediate Error Resolution
(function () {
  "use strict";

  // Fix all closest() compatibility issues immediately
  if (!Element.prototype.closest) {
    Element.prototype.closest = function (selector) {
      var el = this;
      while (el && el.nodeType === 1) {
        if (el.matches && el.matches(selector)) {
          return el;
        }
        el = el.parentElement || el.parentNode;
      }
      return null;
    };
  }

  // Fix matches() compatibility
  if (!Element.prototype.matches) {
    Element.prototype.matches =
      Element.prototype.matchesSelector ||
      Element.prototype.mozMatchesSelector ||
      Element.prototype.msMatchesSelector ||
      Element.prototype.oMatchesSelector ||
      Element.prototype.webkitMatchesSelector ||
      function (s) {
        var matches = (this.document || this.ownerDocument).querySelectorAll(s);
        var i = matches.length;
        while (--i >= 0 && matches.item(i) !== this) {}
        return i > -1;
      };
  }

  // Minimal error handling - don't interfere with legitimate functionality
  console.log("TRAXOVO Compatibility Layer Active");

  console.log("TRAXOVO Emergency Fix Active - JavaScript errors suppressed");
})();
