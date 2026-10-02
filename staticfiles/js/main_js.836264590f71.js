
const buttons = document.querySelectorAll("[data-filter]");
const cards = document.querySelectorAll("#listings .listing");
const empty = document.getElementById("filter-empty");

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    buttons.forEach((item) => {
      item.classList.remove("active");
      item.setAttribute("aria-pressed", "false");
    });
    button.classList.add("active");
    button.setAttribute("aria-pressed", "true");

    let visible = 0;
    cards.forEach((card) => {
      const show = filter === "all" || card.dataset.type === filter;
      card.hidden = !show;
      if (show) visible += 1;
    });

    if (empty) empty.hidden = visible !== 0;
  });
});

buttons.forEach((button) => {
  button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
});

const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.getElementById("site-nav");
if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const open = siteNav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", open ? "true" : "false");
  });
}

const profileFilterButtons = document.querySelectorAll("[data-profile-filter]");
const profileProjects = document.querySelectorAll("[data-profile-type]");
const profileEmpty = document.getElementById("profile-filter-empty");

profileFilterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.profileFilter;
    let visible = 0;
    profileFilterButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    profileProjects.forEach((project) => {
      const show = filter === "all" || project.dataset.profileType === filter;
      project.hidden = !show;
      if (show) visible += 1;
    });
    if (profileEmpty) profileEmpty.hidden = visible !== 0;
  });
});
