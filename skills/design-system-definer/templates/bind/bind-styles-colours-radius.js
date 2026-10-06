// ---- bind existing layers to text styles, colour variables and radius variables ----
const styles = Object.fromEntries((await figma.getLocalTextStylesAsync()).map(s => [s.name, s]));
const localIds = new Set(Object.values(styles).map(s => s.id));
for (const s of Object.values(styles)) { try { await figma.loadFontAsync(s.fontName); } catch (e) {} }
const STY = CONFIG.styles.filter(s => styles[s.name]).map(s => ({...s, wc: s.weight >= 600 ? 'strong' : 'regular'}));
const UI = CONFIG.uiFamily;
const wOf = s => { s = s.replace(/\s/g, '').toLowerCase(); if (s.includes('italic')) return -1; if (s.includes('thin') || s.includes('extralight') || s.includes('light')) return 300;
  if (s.includes('semibold')) return 600; if (s.includes('extrabold') || s.includes('black')) return 800; if (s.includes('bold')) return 700; if (s.includes('medium')) return 500; return 400; };
const near = (sz, pool) => pool.reduce((a, x) => Math.abs(x.size - sz) < Math.abs(a.size - sz) || (Math.abs(x.size - sz) === Math.abs(a.size - sz) && x.size > a.size) ? x : a, pool[0]);
// pick the style that matches font family role, weight class and nearest size; report why a layer is skipped
const styleFor = (fam, fs, sz, len) => {
  const w = wOf(fs); if (w < 0) return {skip: 'italic'}; if (sz > 72) return {skip: 'oversize'};
  const ui = !!UI && fam === UI && sz <= 17.5;
  const wc = w >= 600 || (w === 500 && sz < 17 && len <= 40) ? 'strong' : 'regular';
  let pool;
  if (ui) pool = STY.filter(s => s.role === 'ui');
  else if (sz >= 17) pool = STY.filter(s => s.role !== 'ui' && s.size >= 17 && s.wc === wc);
  else { pool = STY.filter(s => s.role !== 'ui' && s.size < 17 && s.wc === wc); if (!pool.length) pool = STY.filter(s => s.role !== 'ui' && s.size < 17); }
  if (!pool.length) return {skip: sz >= 17 && wc === 'regular' ? 'regular-heading' : 'no-style'};
  const t = near(ui ? sz : (sz < 17 ? Math.max(sz, 12) : sz), pool);
  if (sz >= 17 && Math.abs(t.size - sz) > (sz >= 40 ? 8 : 4)) return {skip: 'big-shift'};
  return {name: t.name};
};
const hintOf = n => { const s = n.name.toLowerCase(); return /button|btn|cta/.test(s) ? 'button' : /input|field|search|select/.test(s) ? 'field' : /card|tile|panel/.test(s) ? 'card' : /check/.test(s) ? 'control' : ''; };
const S = {nodes: 0, instanceNodesSkipped: 0, text: {seen: 0, styled: 0, alreadyStyled: 0, hugged: 0, skipped: {}}, tcol: {bound: 0, onBrand: 0}, fill: {bound: 0, unbound: {}}, stroke: {bound: 0, unbound: {}}, radius: {bound: 0, unbound: {}}, errors: []};
const targets = await collect(ROOT_IDS);
const R = CONFIG.radius;
for (const [n, inInst] of targets) {
  S.nodes++;
  if (inInst) { S.instanceNodesSkipped++; continue; }
  if (n.type === 'SECTION') continue;
  try {
    if (n.type === 'TEXT') {
      S.text.seen++;
      const segs = n.getStyledTextSegments(['fontName', 'fontSize', 'fills', 'textStyleId', 'textCase', 'textDecoration']);
      for (const g of segs) await figma.loadFontAsync(g.fontName);
      if (segs.every(g => localIds.has(g.textStyleId))) S.text.alreadyStyled++;
      else if (segs.some(g => (g.textCase && g.textCase !== 'ORIGINAL') || (g.textDecoration && g.textDecoration !== 'NONE'))) bump(S.text.skipped, 'case/decoration'); // a style would reset case or underline
      else {
        const plan = segs.map(g => styleFor(g.fontName.family, g.fontName.style, g.fontSize, g.characters.length));
        if (!plan.every(p => p.name)) { for (const p of plan) if (p.skip) bump(S.text.skipped, p.skip); }
        else if (APPLY) {
          const w0 = n.width, h0 = n.height, mode = n.textAutoResize, align = n.textAlignHorizontal;
          const lh0 = n.lineHeight && n.lineHeight !== figma.mixed && n.lineHeight.unit === 'PIXELS' ? n.lineHeight.value : segs[0].fontSize * 1.3;
          const single = h0 <= lh0 * 1.5 + 1 && !n.characters.includes('\n');
          // note: do not restore letter spacing afterwards; setting it detaches the style
          if (new Set(plan.map(p => p.name)).size === 1 && segs.length === 1) await n.setTextStyleIdAsync(styles[plan[0].name].id);
          else for (let i = 0; i < segs.length; i++) await n.setRangeTextStyleIdAsync(segs[i].start, segs[i].end, styles[plan[i].name].id);
          S.text.styled++;
          if (single && mode !== 'WIDTH_AND_HEIGHT') { // a one-line label that no longer fits its fixed width: let it hug
            n.textAutoResize = 'WIDTH_AND_HEIGHT';
            if (n.width <= w0 + 0.5) { n.textAutoResize = mode; n.resize(w0, h0); }
            else { S.text.hugged++; const dw = n.width - w0; const par = n.parent; const autoPar = par && 'layoutMode' in par && par.layoutMode !== 'NONE';
              if (!autoPar) { if (align === 'RIGHT') n.x -= dw; else if (align === 'CENTER') n.x -= dw / 2; } }
          }
        } else S.text.styled++;
      }
      // text colour
      const segc = n.getStyledTextSegments(['fills']);
      if (segc.some(g => { const p = g.fills && g.fills[0]; return p && p.type === 'SOLID' && p.visible !== false && !isBound(p); })) {
        const bg = bgOf(n);
        const dec = segc.map(g => { const p = g.fills && g.fills[0]; if (!p || p.type !== 'SOLID' || p.visible === false || isBound(p)) return {keep: true}; const m = pickText(p.color, bg); return m ? {m, p} : {miss: true}; });
        if (dec.some(d => d.m) && APPLY) {
          if (segc.length === 1 && dec[0].m) setPaints(n, 'fills', [bindPaint(dec[0].p, dec[0].m.k)], [opOf(dec[0].p)]);
          else for (let i = 0; i < segc.length; i++) { const d = dec[i]; if (!d.m) continue; const s = segc[i].start, e = segc[i].end; n.setRangeFills(s, e, [bindPaint(d.p, d.m.k)]);
            if (opOf(d.p) < 1) { const rf = JSON.parse(JSON.stringify(n.getRangeFills(s, e))); rf[0].opacity = opOf(d.p); n.setRangeFills(s, e, rf); } }
        }
        for (const d of dec) if (d.m) { S.tcol.bound++; if (d.m.fix) S.tcol.onBrand++; }
      }
      continue;
    }
    const isIcon = ['VECTOR', 'BOOLEAN_OPERATION', 'STAR', 'POLYGON', 'LINE'].includes(n.type);
    const thin = 'width' in n && Math.min(n.width, n.height) <= 2;
    const hint = hintOf(n);
    if ('fills' in n && Array.isArray(n.fills) && n.fills.length) {
      let changed = false; const ops = n.fills.map(opOf);
      const nf = n.fills.map(p => { if (p.type !== 'SOLID' || p.visible === false || isBound(p)) return p;
        const m = pickColor(p.color, thin ? C_STROKE : (isIcon ? C_ICON : C_FILL), hint);
        if (!m) { bump(S.fill.unbound, toHex(p.color)); return p; } S.fill.bound++; changed = true; return bindPaint(p, m.k); });
      if (changed && APPLY) { if (n.fillStyleId) await n.setFillStyleIdAsync(''); setPaints(n, 'fills', nf, ops); }
    }
    if ('strokes' in n && Array.isArray(n.strokes) && n.strokes.length) {
      let changed = false; const ops = n.strokes.map(opOf);
      const ns = n.strokes.map(p => { if (p.type !== 'SOLID' || p.visible === false || isBound(p)) return p;
        const m = pickColor(p.color, C_STROKE, hint);
        if (!m) { bump(S.stroke.unbound, toHex(p.color)); return p; } S.stroke.bound++; changed = true; return bindPaint(p, m.k); });
      if (changed && APPLY) { if (n.strokeStyleId) await n.setStrokeStyleIdAsync(''); setPaints(n, 'strokes', ns, ops); }
    }
    if ('cornerRadius' in n && typeof n.cornerRadius === 'number' && n.cornerRadius > 0 && n.type !== 'ELLIPSE') {
      const r = n.cornerRadius, m = Math.min(n.width, n.height); let key = null;
      if (r >= 9999 || (m >= 8 && r >= m / 2 - 0.5)) key = R.round;
      else if (R.prim[String(r)]) { key = R.prim[String(r)];
        if (hint === 'field' && R.field && R.fieldValue === r) key = R.field; else if (hint === 'button' && R.button && R.buttonValue === r) key = R.button;
        else if ((hint === 'card' || n.width >= 160) && R.card && R.cardValue === r) key = R.card; else if (hint === 'control' && R.control && R.controlValue === r) key = R.control; }
      if (key && V[key]) { S.radius.bound++; if (APPLY) for (const f of ['topLeftRadius', 'topRightRadius', 'bottomLeftRadius', 'bottomRightRadius']) n.setBoundVariable(f, V[key]); }
      else bump(S.radius.unbound, String(r));
    }
  } catch (e) { S.errors.push(n.id + ' ' + n.type + ': ' + String(e.message).slice(0, 80)); }
}
const top = (o, k = 10) => Object.entries(o).sort((a, c) => c[1] - a[1]).slice(0, k).map(([x, v]) => x + ' x' + v);
return {apply: APPLY, roots: ROOT_IDS, nodes: S.nodes, instanceNodesSkipped: S.instanceNodesSkipped,
  text: {seen: S.text.seen, styled: S.text.styled, alreadyStyled: S.text.alreadyStyled, hugged: S.text.hugged, skipped: S.text.skipped},
  textColour: {bound: S.tcol.bound, onBrandFixed: S.tcol.onBrand},
  fills: {bound: S.fill.bound, unbound: top(S.fill.unbound)}, strokes: {bound: S.stroke.bound, unbound: top(S.stroke.unbound)},
  radius: {bound: S.radius.bound, unbound: top(S.radius.unbound)}, errorCount: S.errors.length, errors: S.errors.slice(0, 5)};
