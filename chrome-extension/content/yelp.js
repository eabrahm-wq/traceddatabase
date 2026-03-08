const T = window.__TRACED__;

async function injectYelpPanel() {
  const h1 = document.querySelector('h1');
  if (!h1 || document.querySelector(".traced-wrapper")) return;
  const name = h1.textContent.trim();
  if (!name || name.length < 2) return;
  const result = await T.lookup(name, "yelp");
  if (!result || !result.matched) return;
  const wrapper = document.createElement("div");
  wrapper.className = "traced-wrapper";
  wrapper.innerHTML = T.buildPanel(result.brand);
  h1.parentElement.insertBefore(wrapper, h1.nextSibling);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", injectYelpPanel);
} else {
  injectYelpPanel();
}
console.log("[Traced Maps] Yelp active");
