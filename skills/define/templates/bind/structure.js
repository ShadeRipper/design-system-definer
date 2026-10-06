// ---- structure pass: verified auto-layout, role names, spacing variables ----
// Every auto-layout conversion is verified: if any child moves more than 1px or changes size, it is rolled back.
const OPT = typeof OPTIONS === 'undefined' ? {layout: true, names: true, spacing: true} : OPTIONS;
const S = {nodes: 0, instanceNodesSkipped: 0, layout: {candFrames: 0, candGroups: 0, converted: 0, groupsConverted: 0, reverted: 0, notClean: {}}, names: {renamed: 0}, spacing: {bound: 0, offGrid: {}}, errors: []};
const targets = await collect(ROOT_IDS);
const LEAF = new Set(['VECTOR', 'BOOLEAN_OPERATION', 'STAR', 'POLYGON', 'LINE', 'ELLIPSE', 'RECTANGLE']);
// detect a clean row or column: no overlap, one counter-axis alignment, equal gaps (or space-between)
function detect(boxes, W, H) {
  if (boxes.length < 2) return {no: 'single'};
  const eq = (a, b, t = 1) => Math.abs(a - b) <= t;
  for (const dir of ['HORIZONTAL', 'VERTICAL']) {
    const H1 = dir === 'HORIZONTAL';
    const key = b => H1 ? {p: b.x, ps: b.w, c: b.y, cs: b.h} : {p: b.y, ps: b.h, c: b.x, cs: b.w};
    const sorted = [...boxes].sort((a, b) => key(a).p - key(b).p);
    let ok = true; const gaps = [];
    for (let i = 1; i < sorted.length; i++) { const a = key(sorted[i - 1]), b2 = key(sorted[i]); const g = b2.p - (a.p + a.ps); if (g < -0.5) { ok = false; break; } gaps.push(g); }
    if (!ok) continue;
    const kk = sorted.map(key); const CW = H1 ? H : W; let align = null;
    if (kk.every(k => eq(k.c, kk[0].c))) align = 'MIN';
    else if (kk.every(k => eq(k.c + k.cs, kk[0].c + kk[0].cs))) align = 'MAX';
    else if (kk.every(k => eq(k.c + k.cs / 2, CW / 2))) align = 'CENTER';
    if (!align) continue;
    const mean = gaps.reduce((a, b) => a + b, 0) / gaps.length; const PW = H1 ? W : H; let mode = null, spacing = 0;
    if (gaps.every(g => eq(g, mean))) { mode = 'MIN'; spacing = Math.round(mean); }
    else if (eq(kk[0].p, PW - (kk[kk.length - 1].p + kk[kk.length - 1].ps))) mode = 'SPACE_BETWEEN';
    if (!mode) continue;
    const padStart = Math.round(kk[0].p); if (padStart < 0) continue;
    let padC = 0; if (align === 'MIN') padC = Math.round(kk[0].c); else if (align === 'MAX') padC = Math.round(CW - (kk[0].c + kk[0].cs));
    if (padC < 0) continue;
    return {dir, mode, spacing, align, padStart, padC, order: sorted};
  }
  return {no: 'not-clean'};
}
function applyLayout(F, det, kids) {
  const orig = [...F.children];
  const saved = kids.map(k => ({k, x: k.x, y: k.y, w: k.width, h: k.height, ax: absT(k).x, ay: absT(k).y}));
  const fw = F.width, fh = F.height, H1 = det.dir === 'HORIZONTAL';
  F.layoutMode = det.dir; F.primaryAxisSizingMode = 'FIXED'; F.counterAxisSizingMode = 'FIXED';
  F.itemSpacing = det.mode === 'SPACE_BETWEEN' ? 0 : det.spacing;
  F.primaryAxisAlignItems = det.mode === 'SPACE_BETWEEN' ? 'SPACE_BETWEEN' : 'MIN'; F.counterAxisAlignItems = det.align;
  const ps = det.padStart;
  if (H1) { F.paddingLeft = ps; F.paddingRight = det.mode === 'SPACE_BETWEEN' ? ps : 0; F.paddingTop = det.align === 'MIN' ? det.padC : 0; F.paddingBottom = det.align === 'MAX' ? det.padC : 0; }
  else { F.paddingTop = ps; F.paddingBottom = det.mode === 'SPACE_BETWEEN' ? ps : 0; F.paddingLeft = det.align === 'MIN' ? det.padC : 0; F.paddingRight = det.align === 'MAX' ? det.padC : 0; }
  det.order.forEach((b, i) => { const k = kids.find(c => c.id === b.id); F.insertChild(i, k); });
  let bad = Math.abs(F.width - fw) > 0.5 || Math.abs(F.height - fh) > 0.5;
  if (!bad) for (const s of saved) { const a = absT(s.k); if (Math.abs(a.x - s.ax) > 1 || Math.abs(a.y - s.ay) > 1 || Math.abs(s.k.width - s.w) > 0.5 || Math.abs(s.k.height - s.h) > 0.5) { bad = true; break; } }
  if (bad) { F.layoutMode = 'NONE'; orig.forEach((k, i) => F.insertChild(i, k));
    for (const s of saved) { s.k.x = s.x; s.k.y = s.y; if (Math.abs(s.k.width - s.w) > 0.1 || Math.abs(s.k.height - s.h) > 0.1) s.k.resize(s.w, s.h); }
    if (Math.abs(F.width - fw) > 0.1 || Math.abs(F.height - fh) > 0.1) F.resize(fw, fh); }
  return !bad;
}
const dirOf = n => n.layoutMode === 'HORIZONTAL' ? 'Row' : n.layoutMode === 'VERTICAL' ? 'Column' : 'Container';
if (OPT.layout) {
  for (const [n, inInst] of [...targets].reverse()) { // children before parents
    if (inInst) continue;
    try {
      if (n.type === 'FRAME' && (n.layoutMode === 'NONE' || !n.layoutMode)) {
        const kids = n.children.filter(VISIBLE); if (kids.length < 2) continue; S.layout.candFrames++;
        if (kids.some(k => k.rotation && Math.abs(k.rotation) > 0.01) || kids.some(k => k.layoutPositioning === 'ABSOLUTE')) { bump(S.layout.notClean, 'rotated/absolute'); continue; }
        if (n.children.length !== kids.length) { bump(S.layout.notClean, 'hidden-siblings'); continue; }
        const det = detect(kids.map(k => ({id: k.id, x: k.x, y: k.y, w: k.width, h: k.height})), n.width, n.height);
        if (det.no) { bump(S.layout.notClean, det.no); continue; }
        if (APPLY) { if (applyLayout(n, det, kids)) S.layout.converted++; else S.layout.reverted++; } else S.layout.converted++;
      } else if (n.type === 'GROUP') { // a group cannot hold auto-layout: replace it with a frame only when a clean layout exists
        const kids = n.children.filter(VISIBLE); if (kids.length < 2 || n.children.length !== kids.length) continue; S.layout.candGroups++;
        if (n.opacity < 1 || (n.blendMode && n.blendMode !== 'PASS_THROUGH' && n.blendMode !== 'NORMAL') || (n.effects && n.effects.length) || kids.some(k => k.isMask || (k.rotation && Math.abs(k.rotation) > 0.01)) || (n.rotation && Math.abs(n.rotation) > 0.01)) { bump(S.layout.notClean, 'group-mask/effect/rotation'); continue; }
        const par = n.parent; if (!par || ('layoutMode' in par && par.layoutMode && par.layoutMode !== 'NONE') || par.type === 'INSTANCE') { bump(S.layout.notClean, 'group-in-autolayout'); continue; }
        const gt = absT(n);
        const det = detect(kids.map(k => { const a = absT(k); return {id: k.id, x: a.x - gt.x, y: a.y - gt.y, w: k.width, h: k.height}; }), n.width, n.height);
        if (det.no) { bump(S.layout.notClean, 'group-' + det.no); continue; }
        if (!APPLY) { S.layout.groupsConverted++; continue; }
        const idx = par.children.indexOf(n); const fr = figma.createFrame(); fr.name = n.name; fr.fills = []; fr.clipsContent = false;
        par.insertChild(idx, fr); fr.resize(n.width, n.height); const pt = absT(par); fr.x = gt.x - pt.x; fr.y = gt.y - pt.y;
        const kl = [...n.children]; const abs0 = kl.map(k => ({k, a: absT(k)}));
        for (const k of kl) fr.appendChild(k);
        const ft = absT(fr); for (const o of abs0) { o.k.x = o.a.x - ft.x; o.k.y = o.a.y - ft.y; }
        const det2 = detect(kl.map(k => ({id: k.id, x: k.x, y: k.y, w: k.width, h: k.height})), fr.width, fr.height);
        const ok = !det2.no && applyLayout(fr, det2, kl);
        if (ok) S.layout.groupsConverted++; else S.layout.reverted++;
        try { if (!n.removed) n.remove(); } catch (e2) {}
      }
    } catch (e) { S.errors.push('layout ' + n.id + ': ' + String(e.message).slice(0, 80)); }
  }
}
const fresh = await collect(ROOT_IDS);
const DEFAULT = /^(Frame|Group|Rectangle|Ellipse|Vector|Line|Polygon|Star|Container|Component|Boolean|Subtract|Union|Intersect|Exclude|Image|Mask)\s*\d*$|^(div|span|a|p|img|svg|ul|li|ol|h[1-6]|section|nav|header|footer|main|label|input|path|g|form|aside|article|button)(\.[\w-]+)*\s*\d*$/i;
const hasFillVis = n => 'fills' in n && Array.isArray(n.fills) && n.fills.some(p => p.visible !== false && (p.type !== 'SOLID' || p.opacity === undefined || p.opacity > 0.05));
const hasImg = n => 'fills' in n && Array.isArray(n.fills) && n.fills.some(p => p.type === 'IMAGE' && p.visible !== false);
const hasStroke = n => 'strokes' in n && Array.isArray(n.strokes) && n.strokes.some(p => p.visible !== false);
function roleName(n) {
  const w = n.width, h = n.height;
  if (n.type === 'RECTANGLE') { if (Math.min(w, h) <= 2) return 'Divider'; if (hasImg(n)) return 'Image'; const p = n.parent; if (p && 'width' in p && w >= p.width * 0.95 && h >= p.height * 0.95) return 'Background'; return 'Shape'; }
  if (['VECTOR', 'BOOLEAN_OPERATION', 'STAR', 'POLYGON'].includes(n.type)) return Math.max(w, h) <= 48 ? 'Icon' : 'Illustration';
  if (n.type === 'LINE') return 'Line';
  if (n.type === 'ELLIPSE') { if (hasImg(n)) return 'Avatar'; return w <= 16 ? 'Dot' : 'Circle'; }
  if (n.type === 'FRAME' || n.type === 'GROUP') {
    if (hasImg(n)) return 'Image';
    const kids = n.children.filter(VISIBLE); if (kids.length === 0) return null;
    if (kids.every(c => LEAF.has(c.type) || c.type === 'GROUP' || (c.type === 'FRAME' && c.children && c.children.every(d => LEAF.has(d.type)))) && Math.max(w, h) <= 48 && !kids.some(c => c.type === 'TEXT')) return 'Icon';
    const texts = kids.filter(c => c.type === 'TEXT'), t = texts[0]; const cr = typeof n.cornerRadius === 'number' ? n.cornerRadius : 0;
    if (t && texts.length <= 2 && t.characters.length <= 28 && t.characters.trim()) {
      const label = t.characters.trim().replace(/\s+/g, ' ');
      if (n.type === 'FRAME' && h <= 32 && h >= 18 && cr >= h / 2 - 1 && (hasFillVis(n) || hasStroke(n))) return 'Tag / ' + label;
      if (n.type === 'FRAME' && h >= 32 && h <= 64 && w <= 320 && texts.length === 1 && (hasFillVis(n) || hasStroke(n)) && cr >= 4) return 'Button / ' + label;
      return dirOf(n) + ' / ' + label;
    }
    if (n.type === 'FRAME' && w >= 200 && h >= 100 && (hasFillVis(n) || hasStroke(n)) && cr >= 8) return 'Card';
    return dirOf(n);
  }
  return null;
}
for (const [n, inInst] of fresh) {
  S.nodes++; if (inInst) { S.instanceNodesSkipped++; continue; }
  try {
    if (OPT.names && !['TEXT', 'SECTION', 'INSTANCE', 'COMPONENT'].includes(n.type) && DEFAULT.test(n.name)) { const nm = roleName(n); if (nm && nm !== n.name) { if (APPLY) n.name = nm.slice(0, 60); S.names.renamed++; } }
    if (OPT.spacing && n.type === 'FRAME' && n.layoutMode && n.layoutMode !== 'NONE') {
      const fields = ['itemSpacing', 'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom']; if (n.layoutWrap === 'WRAP') fields.push('counterAxisSpacing');
      for (const f of fields) { const v = n[f]; if (typeof v !== 'number' || v === 0) continue; const key = CONFIG.space[String(Math.round(v * 100) / 100)];
        if (key && V[key]) { if (APPLY) n.setBoundVariable(f, V[key]); S.spacing.bound++; } else bump(S.spacing.offGrid, String(Math.round(v * 10) / 10)); }
    }
  } catch (e) { S.errors.push('name/spacing ' + n.id + ': ' + String(e.message).slice(0, 80)); }
}
const top = (o, k = 10) => Object.entries(o).sort((a, c) => c[1] - a[1]).slice(0, k).map(([x, v]) => x + ' x' + v);
return {apply: APPLY, roots: ROOT_IDS, nodes: S.nodes, instanceNodesSkipped: S.instanceNodesSkipped, layout: S.layout, names: S.names, spacing: {bound: S.spacing.bound, offGrid: top(S.spacing.offGrid)}, errorCount: S.errors.length, errors: S.errors.slice(0, 5)};
