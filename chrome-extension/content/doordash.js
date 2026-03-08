const T = window.__TRACED__;
let lastName = null;

async function injectDoorDashPanel() {
  const h1 = document.querySelector('h1');
  if (!h1) return;
  const name = h1.textContent.trim();
  if (!name || name === lastName) return;
  lastName = name;
  document.querySelectorAll(".traced-wrapper").forEach(e => e.remove());
  const result = await T.lookup(name, "doordash");
  if (!result || !result.matched) return;
  const wrapper = document.createElement("div");
  wrapper.className = "traced-wrapper";
  wrapper.innerHTML = T.buildPanel(result.brand);
  h1.parentElement.insertBefore(wrapper, h1.nextSibling);
}

const observer = new MutationObserver(() => {
  if (window.location.pathname.includes("/store/")) injectDoorDashPanel();
});
observer.observe(document.body, { childList: true, subtree: true });
setTimeout(injectDoorDashPanel, 1500);
console.log("[Traced Maps] DoorDash active");
