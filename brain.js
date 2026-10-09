/* Local descending-neuron layer: Drosophila-like, no quest waiting. */
(function (w) {
  const N = 166700;
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  let s = {};

  function reset() {
    s = { votes: new Array(8).fill(0), r: new Array(6).fill(0), ppl: 0, phase: 0, fireCd: 0, dartT: 0, feedCd: 0 };
    syncHud();
  }
  function syncHud() {
    FlyBrain.neurons = { count: N, votes: s.votes.slice(), ppl101: s.ppl, r: s.r.slice() };
  }

  function tick(sn) {
    s.phase += 0.09;
    s.fireCd = Math.max(0, s.fireCd - 0.016);
    s.dartT = Math.max(0, s.dartT - 0.016);
    s.feedCd = Math.max(0, s.feedCd - 0.016);
    const r = [+sn.r1||0,+sn.r2||0,+sn.r3||0,+sn.r4||0,+sn.r5||0,+sn.r6||0];
    s.r = r;
    s.ppl = clamp(+sn.ppl101||0, 0, 1);
    const odorL = clamp(+sn.odorL||0, 0, 1);
    const odorR = clamp(+sn.odorR||0, 0, 1);
    const odor = Math.max(odorL, odorR, +sn.smell||0);
    const loom = clamp(+sn.loom||0, 0, 1);
    const hunger = clamp(+sn.hunger||0.6, 0, 1);
    const sugar = clamp(+sn.sugarNear||0, 0, 1);
    const hp = clamp(+sn.hp||1, 0, 1);
    const foodAng = clamp(+sn.foodAng||0, -1, 1);
    const foodDist = Math.max(0, +sn.foodDist||9);

    let forward = 0.32 + hunger * 0.2;
    let strafe = 0;
    let turn = foodAng * (1.4 + hunger * 2.4);
    let fire = 0, talk = 0, dart = 0, feed = 0;
    let fear = loom * 0.8;

    if (hunger > 0.15 && foodDist < 40) {
      turn = clamp(foodAng * 2.8, -1, 1);
      forward = Math.abs(foodAng) > 0.55 ? 0.28 : (0.62 + hunger * 0.28);
      if (foodDist < 2.2 && hunger > 0.1) { feed = 1; forward = 0.08; }
    } else if (odor > 0.08) {
      forward = 0.55 + hunger * 0.25;
      turn += (odorR - odorL) * 2.2;
    } else {
      turn += Math.sin(s.phase * 0.55) * 0.45;
      forward = 0.34;
    }
    // Giant-fiber escape on loom
    if (loom > 0.45 || (s.ppl > 0.55 && hp < 0.5)) {
      dart = 1; s.dartT = 0.32; fear = 1; forward = -0.85;
      turn += (Math.random() - 0.5) * 1.4;
    }
    if (s.dartT > 0) { dart = 1; forward = -0.7; }
    // Proboscis extension / feed
    if (sugar > 0.35 && hunger > 0.08 && s.feedCd <= 0) {
      feed = 1; fire = 1; forward = 0.04; s.feedCd = 0.7;
    }
    turn = clamp(turn + Math.sin(s.phase * 3) * 0.08, -1, 1);
    forward = clamp(forward, -1, 1);
    const targets = [
      Math.max(0, forward), Math.max(0, -forward),
      Math.max(0, (odorR-odorL)), Math.max(0, (odorL-odorR)),
      Math.max(0, turn), Math.max(0, -turn), fire, dart
    ];
    for (let i = 0; i < 8; i++) s.votes[i] = lerp(s.votes[i], targets[i], 0.3);
    syncHud();
    return { forward, strafe, turn, fire, talk, dart, fear, feed };
  }

  const FlyBrain = { reset, tick, neurons: { count: N, votes: [], ppl101: 0, r: [] } };
  reset();
  w.FlyBrain = FlyBrain;
})(window);
