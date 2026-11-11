import * as pdfjsLib from "/static/vendor/pdf.min.mjs";
pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdf.worker.min.mjs";
const root = document.querySelector("#reader"),
  canvas = document.querySelector("#pdf-canvas"),
  input = document.querySelector("#page"),
  status = document.querySelector("#save-status");
let pdf,
  page = Number(root.dataset.page),
  scale = 1.2,
  busy = false,
  queued = false;
async function draw() {
  if (busy) {
    queued = true;
    return;
  }
  busy = true;
  const renderedPage = page;
  try {
    const p = await pdf.getPage(renderedPage),
      viewport = p.getViewport({ scale });
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    await p.render({ canvasContext: canvas.getContext("2d"), viewport })
      .promise;
    input.value = renderedPage;
    const response = await fetch(root.dataset.save, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
          .value,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: "page=" + renderedPage,
    });
    status.textContent = response.ok
      ? "✓ حُفظ تقدمك"
      : "تعذر حفظ التقدم؛ أعد تسجيل الدخول.";
  } catch (e) {
    status.textContent = "تعذر عرض الصفحة. حاول مجددًا.";
  } finally {
    busy = false;
    if (queued) {
      queued = false;
      draw();
    }
  }
}
function go(n) {
  if (pdf && n >= 1 && n <= pdf.numPages) {
    page = n;
    draw();
  }
}
document.querySelector("#prev").onclick = () => go(page - 1);
document.querySelector("#next").onclick = () => go(page + 1);
input.onchange = () => go(Number(input.value));
document.querySelector("#zoom-in").onclick = () => {
  scale = Math.min(3, scale + 0.2);
  draw();
};
document.querySelector("#zoom-out").onclick = () => {
  scale = Math.max(0.4, scale - 0.2);
  draw();
};
pdfjsLib
  .getDocument({ url: root.dataset.url, isEvalSupported: false })
  .promise.then((doc) => {
    pdf = doc;
    page = Math.min(page, pdf.numPages);
    draw();
  })
  .catch(
    () => (status.textContent = "تعذر تحميل الكتاب. تحقق من تسجيل الدخول."),
  );
