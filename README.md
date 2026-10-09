# World of Flycraft

A first-person orchard toy: Sir Buzzington, a knight-fly, is driven by a two-speed “brain.”

- **FlyBrain** (`brain.js`) — local descending neurons at ~60Hz (chemotaxis, loom/escape, feeding).
- **Isaac** (optional) — slow cortex. `server.py` POSTs `/tick` with senses + a “what I see” packet; Isaac returns motor JSON.

Original world. Not that other MMO. A toy, not a mind.

## Run

From this folder:

```bash
python3 server.py
```

Then open **http://127.0.0.1:8770/** and hit **LET THE FLY PLAY**.

`server.py` expects the [claude-pokee](https://github.com/Pokee-AI/claude-pokee) checkout two directories up (for the Isaac client + `.env` key). Without Isaac, local DNs still fly; the HUD will say cortex is offline.

## Controls

- Autopilot is on by default (hungry fly selects fruit and homes in).
- **F** take the stick · **T** drop sugar · **G** loom/startle · **B** bags

## Layout

```
index.html   Three.js orchard + HUD
brain.js     local DN layer
server.py    static files + /tick
sprites/     punched PNGs
```
