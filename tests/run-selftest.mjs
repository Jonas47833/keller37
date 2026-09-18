// Führt SelfTest.run() aus keller37.html unter Node aus.
// Lädt nur die DOM-freien Script-Blöcke: rules, state, bus, util, selftest.
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('../keller37.html', import.meta.url), 'utf8');
const block = (id) => {
  const m = html.match(new RegExp(`<script id="${id}">([\\s\\S]*?)<\\/script>`));
  if (!m) throw new Error(`Script-Block "${id}" fehlt`);
  return m[1];
};
const storage = {
  data: {},
  getItem(k) { return k in this.data ? this.data[k] : null; },
  setItem(k, v) { this.data[k] = String(v); },
  removeItem(k) { delete this.data[k]; },
  clear() { this.data = {}; },
};
const ctx = { console, localStorage: storage, setTimeout, clearTimeout };
vm.createContext(ctx);
for (const id of ['rules', 'gear-rules', 'perk-rules', 'util', 'state', 'bus', 'story-rules', 'royal-rules', 'baccarat-rules', 'gang-rules', 'story-probe', 'story-schuld', 'story-kater', 'story-stash', 'selftest']) {
  if (!html.includes(`<script id="${id}">`)) continue; // state/bus kommen erst in Task 4
  vm.runInContext(block(id), ctx, { filename: `${id}.js` });
}
const r = await vm.runInContext('SelfTest.run()', ctx); // run() ist async (Browser-Tests dürfen awaiten)
for (const f of r.failures) console.error('FAIL', f);
console.log(`${r.passed} bestanden, ${r.failed} fehlgeschlagen`);
process.exit(r.failed ? 1 : 0);
