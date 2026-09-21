// Balancing-Simulation: Auszahlungsquoten je Spiel/Glück/Einsatz und Erreichbarkeit der Story-Ziele.
// Lädt die echten Regelblöcke aus keller37.html (wie run-selftest.mjs) – keine Kopie der Regeln.
//
//   node tests/balance-sim.mjs            # RTP-Tabelle + Story-Läufe
//   node tests/balance-sim.mjs --rtp      # nur die RTP-Tabelle
//
// Spieler-Modelle (Abend = ein Besuch im Keller, ~40 Spins):
//   Leitplanken (Balancing 2026-09-21): nüchtern alle Tische ~97 %, mit 3 Bier ~115 %, 3 Bier lohnen sich ab ~110 € Einsatz;
//   Story 1/2 diszipliniert auf Rot ~75 %/~70 %, wild bleibt pleite.
//   diszipliniert – erst per Job Bankroll aufbauen, Einsatz ≈ 10 % der Bankroll bis LUCK_CAP, 3 Bier nur wenn
//                   sie sich bei diesem Einsatz rechnen, Stop-Loss bei −50 % des Abendstarts
//   wild          – halbe Bankroll pro Spin, kein Bier, bis null oder Ziel
// Die Prozentzahlen sind Modellwerte, keine Vorhersage – aber Vorher/Nachher bei Regeländerungen ist belastbar.
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('../keller37.html', import.meta.url), 'utf8');
const block = (id) => {
  const m = html.match(new RegExp(`<script id="${id}">([\\s\\S]*?)<\\/script>`));
  if (!m) throw new Error(`Script-Block "${id}" fehlt`);
  return m[1];
};
const ctx = { console, setTimeout, clearTimeout };
vm.createContext(ctx);
for (const id of ['rules', 'gear-rules', 'perk-rules', 'util', 'royal-rules', 'baccarat-rules']) vm.runInContext(block(id), ctx, { filename: `${id}.js` });
const Rules = vm.runInContext('Rules', ctx), RoyalRules = vm.runInContext('RoyalRules', ctx), BaccaratRules = vm.runInContext('BaccaratRules', ctx);
const seeded = (a) => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
const mods = Rules.NEUTRAL_MODS;

/* Ein Spiel = (Einsatz, wirksames Glück, rng) → Gewinn/Verlust in € */
const games = {
  slots(bet, luck, rng) { const res = Rules.slotLuckOverride(Rules.slotRoll(rng), luck, rng); return Rules.slotDelta(bet, Rules.slotMultiplier(...res, mods)); },
  rouletteRot(bet, luck, rng) { const rolled = Rules.rouletteLuckOverride('red', null, Rules.rouletteRoll(rng), luck, rng); return Rules.roulettePayout('red', null, rolled, bet, mods); },
  rouletteZahl(bet, luck, rng) { return Rules.roulettePayout('number', 17, Rules.rouletteRoll(rng), bet, mods); },
  wheel(bet, luck, rng) { const i = RoyalRules.wheelLuckOverride(RoyalRules.wheelSpin(rng), luck, rng); return RoyalRules.wheelDelta(i, bet); },
  /* Mega Seven zahlt den Großteil über Freispiele: ein bezahlter Spin inklusive der Freispiele, die er auslöst (und die diese auslösen, gedeckelt wie im Spiel) */
  mega(bet, luck, rng) {
    let free = 0, total = -bet, first = true;
    while (first || free > 0) {
      const isFree = !first; if (isFree) free--; first = false;
      const g = RoyalRules.megaLuckOverride(RoyalRules.megaRoll(rng), luck, rng);
      const w = RoyalRules.megaWin(g, bet, isFree); total += w.payout;
      if (w.freeSpins) free = Math.min(RoyalRules.MEGA.FREE_MAX, free + w.freeSpins);
    }
    return total;
  },
  crapsPass(bet, luck, rng) {
    let point = null;
    for (;;) {
      const d = RoyalRules.crapsLuckOverride(RoyalRules.crapsRoll(rng), point, true, luck, rng);
      const r = RoyalRules.crapsSettle({ pass: bet, field: 0 }, point, d); point = r.point;
      if (r.pass === 'win' || r.pass === 'lose') return r.delta;
    }
  },
  baccaratBank(bet, luck, rng) { const bets = { player: 0, banker: bet, tie: 0 }; return BaccaratRules.settle(bets, BaccaratRules.luckOverride(BaccaratRules.deal(rng), bets, luck, rng)); },
};

function rtpTable() {
  const N = 200000;
  console.log(`Auszahlungsquote in % (100 = fair). Spalten: Einsatz 100 € / ${Rules.LUCK_CAP} € / ${Rules.LUCK_CAP * 5} €. Zeilen: Glück 0 · +20 (3 Bier) · +60 (3 Bier + Brownie)`);
  console.log(`LUCK_CAP ${Rules.LUCK_CAP}, BEER_SPINS ${Rules.BEER_SPINS}, BROWNIE_SPINS ${Rules.BROWNIE_SPINS}`);
  for (const [name, fn] of Object.entries(games)) {
    const cells = [];
    for (const luck of [0, 20, 60]) {
      for (const bet of [100, Rules.LUCK_CAP, Rules.LUCK_CAP * 5]) {
        const rng = seeded(42); let sum = 0;
        for (let i = 0; i < N; i++) sum += fn(bet, Rules.effectiveLuck(luck, bet), rng);
        cells.push(((sum / N / bet + 1) * 100).toFixed(1).padStart(6));
      }
    }
    console.log(`  ${name.padEnd(13)} L0: ${cells.slice(0, 3).join(' ')}   L20: ${cells.slice(3, 6).join(' ')}   L60: ${cells.slice(6).join(' ')}`);
  }
}

/* Vorteil (Quote − 100 %) eines Spiels bei +20 Glück und Einsatz ≤ Cap – daraus folgt, ab welchem Einsatz 150 € Bier sich rechnen */
/* Vorteil von 3 Bier = Quote bei BASE_LUCK+20 minus Quote bei BASE_LUCK (in Einsätzen) */
function beerEdge(game) {
  const N = 100000; let with3 = 0, sober = 0;
  let rng = seeded(3); for (let i = 0; i < N; i++) with3 += games[game](100, Rules.BASE_LUCK + 20, rng);
  rng = seeded(3); for (let i = 0; i < N; i++) sober += games[game](100, Rules.BASE_LUCK, rng);
  return (with3 - sober) / N / 100;
}

function disciplined(rng, P) {
  const cap = Rules.LUCK_CAP, beerSpins = Rules.BEER_SPINS;
  const minBet = Math.min(cap, 150 / (beerSpins * P.edge));   // ab hier lohnt das Bier
  let bal = P.start, zero = 0;
  for (let d = 0; d < P.days; d++) {
    bal += P.job(d);
    if (d < P.gameFrom || bal < 10 * minBet) continue;        // Bankroll aufbauen
    const start = bal; let spins = 0, timer = 0;
    while (spins++ < P.spins && bal < P.target && bal > start * 0.5) {
      const bet = Math.max(minBet, Math.min(cap, Math.round(bal / 10 / 10) * 10));
      if (timer === 0) { bal -= 150; timer = beerSpins; }
      bal += games[P.game](bet, Rules.effectiveLuck(Rules.BASE_LUCK + 20, bet), rng); timer--;
    }
    if (bal < 50) zero++;
    if (bal >= P.target) return { won: true, zero, day: d + 1 };
  }
  return { won: false, zero, final: bal };
}
function wild(rng, P) {
  let bal = P.start, zero = 0;
  for (let d = 0; d < P.days; d++) {
    bal += P.job(d); let spins = 0;
    while (spins++ < P.spins && bal >= 10 && bal < P.target) { const bet = Math.max(10, Math.round(bal / 2)); bal += games[P.game](bet, Rules.effectiveLuck(Rules.BASE_LUCK, bet), rng); }
    if (bal < 50) zero++;
    if (bal >= P.target) return { won: true, zero, day: d + 1 };
  }
  return { won: false, zero, final: bal };
}
function run(name, P, strat) {
  const rng = seeded(21); let won = 0, zero = 0, days = 0; const finals = []; const N = 3000;
  for (let i = 0; i < N; i++) { const r = strat(rng, P); if (r.won) { won++; days += r.day; } else finals.push(r.final); zero += r.zero; }
  finals.sort((a, b) => a - b);
  console.log(`  ${name.padEnd(44)} Ziel ${(won / N * 100).toFixed(1).padStart(5)} %   Ø Tag ${won ? (days / won).toFixed(0).padStart(2) : ' -'}   Abende < 50 €: ${(zero / N).toFixed(1).padStart(4)}   Median-Ende (Verlierer): ${finals.length ? Math.round(finals[Math.floor(finals.length / 2)]) : '-'} €`);
}

rtpTable();
if (!process.argv.includes('--rtp')) {
  const rot = beerEdge('rouletteRot'), slots = beerEdge('slots');
  console.log(`\nVorteil von 3 Bier (Grundglück ${Rules.BASE_LUCK}): Roulette Rot ${(rot * 100).toFixed(1)} %, Slots ${(slots * 100).toFixed(1)} % → 3 Bier (150 €) rechnen sich ab ${(150 / (Rules.BEER_SPINS * rot)).toFixed(0)} € (Rot) bzw. ${(150 / (Rules.BEER_SPINS * slots)).toFixed(0)} € (Slots) Einsatz`);
  /* Story 1: 50 € Start, 30 Tage, Jobs ~100 €/Tag (Spüler/Post), ab Tag 6 Roulette und Taxi (~220 €/Tag). Ziel: 50.000 € für Vito („ehrlich"). */
  const s1 = { start: 50, days: 30, target: 50000, job: (d) => (d < 6 ? 100 : 220), spins: 40 };
  /* Story 2: ab Tag 4 bei 0 €, 26 Abende, Jobs ~180 €/Tag, Roulette offen. Ziel: 40.000 € + Deckel („Der Wirt"). */
  const s2 = { start: 0, days: 26, target: 40000, job: () => 180, spins: 40 };
  console.log('\nStory 1 „Die Schuld" – 50.000 € für Vito in 30 Tagen (Roulette ab Tag 6):');
  run('diszipliniert, Roulette Rot, 40 Spins/Abend', { ...s1, game: 'rouletteRot', edge: rot, gameFrom: 5 }, disciplined);
  run('diszipliniert, Roulette Rot, 80 Spins/Abend', { ...s1, game: 'rouletteRot', edge: rot, gameFrom: 5, spins: 80 }, disciplined);
  run('diszipliniert, nur Slots', { ...s1, game: 'slots', edge: slots, gameFrom: 0 }, disciplined);
  run('wild, Slots', { ...s1, game: 'slots' }, wild);
  console.log('\nStory 2 „Der Kater" – 40.000 € in 26 Abenden:');
  run('diszipliniert, Roulette Rot, 40 Spins/Abend', { ...s2, game: 'rouletteRot', edge: rot, gameFrom: 0 }, disciplined);
  run('diszipliniert, Roulette Rot, 80 Spins/Abend', { ...s2, game: 'rouletteRot', edge: rot, gameFrom: 0, spins: 80 }, disciplined);
  run('diszipliniert, nur Slots', { ...s2, game: 'slots', edge: slots, gameFrom: 0 }, disciplined);
  run('wild, Glücksrad', { ...s2, game: 'wheel' }, wild);
  console.log('\nZwischenziele: 15.000 € (Chantal, Story 2) und 8.000 € (Flucht, Story 1), diszipliniert Rot:');
  run('Story 2 → 15.000 €', { ...s2, target: 15000, game: 'rouletteRot', edge: rot, gameFrom: 0 }, disciplined);
  run('Story 1 → 8.000 €', { ...s1, target: 8000, game: 'rouletteRot', edge: rot, gameFrom: 5 }, disciplined);
}
