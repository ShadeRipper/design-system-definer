// ---- audit: read-only coverage report. Run before (to see the gap) and after (to prove the result) ----
const localStyleIds = new Set((await figma.getLocalTextStylesAsync()).map(s => s.id));
const A = {nodes: 0, inInstance: 0, text: {n: 0, styled: 0, partial: 0, unstyled: 0, colourBound: 0, colourRaw: 0, missingFont: 0},
  fills: {bound: 0, raw: 0}, strokes: {bound: 0, raw: 0}, radius: {bound: 0, raw: 0}, spacing: {bound: 0, raw: 0},
  frames: {n: 0, autoLayout: 0}, groups: 0, genericNames: 0, rawTextColours: {}, rawFillColours: {}, rawRadius: {}, rawSpacing: {}};
const GENERIC = /^(Frame|Group|Rectangle|Ellipse|Vector|Line|Polygon|Star|Container|Component|Boolean|Subtract|Union|Intersect|Exclude|Image|Mask)\s*\d*$|^(div|span|a|p|img|svg|ul|li|ol|h[1-6]|section|nav|header|footer|main|label|input|path|g|form|aside|article|button)(\.[\w-]+)*\s*\d*$/i;
const all = await collect(ROOT_IDS);
for (const [n, inInst] of all) {
  A.nodes++;
  if (inInst) { A.inInstance++; continue; }
  if (n.type === 'TEXT') {
    A.text.n++; let segs;
    try { segs = n.getStyledTextSegments(['textStyleId', 'fills']); } catch (e) { A.text.missingFont++; continue; }
    const loc = segs.filter(g => localStyleIds.has(g.textStyleId)).length;
    if (loc === segs.length) A.text.styled++; else if (loc > 0) A.text.partial++; else A.text.unstyled++;
    for (const g of segs) { const p = g.fills && g.fills[0]; if (p && p.type === 'SOLID') { if (isBound(p)) A.text.colourBound++; else { A.text.colourRaw++; bump(A.rawTextColours, toHex(p.color)); } } }
    continue;
  }
  if ('fills' in n && Array.isArray(n.fills)) for (const p of n.fills) if (p.type === 'SOLID' && p.visible !== false) { if (isBound(p)) A.fills.bound++; else { A.fills.raw++; bump(A.rawFillColours, toHex(p.color)); } }
  if ('strokes' in n && Array.isArray(n.strokes)) for (const p of n.strokes) if (p.type === 'SOLID' && p.visible !== false) { if (isBound(p)) A.strokes.bound++; else A.strokes.raw++; }
  if ('cornerRadius' in n && typeof n.cornerRadius === 'number' && n.cornerRadius > 0 && n.type !== 'ELLIPSE') { if (n.boundVariables && n.boundVariables.topLeftRadius) A.radius.bound++; else { A.radius.raw++; bump(A.rawRadius, String(n.cornerRadius)); } }
  if (n.type === 'FRAME') {
    A.frames.n++;
    if (n.layoutMode && n.layoutMode !== 'NONE') { A.frames.autoLayout++;
      for (const f of ['itemSpacing', 'paddingLeft', 'paddingRight', 'paddingTop', 'paddingBottom']) { const v = n[f]; if (typeof v === 'number' && v > 0) { if (n.boundVariables && n.boundVariables[f]) A.spacing.bound++; else { A.spacing.raw++; bump(A.rawSpacing, String(Math.round(v * 10) / 10)); } } } }
  }
  if (n.type === 'GROUP') A.groups++;
  if (!['SECTION', 'INSTANCE'].includes(n.type) && GENERIC.test(n.name)) A.genericNames++;
}
const top = (o, k = 8) => Object.entries(o).sort((a, c) => c[1] - a[1]).slice(0, k).map(([x, v]) => x + ' x' + v);
const pct = (a, b) => b ? Math.round(a / b * 1000) / 10 + '%' : 'n/a';
return {roots: ROOT_IDS, nodes: A.nodes, inInstanceSkipped: A.inInstance,
  coverage: {textStyled: pct(A.text.styled, A.text.n), textColourBound: pct(A.text.colourBound, A.text.colourBound + A.text.colourRaw), fillsBound: pct(A.fills.bound, A.fills.bound + A.fills.raw),
    strokesBound: pct(A.strokes.bound, A.strokes.bound + A.strokes.raw), radiusBound: pct(A.radius.bound, A.radius.bound + A.radius.raw),
    spacingBound: pct(A.spacing.bound, A.spacing.bound + A.spacing.raw), autoLayoutFrames: pct(A.frames.autoLayout, A.frames.n)},
  counts: {text: A.text, fills: A.fills, strokes: A.strokes, radius: A.radius, spacing: A.spacing, frames: A.frames, groups: A.groups, genericNames: A.genericNames},
  topUnbound: {textColours: top(A.rawTextColours), fillColours: top(A.rawFillColours), radius: top(A.rawRadius), spacing: top(A.rawSpacing)}};
