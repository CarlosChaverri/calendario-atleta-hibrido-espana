// Extrae window.__NUXT__ de una pagina HTML de Runnea y vuelca el JSON por stdout
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
let i = html.indexOf('window.__NUXT__=');
if (i < 0) i = html.indexOf('__NUXT__=');
if (i < 0) { console.log('null'); process.exit(0); }
let start = html.indexOf('=', i) + 1;
let end = html.indexOf('</script>', start);
let code = html.slice(start, end).trim().replace(/;$/, '');
try {
  const data = eval('(' + code + ')');
  const out = { lists: [] };
  if (data && data.state && data.state.lists) {
    for (const k of Object.keys(data.state.lists)) {
      const l = data.state.lists[k];
      if (l && Array.isArray(l.contents)) out.lists.push({ total: l.total, contents: l.contents });
    }
  }
  console.log(JSON.stringify(out));
} catch (e) {
  console.error('parse error: ' + e.message);
  console.log('null');
}
