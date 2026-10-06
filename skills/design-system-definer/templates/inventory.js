// Design System Definer: inventory of an existing Figma file. READ-ONLY. Run it through use_figma BEFORE the interview's lever stage.
// It tallies the fonts, sizes, colours, radii and spacing the screens really use, so the interview starts from evidence, not memory.
// No config is needed: this runs before one exists.
const PAGE_ID = 'REPLACE_WITH_PAGE_ID';        // the page that holds the screens
const ROOT_IDS = ['REPLACE_WITH_FRAME_ID'];    // frames or sections to read (a few thousand layers per call)
const _page = figma.root.children.find(p => p.id === PAGE_ID);
if (!_page) return {error: 'PAGE_ID not found in this file: ' + PAGE_ID};
await figma.setCurrentPageAsync(_page);
const bump = (o, k, n = 1) => { o[k] = (o[k] || 0) + n; };
const toHex = c => '#' + [c.r, c.g, c.b].map(x => Math.round(x * 255).toString(16).padStart(2, '0')).join('');
const walk = (n, out, inInst) => { out.push([n, inInst]); if ('children' in n) { const ni = inInst || n.type === 'INSTANCE'; for (const c of n.children) { if (c.visible === false) continue; walk(c, out, ni); } } };
const collect = async ids => { const out = []; for (const id of ids) { const r = await figma.getNodeByIdAsync(id); walk(r, out, false); } return out; };
// ---- inventory: read-only. What does this file actually use? Run BEFORE the interview's lever stage ----
// Tallies fonts, sizes, colours (weighted by area), radii and spacing so the interview starts from evidence.
const I = {nodes: 0, inInstance: 0, frames: {}, fonts: {}, textPairs: {}, fills: {}, fillArea: {}, strokes: {}, textColours: {}, radius: {}, spacing: {}, autoLayout: 0, frameCount: 0};
const all = await collect(ROOT_IDS);
for (const [n, inInst] of all) {
  I.nodes++;
  if (inInst) { I.inInstance++; continue; }
  if (n.type === 'TEXT') {
    let segs; try { segs = n.getStyledTextSegments(['fontName', 'fontSize', 'fills', 'textStyleId']); } catch (e) { bump(I.fonts, 'unloadable font'); continue; }
    for (const g of segs) {
      bump(I.fonts, g.fontName.family); bump(I.textPairs, g.fontName.family + '|' + g.fontName.style + '|' + Math.round(g.fontSize * 10) / 10);
      const p = g.fills && g.fills[0]; if (p && p.type === 'SOLID') bump(I.textColours, toHex(p.color));
    }
    continue;
  }
  if ('fills' in n && Array.isArray(n.fills)) for (const p of n.fills) if (p.type === 'SOLID' && p.visible !== false) { const h = toHex(p.color) + (p.opacity !== undefined && p.opacity < 1 ? '@' + p.opacity.toFixed(2) : ''); bump(I.fills, h); I.fillArea[h] = (I.fillArea[h] || 0) + ('width' in n ? n.width * n.height : 0); }
  if ('strokes' in n && Array.isArray(n.strokes)) for (const p of n.strokes) if (p.type === 'SOLID' && p.visible !== false) bump(I.strokes, toHex(p.color));
  if ('cornerRadius' in n && typeof n.cornerRadius === 'number' && n.cornerRadius > 0 && n.type !== 'ELLIPSE') bump(I.radius, String(n.cornerRadius));
  if (n.type === 'FRAME') {
    I.frameCount++;
    if (n.parent && (n.parent.type === 'SECTION' || n.parent.type === 'PAGE')) bump(I.frames, Math.round(n.width) + ' wide');
    if (n.layoutMode && n.layoutMode !== 'NONE') { I.autoLayout++; for (const f of ['itemSpacing', 'paddingLeft', 'paddingTop']) { const v = n[f]; if (typeof v === 'number' && v > 0) bump(I.spacing, String(Math.round(v * 10) / 10)); } }
  }
}
const top = (o, k = 14) => Object.entries(o).sort((a, c) => c[1] - a[1]).slice(0, k).map(([x, v]) => x + ' x' + v);
const topArea = o => Object.entries(o).sort((a, c) => c[1] - a[1]).slice(0, 10).map(([x, v]) => x + ' ' + Math.round(v / 1000) + 'k');
return {roots: ROOT_IDS, nodes: I.nodes, inInstanceSkipped: I.inInstance, topLevelFrameWidths: top(I.frames, 6), fontFamilies: top(I.fonts, 8),
  fontSizeWeight: top(I.textPairs, 30), textColours: top(I.textColours), fillColours: top(I.fills), fillColoursByArea: topArea(I.fillArea),
  strokeColours: top(I.strokes), radius: top(I.radius, 12), spacing: top(I.spacing, 12), autoLayoutShare: I.frameCount ? Math.round(I.autoLayout / I.frameCount * 1000) / 10 + '%' : 'n/a'};
