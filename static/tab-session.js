(() => {
  const token = document.querySelector('meta[name="app-tab-token"]')?.content;
  if (!token) return;

  const address = new URL(window.location.href);
  address.searchParams.delete("_tab");
  window.history.replaceState(null, "", address);

  const addTabToken = (element, attribute) => {
    const value = element.getAttribute(attribute);
    if (!value) return;

    const target = new URL(value, window.location.href);
    if (target.origin !== window.location.origin) return;

    target.searchParams.set("_tab", token);
    element.setAttribute(attribute, `${target.pathname}${target.search}${target.hash}`);
  };

  document.querySelectorAll("a[href]").forEach((link) => addTabToken(link, "href"));
  document.querySelectorAll("form[action]").forEach((form) => addTabToken(form, "action"));
})();
