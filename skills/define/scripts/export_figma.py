"""Figma outputs.

1. Native variable JSON, one file per collection and mode (Figma's Import).
   Colors are color objects (colorSpace, components, alpha, hex); plain hex is skipped
   by Figma on import. Cross-collection alias handling and the exact export shape are
   NOT yet validated against a real Figma export (PRD R6).
2. Build scripts for the `use_figma` tool (the reliable path): create-or-update
   collections, modes, variables, scopes, descriptions and aliases, then text styles.
"""
import json

from color import hex_to_srgb_floats
from config import slugify
from model import FIGMA_TYPES, Alias

SCRIPT_LIMIT = 40000  # use_figma accepts 50,000 characters of code


# ------------------------------------------------------------------ native JSON
def _nest(items):
    root = {}
    for path, leaf in items:
        node = root
        *groups, name = path.split("/")
        for g in groups:
            node = node.setdefault(g, {})
        node[name] = leaf
    return root


def _native_leaf(v, mode):
    val = v.values[mode]
    if isinstance(val, Alias):
        value = "{" + val.target.replace("/", ".") + "}"
    elif v.type == "color":
        value = {"colorSpace": "srgb", "components": [round(c, 5) for c in hex_to_srgb_floats(val)],
                 "alpha": 1, "hex": val}
    else:
        value = val
    leaf = {"$type": "color" if v.type == "color" else "string" if v.type == "string" else "number",
            "$value": value, "$description": v.description,
            "$extensions": {"com.figma.scopes": v.scopes or ["ALL_SCOPES"]}}
    return leaf


def export_native_json(collections):
    """{relative filename: json text}. Easing variables are skipped (build script only)."""
    files = {}
    for col in collections:
        for mode in col.modes:
            items = [(v.path, _native_leaf(v, mode)) for v in col.variables if v.type != "easing"]
            files[f"{col.name}.{mode}.tokens.json"] = json.dumps(_nest(items), indent=2,
                                                                 ensure_ascii=False) + "\n"
    return files


# ------------------------------------------------------------------ build scripts
JS_HEADER = r"""
const typeMap = {color:'COLOR', number:'FLOAT', string:'STRING', boolean:'BOOLEAN', easing:'EASING'};
const hexToRgb = h => ({r: parseInt(h.slice(1,3),16)/255, g: parseInt(h.slice(3,5),16)/255, b: parseInt(h.slice(5,7),16)/255});
const cols = await figma.variables.getLocalVariableCollectionsAsync();
const locals = await figma.variables.getLocalVariablesAsync();
const colById = Object.fromEntries(cols.map(c => [c.id, c]));
const byKey = {};
for (const v of locals) byKey[colById[v.variableCollectionId].name + '::' + v.name] = v;
const report = {created: 0, updated: 0, errors: []};
"""

JS_VARS = r"""
for (const C of DATA.collections) {
  let col = cols.find(c => c.name === C.name);
  if (!col) { col = figma.variables.createVariableCollection(C.name); cols.push(col); }
  const modeIds = {};
  for (const name of C.modes) {
    let m = col.modes.find(x => x.name === name);
    if (!m) {
      if (col.modes.length === 1 && col.modes[0].name.startsWith('Mode ')) {
        col.renameMode(col.modes[0].modeId, name); m = col.modes[0];
      } else { col.addMode(name); m = col.modes.find(x => x.name === name); }
    }
    modeIds[name] = m.modeId;
  }
  for (const v of C.variables) {
    try {
      const key = C.name + '::' + v.path;
      let variable = byKey[key];
      if (variable) report.updated++; else { variable = figma.variables.createVariable(v.path, col, typeMap[v.type]); byKey[key] = variable; report.created++; }
      if (v.type !== 'easing') { try { variable.scopes = v.scopes; } catch (e) { report.errors.push(key + ' scopes: ' + e.message); } }
      variable.description = v.description || '';
      for (const [mode, val] of Object.entries(v.values)) {
        let value;
        if (val !== null && typeof val === 'object' && val.alias) {
          const target = byKey[val.collection + '::' + val.alias];
          if (!target) throw new Error('alias target missing: ' + val.collection + '::' + val.alias);
          value = figma.variables.createVariableAlias(target);
        } else if (v.type === 'color') value = hexToRgb(val);
        else if (v.type === 'easing') value = {type: 'CUSTOM_CUBIC_BEZIER', easingFunctionCubicBezier: {x1: val[0], y1: val[1], x2: val[2], y2: val[3]}};
        else value = val;
        variable.setValueForMode(modeIds[mode], value);
      }
    } catch (e) { report.errors.push(C.name + '::' + v.path + ': ' + e.message); }
  }
}
return report;
"""

JS_STYLES = r"""
const FONT_STYLE = {400: ['Regular'], 500: ['Medium'], 600: ['Semi Bold', 'SemiBold'], 700: ['Bold'], 800: ['Extra Bold', 'ExtraBold'], 900: ['Black', 'Heavy']};
const available = await figma.listAvailableFontsAsync();
const existing = await figma.getLocalTextStylesAsync();
const result = {styles: [], errors: []};
for (const d of DATA.styles) {
  try {
    const candidates = FONT_STYLE[d.weight] || ['Regular'];
    const found = available.find(f => f.fontName.family === d.family && candidates.includes(f.fontName.style));
    if (!found) throw new Error('font not available: ' + d.family + ' ' + candidates.join('/') + ' (install it or substitute)');
    await figma.loadFontAsync(found.fontName);
    const style = existing.find(s => s.name === d.name) || figma.createTextStyle();
    style.name = d.name;
    style.fontName = found.fontName;
    style.fontSize = d.size;
    style.lineHeight = {unit: 'PIXELS', value: d.line};
    for (const [field, key] of [['fontSize', d.bind.size], ['lineHeight', d.bind.line], ['fontFamily', d.bind.family], ['fontWeight', d.bind.weight]]) {
      const v = byKey[d.bind.collection[field] + '::' + key];
      if (!v) throw new Error('missing variable ' + key);
      style.setBoundVariable(field, v);
    }
    result.styles.push(style.id);
  } catch (e) { result.errors.push(d.name + ': ' + e.message); }
}
return result;
"""


def _alias_json(val):
    return {"alias": val.target, "collection": val.collection} if isinstance(val, Alias) else val


def _collection_json(col, variables):
    return {"name": col.name, "modes": col.modes,
            "variables": [{"path": v.path, "type": v.type, "scopes": v.scopes,
                           "description": v.description,
                           "values": {m: _alias_json(x) for m, x in v.values.items()}}
                          for v in variables]}


def _chunk(col):
    """Split a collection's variables so each script stays under SCRIPT_LIMIT."""
    chunks, cur, size = [], [], 0
    for v in col.variables:
        n = len(json.dumps(_collection_json(col, [v])))
        if cur and size + n > SCRIPT_LIMIT - 4000:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(v)
        size += n
    if cur:
        chunks.append(cur)
    return chunks


def export_build_scripts(collections, cfg):
    """{filename: JS source} for use_figma, in run order."""
    files, n = {}, 1
    for col in collections:
        chunks = _chunk(col)
        for i, vs in enumerate(chunks, 1):
            suffix = f"-part{i}" if len(chunks) > 1 else ""
            data = json.dumps({"collections": [_collection_json(col, vs)]}, ensure_ascii=False)
            files[f"{n:02d}-{slugify(col.name)}{suffix}.js"] = (
                f"// Design System Definer: {col.name} collection{suffix}. Run with use_figma.\n"
                f"const DATA = {data};\n{JS_HEADER}{JS_VARS}")
            n += 1
    styles = text_style_defs(collections, cfg)
    if styles:
        data = json.dumps({"styles": styles}, ensure_ascii=False)
        files[f"{n:02d}-text-styles.js"] = (
            "// Design System Definer: text styles bound to variables. Run after the collections.\n"
            f"const DATA = {data};\n{JS_HEADER}{JS_STYLES}")
    return files


def _find(collections, path):
    for c in collections:
        for v in c.variables:
            if v.path == path:
                return c, v
    raise KeyError(path)


def _resolve(collections, col, var):
    """Follow aliases to a literal, using each collection's first mode."""
    val = var.values[col.modes[0]]
    while isinstance(val, Alias):
        col = next(c for c in collections if c.name == val.collection)
        var = col.get(val.target)
        val = var.values[col.modes[0]]
    return val


def text_style_defs(collections, cfg):
    """Text styles bound to the canonical variables. Values come from each collection's first mode."""
    out = []
    for name, size_key, fam_role, wt_role in cfg["type"]["styles"]:
        paths = {"size": f"type/size/{size_key}", "line": f"type/line-height/{size_key}",
                 "family": f"type/family/{fam_role}", "weight": f"type/weight/{wt_role}"}
        found = {k: _find(collections, p) for k, p in paths.items()}
        vals = {k: _resolve(collections, c, v) for k, (c, v) in found.items()}
        out.append({"name": name, "size": vals["size"], "line": vals["line"], "family": vals["family"],
                    "weight": vals["weight"],
                    "bind": {**paths, "collection": {"fontSize": found["size"][0].name,
                                                     "lineHeight": found["line"][0].name,
                                                     "fontFamily": found["family"][0].name,
                                                     "fontWeight": found["weight"][0].name}}})
    return out
