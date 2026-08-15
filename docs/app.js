const grid = document.querySelector("#style-grid");
const status = document.querySelector("#gallery-status");
const filters = [...document.querySelectorAll(".filter")];
const dialog = document.querySelector("#style-dialog");
const toast = document.querySelector("#toast");
const carousel = document.querySelector("#hero-carousel");
const carouselTrack = document.querySelector("#carousel-track");
const carouselKicker = document.querySelector("#carousel-kicker");
const carouselTitle = document.querySelector("#carousel-title");
const carouselCounter = document.querySelector("#carousel-counter");
const carouselToggle = document.querySelector("#carousel-toggle");
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let styles = [];
let toastTimer;
let activeStyleIndex = 0;
let carouselItems = [];
let carouselIndex = 0;
let carouselTimer;
let carouselPaused = false;
let carouselInteracting = false;

const labels = {
  right_grazing_daylight: "右侧自然侧光",
  soft_diagonal_window: "柔和斜向窗影",
  broad_center_glow: "宽幅中心柔光",
  cinematic_center_falloff: "电影感中央衰减",
  dappled_afternoon: "午后虚化光斑",
  paper_halo: "纸面漫射柔光",
  vertical_soft_beams: "纵向宽幅柔影",
  architectural_diagonal: "建筑斜向窗光",
  limewash_diffusion: "石灰墙漫射",
  stone_diagonal: "石材宽幅斜光",
  top_gallery_glow: "对称顶光",
  upper_left_spotlight: "左上聚光",
  flat: "贴合",
  subtle_float: "轻悬浮",
  premium_float: "高级悬浮",
  architectural: "建筑感深阴影",
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function groupMatches(style, filter) {
  if (filter === "all") return true;
  const haystack = `${style.categories.join(" ")} ${style.material} ${style.lighting}`.toLowerCase();
  if (filter === "paper") return /paper|washi|纸/.test(haystack);
  if (filter === "textile") return /textile|linen|fabric|亚麻|织物/.test(haystack);
  if (filter === "mineral") return /mineral|stone|stucco|plaster|limewash|travertine|sand/.test(haystack);
  if (filter === "light") return /light|glow|window|spot|beam|cinematic|sun/.test(haystack);
  return false;
}

function cardTemplate(style) {
  return `
    <article class="style-card" data-style-id="${escapeHtml(style.style_id)}">
      <button class="style-image-button" type="button" data-open="${escapeHtml(style.style_id)}" aria-label="查看第 ${style.order} 种风格：${escapeHtml(style.name)}">
        <img src="${escapeHtml(style.image)}" width="750" height="1000" loading="eager" alt="第 ${style.order} 种背景效果：${escapeHtml(style.name)}">
        <span class="style-number" aria-hidden="true">${String(style.order).padStart(2, "0")}</span>
      </button>
      <div class="style-card-body">
        <div class="style-name-group">
          <h3>${escapeHtml(style.name)}</h3>
          <span>${escapeHtml(style.material)}</span>
        </div>
        <button class="copy-icon-button" type="button" data-copy="${escapeHtml(style.name)}" data-copy-kind="name" aria-label="复制中文名：${escapeHtml(style.name)}" title="复制中文名">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>
        </button>
      </div>
    </article>`;
}

function render(filter = "all") {
  const visible = styles.filter((style) => groupMatches(style, filter));
  grid.innerHTML = visible.map(cardTemplate).join("");
  status.textContent = `当前显示 ${visible.length} / ${styles.length} 种效果`;
}

function carouselItemTemplate(item, index) {
  return `
    <div class="carousel-slide${index === 0 ? " active" : ""}" aria-hidden="${index === 0 ? "false" : "true"}">
      <img
        src="${escapeHtml(item.image)}"
        width="750"
        height="1000"
        loading="${index === 0 ? "eager" : "lazy"}"
        alt="${escapeHtml(item.alt)}"
      >
    </div>`;
}

function updateCarousel(index) {
  if (!carouselItems.length) return;
  carouselIndex = (index + carouselItems.length) % carouselItems.length;
  [...carouselTrack.children].forEach((slide, slideIndex) => {
    const active = slideIndex === carouselIndex;
    slide.classList.toggle("active", active);
    slide.setAttribute("aria-hidden", String(!active));
  });
  const item = carouselItems[carouselIndex];
  const position = `${String(carouselIndex + 1).padStart(2, "0")} / ${String(carouselItems.length).padStart(2, "0")}`;
  carouselKicker.textContent = `${item.kicker} · ${position}`;
  carouselTitle.textContent = item.title;
  carouselCounter.textContent = position;
}

function stopCarousel() {
  window.clearInterval(carouselTimer);
  carouselTimer = undefined;
}

function startCarousel(force = false) {
  stopCarousel();
  if (carouselPaused || (!force && carouselInteracting) || reducedMotion.matches || document.hidden) return;
  carouselTimer = window.setInterval(() => updateCarousel(carouselIndex + 1), 4500);
}

function stepCarousel(direction) {
  updateCarousel(carouselIndex + direction);
  startCarousel();
}

function setCarouselPaused(paused) {
  carouselPaused = paused;
  carouselToggle.setAttribute("aria-pressed", String(paused));
  carouselToggle.setAttribute("aria-label", paused ? "继续自动播放" : "暂停自动播放");
  if (paused) stopCarousel();
  else startCarousel(true);
}

function initializeCarousel() {
  carouselItems = Array.isArray(window.CAROUSEL_ITEMS) ? window.CAROUSEL_ITEMS : [];
  if (carouselItems.length !== 15) throw new Error(`预期 15 张轮播素材，实际 ${carouselItems.length} 张`);
  carousel.setAttribute("aria-label", `票根成品轮播，共 ${carouselItems.length} 张`);
  carouselTrack.innerHTML = carouselItems.map(carouselItemTemplate).join("");
  updateCarousel(0);
  startCarousel();
}

function showToast(message) {
  window.clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("show");
  toastTimer = window.setTimeout(() => toast.classList.remove("show"), 1800);
}

async function copyText(text, kind = "command") {
  const isName = kind === "name";
  try {
    await navigator.clipboard.writeText(text);
    showToast(isName ? `已复制：${text}` : "调用语句已复制");
  } catch {
    window.prompt(isName ? "请复制下面的中文名：" : "请复制下面的调用语句：", text);
  }
}

function openDialog(styleId) {
  const index = styles.findIndex((item) => item.style_id === styleId);
  if (index < 0) return;
  activeStyleIndex = index;
  updateDialog(styles[activeStyleIndex]);
  document.body.classList.add("dialog-open");
  if (!dialog.open) dialog.showModal();
}

function updateDialog(style) {
  if (!style) return;
  document.querySelector("#dialog-image").src = style.image;
  document.querySelector("#dialog-image").alt = `第 ${style.order} 种背景效果：${style.name}`;
  document.querySelector("#dialog-order").textContent = `STYLE ${String(style.order).padStart(2, "0")}`;
  document.querySelector("#dialog-name").textContent = style.name;
  document.querySelector("#dialog-id").textContent = style.style_id;
  document.querySelector("#dialog-description").textContent = style.description;
  document.querySelector("#dialog-material").textContent = style.material;
  document.querySelector("#dialog-lighting").textContent = labels[style.lighting] || style.lighting;
  document.querySelector("#dialog-shadow").textContent = labels[style.shadow] || style.shadow;
  document.querySelector("#dialog-best-for").textContent = style.best_for.join("、");
  document.querySelector("#dialog-copy").dataset.copy = style.name;
  document.querySelector("#dialog-copy").dataset.copyKind = "name";
  document.querySelector("#dialog-prev").setAttribute("aria-label", `上一种风格：${styles[(activeStyleIndex - 1 + styles.length) % styles.length].name}`);
  document.querySelector("#dialog-next").setAttribute("aria-label", `下一种风格：${styles[(activeStyleIndex + 1) % styles.length].name}`);
}

function stepDialog(direction) {
  activeStyleIndex = (activeStyleIndex + direction + styles.length) % styles.length;
  updateDialog(styles[activeStyleIndex]);
}

document.addEventListener("click", (event) => {
  const openTarget = event.target.closest("[data-open]");
  if (openTarget) {
    openDialog(openTarget.dataset.open);
    return;
  }
  const copyTarget = event.target.closest("[data-copy]");
  if (copyTarget) copyText(copyTarget.dataset.copy, copyTarget.dataset.copyKind);
});

filters.forEach((button) => {
  button.addEventListener("click", () => {
    filters.forEach((item) => {
      item.classList.remove("active");
      item.setAttribute("aria-pressed", "false");
    });
    button.classList.add("active");
    button.setAttribute("aria-pressed", "true");
    render(button.dataset.filter);
  });
});

document.querySelector("#copy-default").addEventListener("click", () => {
  copyText("把这张图片做成票根，使用默认轻质感纯色背景，颜色按图片主题色生成。");
});

document.querySelector("#carousel-prev").addEventListener("click", () => stepCarousel(-1));
document.querySelector("#carousel-next").addEventListener("click", () => stepCarousel(1));
carouselToggle.addEventListener("click", () => setCarouselPaused(!carouselPaused));
carousel.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    stepCarousel(-1);
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    stepCarousel(1);
  }
  if (event.key === " ") {
    event.preventDefault();
    setCarouselPaused(!carouselPaused);
  }
});
carousel.addEventListener("mouseenter", () => {
  carouselInteracting = true;
  stopCarousel();
});
carousel.addEventListener("mouseleave", () => {
  carouselInteracting = false;
  startCarousel();
});
carousel.addEventListener("focusin", () => {
  carouselInteracting = true;
  stopCarousel();
});
carousel.addEventListener("focusout", (event) => {
  if (carousel.contains(event.relatedTarget)) return;
  carouselInteracting = false;
  startCarousel();
});
document.addEventListener("visibilitychange", startCarousel);
reducedMotion.addEventListener("change", startCarousel);

document.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
document.querySelector("#dialog-prev").addEventListener("click", () => stepDialog(-1));
document.querySelector("#dialog-next").addEventListener("click", () => stepDialog(1));
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
dialog.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    stepDialog(-1);
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    stepDialog(1);
  }
});
dialog.addEventListener("close", () => document.body.classList.remove("dialog-open"));

function initialize(data) {
  styles = data.styles;
  if (styles.length !== 12) throw new Error(`预期 12 种风格，实际 ${styles.length} 种`);
  render();
  initializeCarousel();
}

if (window.STYLE_GALLERY_DATA) {
  try {
    initialize(window.STYLE_GALLERY_DATA);
  } catch (error) {
    status.textContent = `风格数据载入失败：${error.message}`;
    status.style.color = "#a33232";
  }
} else {
  fetch("style-data.json")
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then(initialize)
    .catch((error) => {
      status.textContent = `风格数据载入失败：${error.message}`;
      status.style.color = "#a33232";
    });
}
