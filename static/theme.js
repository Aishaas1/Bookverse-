document.documentElement.dataset.theme =
  localStorage.getItem("bookverse-theme") || "light";
document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#theme").onclick = () => {
    const mode =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = mode;
    localStorage.setItem("bookverse-theme", mode);
  };
});
