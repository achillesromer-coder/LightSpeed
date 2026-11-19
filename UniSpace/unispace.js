'use strict';
const groups = [
  {name: 'Specifications', count: 92, color: '#116b60'},
  {name: 'Tests', count: 162, color: '#477b9a'},
  {name: 'Runtime', count: 51, color: '#ae6337'},
  {name: 'Records and guides', count: 127, color: '#637268'}
];
const canvas = document.querySelector('#atlas');
const buttons = Array.from(document.querySelectorAll('[data-set]'));
let selected = -1;

function drawAtlas() {
  const context = canvas.getContext('2d');
  if (!context) return;
  const width = canvas.clientWidth, height = canvas.clientHeight;
  const scale = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  context.scale(scale, scale);
  const radius = Math.min(width * 0.36, height * 0.39);
  context.translate(width / 2, height / 2);
  context.rotate(-0.32);
  context.strokeStyle = '#dce5df';
  for (let ring = 1; ring <= 4; ring++) {
    context.beginPath();
    context.ellipse(0, 0, radius * (0.6 + ring * 0.17), radius * (0.3 + ring * 0.09), 0, 0, Math.PI * 2);
    context.stroke();
  }
  const points = [];
  let index = 0;
  for (const [group, set] of groups.entries()) {
    for (let i = 0; i < set.count; i++, index++) {
      const theta = index * 2.399963229728653;
      const y = 1 - (index + 0.5) * 2 / 432;
      const ring = Math.sqrt(1 - y * y);
      const z = ring * Math.sin(theta);
      const depth = z * 0.86 - y * 0.50;
      points.push({x: radius * ring * Math.cos(theta), y: radius * (y * 0.86 + z * 0.50), depth, group});
    }
  }
  points.sort((a,b) => a.depth - b.depth);
  for (const point of points) {
    context.fillStyle = groups[point.group].color;
    context.globalAlpha = selected >= 0 && selected !== point.group ? 0.10 : 0.65 + 0.3 * point.depth;
    context.beginPath();
    context.arc(point.x, point.y, Math.max(1.2, radius * 0.015) * (1 + 0.27 * point.depth), 0, Math.PI * 2);
    context.fill();
  }
  context.globalAlpha = 1;
}
for (const [i, button] of buttons.entries()) {
  button.addEventListener('click', () => {
    selected = selected === i ? -1 : i;
    buttons.forEach((b,j) => b.setAttribute('aria-pressed', String(selected === j)));
    const label = selected < 0 ? '432 tracked files' : groups[selected].name + ' · ' + groups[selected].count + ' files';
    document.querySelector('#plot-label').textContent = label;
    document.querySelector('#selection').textContent = selected < 0 ? 'Showing all 432 files.' : label + ' highlighted. Select again to show all.';
    drawAtlas();
  });
}
drawAtlas();
window.addEventListener('resize', drawAtlas);

const picker = document.querySelector('#file');
const result = document.querySelector('#result');
picker.addEventListener('change', async () => {
  const file = picker.files[0];
  result.textContent = '';
  if (!file) return;
  if (file.size !== 3609020) {
    result.textContent = 'Different file size. The S91 reference is 3,609,020 bytes.';
    return;
  }
  try {
    result.textContent = 'Checking file…';
    const hash = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
    if (picker.files[0] !== file) return;
    const digest = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2,'0')).join('');
    result.textContent = digest === document.querySelector('.check code').textContent
      ? 'Verified. This file matches the S91 product reference.' : 'Checksum mismatch. This file differs from the S91 reference.';
  } catch {
    if (picker.files[0] === file) result.textContent = 'Browser verification unavailable. Compare the reference SHA-256 with a local checksum tool.';
  }
});
