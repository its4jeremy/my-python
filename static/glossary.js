let activeButton = null;
function closeExplanation() {
  if (!activeButton) return;
  document.getElementById(activeButton.getAttribute('aria-describedby')).hidden = true;
  activeButton.setAttribute('aria-expanded', 'false');
  activeButton = null;
}
function positionExplanation(button, tip) {
  const bounds = button.getBoundingClientRect();
  tip.style.width = `${Math.min(320, window.innerWidth - 24)}px`;
  const height = tip.getBoundingClientRect().height;
  const left = Math.max(12, Math.min(bounds.left, window.innerWidth - tip.offsetWidth - 12));
  const top = bounds.bottom + height + 12 <= window.innerHeight
    ? bounds.bottom + 8 : Math.max(12, bounds.top - height - 8);
  tip.style.left = `${left}px`;
  tip.style.top = `${top}px`;
}
function openExplanation(button) {
  if (activeButton !== button) closeExplanation();
  activeButton = button;
  const tip = document.getElementById(button.getAttribute('aria-describedby'));
  tip.hidden = false;
  button.setAttribute('aria-expanded', 'true');
  positionExplanation(button, tip);
}
document.querySelectorAll('.glossary-term').forEach(button => {
  button.removeAttribute('title'); // Retain the native explanation only when JS is unavailable.
  button.addEventListener('pointerenter', event => {
    if (event.pointerType === 'mouse') openExplanation(button);
  });
  button.addEventListener('pointerleave', event => {
    if (event.pointerType === 'mouse' && document.activeElement !== button) closeExplanation();
  });
  button.addEventListener('focus', () => openExplanation(button));
  button.addEventListener('blur', closeExplanation);
  // Focus already opens the explanation; a tap or click keeps it open.
  button.addEventListener('click', () => openExplanation(button));
});
document.addEventListener('pointerdown', event => {
  if (!event.target.closest('.term-wrap')) closeExplanation();
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeExplanation();
});
window.addEventListener('scroll', () => {
  if (activeButton && document.activeElement === activeButton) {
    positionExplanation(activeButton, document.getElementById(activeButton.getAttribute('aria-describedby')));
  } else closeExplanation();
}, true);
window.addEventListener('resize', closeExplanation);
document.querySelectorAll('.source-layout').forEach(details => {
  details.addEventListener('toggle', () => {
    if (!details.open) return;
    details.querySelectorAll('img[data-src]').forEach(image => {
      image.src = image.dataset.src;
      delete image.dataset.src;
    });
  });
});
