# GASLIGHT & INK — Game Research & Design Document

*A Roblox anime action RPG inspired by Bungo Stray Dogs: people with powers drawn from great literature fight over a fog-choked 1891 London. Detective guilds, river syndicates, and a secret Crown bureau battle in the gaslight.*

Research date: 2026-11-01 · Revision 2 · Status: pre-production

---

## 0. TL;DR

| Item | Decision |
|---|---|
| Genre | Solo-first anime action RPG ("spin-RPG": Gakuran, Type Soul, Jujutsu Infinite, AoT Revolution) with optional PvP, PvE dungeons/raids, and factions |
| Hook | Your power is a **Manuscript**, an ability based on a classic public-domain book (*Dracula, Frankenstein, The Raven, Moby-Dick…*). You roll it, master it, and can reroll it. |
| Setting | **London, 1891.** Gaslamps, volumetric fog, wet cobblestones, hansom cabs, the steam Underground, and an unfinished Tower Bridge. Realistic lighting, anime combat. |
| Target | Ages 16–22. Ships as **13+** on Roblox (§3). |
| Monetization | Odds-disclosed spins with pity and a **Binding Thread** spark system, Lock slots, game passes, a **Society Membership** subscription, a battle pass, cosmetics, and rewarded video. Everything that affects power can be earned for free. |
| Session design | Nested loops: 30 s fights → 5 min cases → 25 min arcs/dungeons → a night event each Big-Bell cycle → daily/weekly/seasonal goals. Target sessions run 45–120 min. |
| AI NPCs | Roblox `TextGenerator`: free-text witness interrogation, faction leaders with memory, and a daily newspaper (*The Penny Ledger*) generated from that server's events. |
| Unit economics | Modeled lifetime ≈ **9 active days per install** → LTV ≈ **R$45 gross / ~$0.12 net DevEx per install** at R$5 ARPDAU. Growth must come from organic/algorithm reach, not paid installs (§11.5). |

---

## 1. Market Research

### 1.1 Roblox in 2026
- **Scale:** about 123 M DAU in Q2 2026; platform concurrency has topped 12 M.
- **Age mix (age-checked users, H1 2026):** 35 % under 13 · **38 % 13–17** · **27 % 18+**. Only part of DAU is age-checked, so this is a subset. Earlier self-reported data (2024) showed 17–24 as the largest bracket (25 %).
- **Adults are the fastest-growing group.** In April 2026 Roblox raised the DevEx rate **+42 %** for qualifying spend by age-verified US players 18+, explicitly to encourage high-fidelity games for older players.
- **Anime dominates the charts.** Weekly chart write-ups through August 2026 show anime titles in most top spots, and new anime seasons send waves of players to the matching Roblox games.

**What this means:** ages 16–22 sit where the largest age-checked group (13–17) meets the fastest-growing one (18+). A realistic-looking, "mature but 13+" game reaches both groups, and the 18+ US share earns up to 42 % more per Robux.

### 1.2 Competitor teardown (live data, Nov 2026)

> Revenue figures are **third-party estimates** (profitable.app/RoWatcher models built from visits and assumed spend), not reported earnings. CCU numbers depend heavily on when they were measured.

#### Gakuran (学乱): the closest comparable
| Metric | Value |
|---|---|
| Release | 19 Nov 2025 (under 1 year old) |
| Visits | **282.6 M** |
| CCU (1 Nov 2026) | 13.9 K (rank ~#109) |
| Peak CCU | 67.4 K (profitable.app) · RoWatcher reports a **144 K peak on 15 Aug 2026** |
| Like ratio | **89 %** (506 K / 65 K) |
| Favorites | 762.8 K |
| Est. revenue | **~$2.3 M lifetime, ~$203 K last 30 days** |
| Server size | 50 players |
| Trajectory | Spiked +165 % WoW to ~35 K in early Sept 2026 (3.2× algorithm spike), then fell ~32 % over 30 days |

**What it does:** a school-brawler with rerolls for fighting style, appearance, and uniform. It grows through codes (10–30 rerolls each), gates code rewards behind joining the group (some guides say you also need 5+ friends), and sells Robux reroll bundles. It has spun off related games (Basketball 2, Testing Grounds).

**Lessons:**
1. **Rerolling non-power slots (looks, uniform) is a big revenue line in itself.** We copy it with a Look slot and Attire spins.
2. **Codes and group-joins are the growth engine.** Coverage appears in many languages (EN, ES, PL, TR, VI, ZH) with almost no marketing spend.
3. **There is no earnable reroll currency.** It was only "planned", which is the #1 complaint. We ship one on day 1.
4. **Spikes fade without content.** The 144 K → 14 K decline is the cost of slow updates. Our answer is a 2-week cadence (§13).
5. Small team, under 1 year, ~$2.3 M est.: this is the realistic upside for a well-executed indie spin-RPG.

#### Type Soul (Bleach)
- **Rerolls are the entire progression system.** Codes give rerolls for race, clan, and Shikai/Res/Volt, including **"locked" rerolls** (a reroll that keeps a chosen attribute).
- A full race reroll needs a **Soul Ticket, which wipes all progress**. That's high stakes, and players dislike it.
- Weapons and special items are sold for Robux. A 2026 "Relaunch" update reworked content after a decline.
- **Lessons:** "locked reroll" is a proven product, and ours becomes Lock slots plus a "Lock-a-Trait" reroll. Never wipe progress on reroll; it's one of the main reasons players quit.

#### Jujutsu Infinite
- ~4.0–4.4 K CCU mid-2026 (third-party). Innate techniques are rolled with **Spins**.
- Codes give **100 spins** each; daily login gives spins on days 3/8/13.
- **Lesson:** spin inflation. When codes hand out 100 spins, each paid spin is worth little. **We value spins high and give few of them** (codes give 10–30, never 100). Codes should feel generous without making the paid shop pointless.

#### Attack on Titan Revolution
- **748 M visits, 96 % like ratio, ~14.8 K CCU.** Estimated six figures per month from spins and progression items.
- **Lesson:** a 96 % like ratio shows heavy spin monetization is accepted **when the core combat is excellent.** Combat feel comes first; monetization sits on top.

#### Deepwoken
- Permadeath roguelite RPG and a genre benchmark for lore and difficulty. Public bug-tracker threads show **community backlash over the "restore" (character recovery) system** and lag-caused wipes.
- **Lesson:** never charge for recovering from a loss. Players hate paying to undo bad luck. Our losses are small (Ink, bounty), and "insurance" is never sold.

#### Shindo Life
- The original bloodline-spin template; collapsed to ~1–2 K CCU from power creep and stale updates.
- **Lesson:** schedule power resets (seasonal ranked) and keep new rarities from making old ones obsolete.

#### Blox Fruits (scale reference)
- 58 B+ visits. One blog estimates $8–12 M/month (unverified). It shows how far "roll a power, then grind" can scale on Roblox.

### 1.3 Gap in the market
No top-100 Roblox game owns **literary powers + detective noir + Victorian gothic.** Spin RPGs are almost all shonen-IP fighters (Naruto, Bleach, JJK, One Piece, AoT). Victorian London adds a gothic-horror tone (Dracula, Jekyll, the Ripper-era fog) that 16–22-year-olds like (dark academia, gothic aesthetics, steampunk) and that looks great in short clips.

---

## 2. IP & Legal Positioning

Bungo Stray Dogs is copyrighted (Kafka Asagiri / Sango Harukawa / Kadokawa / Bones). Anime publishers do file DMCA takedowns on Roblox.

1. **Don't use** BSD characters, names, likenesses, art, music, organization names (Armed Detective Agency, Port Mafia, Guild), or BSD's specific ability designs.
2. **Use** the unprotectable *idea*: literature-based superpowers, rival organizations, detective work.
3. **All Manuscripts are based on public-domain works** (pre-1929 publication; works by Victorian/Edwardian authors are long PD). The abilities are our own designs.
4. **Overlap rule:** where BSD also uses a work (e.g. *Moby-Dick*, *Frankenstein*), our ability must be visibly different in mechanics, visuals, and name, with no echoes of BSD poses or quotes. The overlaps are marked ⚑ in §6.2. The legal team (or a careful review) signs off on each.
5. **Real history:** Whitechapel is a setting, but **no Jack the Ripper victims or real murders** are depicted. Real crimes against real women aren't content. Fictional cases only.
6. Marketing can say "for fans of literary-ability anime". BSD stays out of the title, thumbnail, and description.

---

## 3. Audience & Platform Constraints

### 3.1 Content rating
- **13+ (Moderate):** fantasy violence, gothic horror tone, crime themes, no realistic gore. Smuggling, not drugs. No alcohol focus (taverns serve "tea and cocoa" jokes).
- **Not 17+:** 17+/Restricted experiences are hidden from anyone not age-verified as 17+, which would cut off most 16–22-year-olds, and they are unavailable in some countries.

### 3.2 Chat
Age checks are required for experience chat, voice, and friends (global since Jan 2026). **Everything must work without chat:** emotes, ping wheel, party invites, trade UI, quick-reply buttons for AI NPCs.

### 3.3 Paid random items — compliance checklist
Roblox's policy (tightened globally in 2026 following South Korea's law) covers any random outcome bought **directly or indirectly** with Robux (tokens, tickets, shards bought with Robux):

- [ ] Every outcome and its % odds shown before purchase; odds add up to exactly **100 %**.
- [ ] Luck boosts explained before purchase; **displayed odds update live** while active.
- [ ] `PolicyService:GetPolicyInfoForPlayerAsync()` checked per player. If `ArePaidRandomItemsRestricted`, paid spins are disabled and the player gets an earn-only path plus the fixed-price **Bindery** (§6.4).
- [ ] Paid and free spins on a banner use identical odds.
- [ ] Pity counters shown on screen.
- [ ] Every roll logged server-side (support and audit).

---

## 4. Setting & World

### 4.1 Premise
**London, 1891.** Since the "Great Ink Fog" of 1888, a few Londoners (the **Inkbound**) wake with a power shaped by a book that marked their soul. Four powers contend for the city:

| Faction | Fantasy | Perks | Leader NPC (LLM persona) |
|---|---|---|---|
| **The Inkwell Society** (private detective guild, above a Strand bookshop) | Solve cases, protect the innocent, wit plus fists | +15 % case rewards, interrogation hints, PvE damage | *Mrs. Augusta Vane*, sharp-tongued widow and master deductionist |
| **The Black Thames** (river syndicate) | Rule the docks, run contraband, fear and loyalty | Territory income, PvP bounty bonus, smuggling runs | *"The Ferryman"*, silent, masked, speaks through a child courier |
| **The Crown Bindery** (secret government bureau that registers the Inkbound) | Order at any cost; morally gray | Rare-material access, Bindery reputation discounts, raid buffs | *Sir Edmund Hale*, charming spymaster who lies a lot |
| *Penny Dreadfuls* (freelancers) | Lone wolf; works for anyone | Flexible contracts, no defection penalty | — |

Defecting triggers a short story arc and a 24 h bounty. Faction choice changes your story chapters, hub, and missions.

### 4.2 Districts (streamed, ~2.5 km² total)
| District | Look & feel | Gameplay role |
|---|---|---|
| **The Strand & Fleet Street** | Bookshops, newspaper presses, omnibuses, newsboys | Main hub; PvP off; Society HQ; shop; banner hall ("The Reading Room") |
| **Whitechapel & Spitalfields** | Narrow alleys, thick fog, market stalls, gaslamps | Horror and mystery cases; open PvP at night |
| **Limehouse & the Docks** | Warehouses, cranes, tall ships, river mist | Black Thames turf; smuggling runs; territory war |
| **Mayfair & Belgravia** | White stucco mansions, ballrooms, gardens | Crown Bindery hub; social-infiltration cases |
| **The Thames & Tower Bridge** | Steamboats; **Tower Bridge under construction** (built 1886–94) | Set-piece bosses on scaffolding; river chases |
| **The Metropolitan Railway** | Steam Underground, soot-black tunnels | Fast travel; train-roof fights |
| **Highgate Cemetery & the Catacombs** | Gothic tombs, Egyptian Avenue, crypts | Entrance to procedural dungeons (**The Undercroft**) |

### 4.3 Realism & art direction
- **Lighting:** Future lighting; warm sodium-amber gaslamps (PointLights with subtle flicker) against blue-grey fog; `Atmosphere` density tuned per district (Whitechapel heaviest).
- **Materials:** PBR `SurfaceAppearance`: wet cobblestone with puddle reflections, soot-stained brick, brass, wrought iron, wool and leather for coats.
- **Weather states:** Fog (default), Drizzle, Downpour + thunder, rare **Clear Moon** night (event bonus), Snow (winter season).
- **Life:** NPC crowds (vendors, constables, newsboys), hansom cabs and horses (the in-game fast-travel "cab fare" is an Ink sink), coal smoke from chimneys, Thames boats.
- **Audio:** hooves on cobbles, distant foghorns, rain on awnings, and a **clock-tower bell that marks each night event.** Newsboys shout headlines generated from real server events (§8).
- **Pipeline:** Blender (manual or Blender MCP) → FBX → Studio. Roblox Studio MCP (`generate_material`, `generate_mesh`, `generate_scene`, `insert_asset`) speeds up greyboxing and texture variety.
- **Budgets:** ≤ 20 K tris per hero building, `RenderFidelity` LODs, ≤ 1,500 draw calls on mobile, 3 graphics tiers. Most Roblox sessions are on mobile, so the low tier must still read as "foggy London".

---

## 5. Core Loops

| Timescale | Loop | Main rewards |
|---|---|---|
| **30 s** | Encounter: combo, dodge, ability, finisher | XP, Ink, drop roll |
| **3–7 min** | **Case** (12 templates, §7.4) | Ink, faction rep, Spin Shard chance, case evidence |
| **20–30 min** | **Story chapter** or **Undercroft** run (5 floors + boss) | Gear, mastery XP, Binding Thread chance |
| **24 min (real time)** | **Big Bell night cycle:** 16 min day / 8 min night. Night opens PvP zones, triples rare-drop odds, and starts a **Night Event** (world boss, syndicate ambush, fog horror, territory skirmish) | Event chests, titles, leaderboard points |
| **Daily** | 3 daily cases, login streak, 1 free banner spin, *The Penny Ledger* bounty | Shards, Ink |
| **Weekly** | Ranked ladder, Territory War (weekend), weekly raid boss | Exclusive cosmetics, Quills |
| **Season (8 wks)** | Battle pass, featured banner rotation, story volume | Limited cosmetics, new district/boss |

**Why a session lasts 1–2 h:** there is always (a) a case under 5 min away, (b) a night event under 24 min away, (c) a mastery/level milestone in view, and (d) a story cliffhanger. Finishing one goal reveals the next, which is the standard "one more" pattern. A real skill curve (§7) keeps play rewarding, not just compulsive.

---

## 6. Character Systems (the reroll layer)

Six slots. Each can be rerolled. Odds are always visible.

| Slot | Spin currency | Paid? | Affects power? |
|---|---|---|---|
| **Manuscript** | Manuscript Spin (10 Shards, or Quills) | Yes | **Major** |
| **Trait** | Trait Spin (300 Ink, or Quills) | Yes | Moderate |
| **Fighting Style** | Style Spin (200 Ink, or Quills) | Yes | Moderate |
| **Origin** | Origin Spin (150 Ink) | Ink only | Minor |
| **Look** (face, hair, eyes, scars) | Look Spin (100 Ink) or direct choose for Quills | Yes | None |
| **Attire** (coat/hat/gloves cosmetic sets) | Wardrobe Spin (Quills) and direct buy | Yes | None |

### 6.1 Manuscript banner odds (Standard "Circulating Library" banner)

| Rarity | Total odds | # at launch | Per Manuscript |
|---|---|---|---|
| Common | 56.0 % | 8 | 7.0 % |
| Uncommon | 24.0 % | 8 | 3.0 % |
| Rare | 12.0 % | 6 | 2.0 % |
| Epic | 6.0 % | 4 | 1.5 % |
| Legendary | 1.8 % | 3 | 0.6 % |
| Mythic | 0.2 % | 1 | 0.2 % |
| **Total** | **100.0 %** | **30** | |

**Pity (counters shown in UI, kept across sessions, shared between paid and free spins):**
- **Epic+ soft pity:** from spin 30, Epic+ odds +2 % per spin; **hard pity at 40.**
- **Legendary+ soft pity:** from spin 120, Legendary+ odds +1 % per spin; **hard pity at 160.**
- Expected spins per Legendary+ without pity ≈ 50; with soft pity the median is ~45.

**Featured banner ("New Edition", rotates every 2 weeks):** same rarity odds. When you hit a Legendary, there's a **50 %** chance it's the featured one; if it isn't, your next Legendary is **guaranteed** featured (the 50/50 rule, disclosed in-app). The featured Epic gets 50 % of the Epic share. This creates "limited-time hype" honestly: the featured Manuscript returns to the Standard pool after 2 seasons, so FOMO is temporary.

### 6.2 Launch Manuscripts (30)

Move keys: **Q / E / R / F** (mobile: 4 buttons) + **Awakening** (G, meter). ⚑ = work also used in BSD, needs a clearly different design.

| # | Manuscript (work, author, year) | Rarity | Role | Q | E | R | F | Awakening |
|---|---|---|---|---|---|---|---|---|
| 1 | *The Tell-Tale Heart* (Poe, 1843) | Common | Bruiser | Heartbeat pulse (AoE stagger) | Floorboard slam | Pounding rhythm (stacking dmg buff) | Guilt mark (DoT) | **"Louder!"**: 8 s of escalating shockwaves |
| 2 | *Rip Van Winkle* (Irving, 1819) | Common | Control | Drowsy cloud (slow) | Yawn wave (cancel enemy cast) | Mountain mist cloak | Nap (self-heal channel) | **Twenty Years**: sleep all enemies in radius 3 s |
| 3 | *The Cask of Amontillado* (Poe, 1846) | Common | Zoner | Brick wall | Trowel throw | Chain shackle (root) | Wine-cellar trap | **Immurement**: wall an enemy in for 4 s |
| 4 | *Oliver Twist* (Dickens, 1838) | Common | Skirmisher | Pickpocket (steal a buff) | Alley dash | Artful decoy | "More, please" (heal on hit) | **The Gang**: 3 urchin clones |
| 5 | *Sleepy Hollow* (Irving, 1820) | Common | Burst | Flaming pumpkin | Spectral gallop | Headless lunge | Hollow scream (fear) | **The Horseman**: mounted charge phase |
| 6 | *Treasure Island* (Stevenson, 1883) | Common | Ranged | Flintlock shot | Cutlass spin | Powder keg | Parrot scout (reveal) | **Broadside**: cannon barrage |
| 7 | *Robinson Crusoe* (Defoe, 1719) | Common | Trapper | Snare | Driftwood shield | Signal fire (zone) | Forage (cleanse) | **Castaway Fort**: palisade arena |
| 8 | *Gulliver's Travels* (Swift, 1726) | Common | Size-shift | Shrink (dodge buff) | Giant stomp | Lilliput ropes (root) | Grow (armor) | **Brobdingnag**: giant form 10 s |
| 9 | *The Invisible Man* (Wells, 1897) | Uncommon | Assassin | Fade | Bandage whip | Unseen strike (backstab ×1.5) | Footprints decoy | **Total Transparency**: invisible 6 s, first hit crits |
| 10 | *Twenty Thousand Leagues* (Verne, 1870) | Uncommon | Mage | Pressure orb | Harpoon pull | Diving bell (shield) | Kraken tendril | **Nautilus**: ram through a line |
| 11 | *The Three Musketeers* (Dumas, 1844) | Uncommon | Duelist | Phantom thrust | Riposte stance | "All for one" (summon 3 blades) | Musket volley | **One for All**: 3 musketeer clones mirror moves |
| 12 | *The Time Machine* (Wells, 1895) | Uncommon | Trickster | Temporal blink | Age (slow enemy) | Rewind 3 s (position + HP) | Future echo | **Eloi & Morlock**: freeze time zone 3 s |
| 13 | *Around the World in 80 Days* (Verne, 1872) | Uncommon | Speed | Steam dash | Balloon hop | Ticket punch (multi-hit) | Pocket-watch haste | **Against the Clock**: +60 % speed and cooldown reduction |
| 14 | *The Pit and the Pendulum* (Poe, 1842) | Uncommon | Zoner | Pendulum swing | Pit (knock-down) | Closing walls | Rats (DoT swarm) | **The Inquisition**: shrinking blade arena |
| 15 | *Carmilla* (Le Fanu, 1872) | Uncommon | Drain | Life sip | Mist step | Nocturne (night buff) | Charm (taunt reversal) | **Crimson Countess**: lifesteal +40 % |
| 16 | *The Jungle Book* (Kipling, 1894) | Uncommon | Summoner | Panther pounce | Bear maul | Python coil (grab) | Wolf pack howl | **Law of the Jungle**: all three spirits at once |
| 17 | *Dracula* (Stoker, 1897) | Rare | Drain/Summon | Bat swarm | Blood spear | Mesmerize (stun) | Mist form (i-frames) | **Count of Transylvania**: winged form, drain aura |
| 18 | *The Hound of the Baskervilles* (Doyle, 1902) | Rare | Pet/Tracker | Hound lunge | Moor fog | Phosphor glow (mark) | Howl (fear) | **The Legend**: giant spectral hound |
| 19 | *The Picture of Dorian Gray* (Wilde, 1890) | Rare | Tank | Portrait (store 30 % of damage taken) | Ageless (cleanse) | Canvas tear (release stored dmg) | Vanity mirror (reflect) | **The Attic**: immune 4 s, then everything stored explodes |
| 20 | *The War of the Worlds* (Wells, 1898) | Rare | Artillery | Heat ray | Black smoke | Tripod stomp | Red weed (zone) | **Martian Tripod**: piloted mech phase |
| 21 | *A Christmas Carol* (Dickens, 1843) | Rare | Support | Ghost of Past (rewind ally HP) | Ghost of Present (buff) | Ghost of Future (curse) | Chain of Marley (pull) | **Three Spirits**: team buff + enemy curse |
| 22 | *Les Misérables* (Hugo, 1862) | Rare | Defender | Barricade | Candlestick bash | Sewer escape | "Do you hear…" rally (team speed) | **The Barricade Falls**: fortified zone |
| 23 | *Frankenstein* (Shelley, 1818) ⚑ | Epic | Summoner/Bruiser | Galvanic bolt | Stitch (heal) | Grave grab | Lightning rod | **The Creature**: you *become* the Creature (unlike BSD's design: no summoned doll) |
| 24 | *Strange Case of Dr Jekyll & Mr Hyde* (Stevenson, 1886) | Epic | Stance-swap | Jekyll: tonic toss (heal) / Hyde: savage claw | Jekyll: deduction mark / Hyde: rampage | Swap stance | Jekyll: smoke vial / Hyde: roar | **Hyde Unleashed**: Hyde form +50 % dmg, no healing |
| 25 | *The Raven* (Poe, 1845) | Epic | Controller | Raven volley | "Nevermore" (silence 2 s) | Midnight dreary (dark zone) | Bust of Pallas (decoy) | **Lenore's Lament**: raven storm, silences all |
| 26 | *The Phantom of the Opera* (Leroux, 1910) | Epic | Trickster | Mirror step | Chandelier drop | Punjab lasso | Siren aria (charm) | **Opera Populaire**: stage domain where you teleport between mirrors |
| 27 | *Moby-Dick* (Melville, 1851) ⚑ | Legendary | Juggernaut | Harpoon chain | Whaleboat ram | Tidal breach | Obsession mark (+dmg on one target) | **The White Whale**: colossal whale breach from the cobbles (as Ahab's hunter, not BSD's floating fortress) |
| 28 | *Paradise Lost* (Milton, 1667) | Legendary | Aerial | Fallen-wing dive | Pandemonium flames | Serpent's whisper (confuse) | Rebel host (summon) | **Better to Reign**: flight + hellfire 10 s |
| 29 | *Faust* (Goethe, 1808/1832) | Legendary | Pact | Pact (trade HP for dmg) | Mephisto's flame | Walpurgis circle | Contract bind (link enemy damage) | **The Wager**: double damage, but die if not KO'd in 10 s (huge risk/reward) |
| 30 | *The Divine Comedy* (Dante, c.1320) | Mythic | Domain | Inferno ring | Purgatory ascent (heal) | Paradiso light | Virgil guide (auto-dodge) | **Nine Circles**: domain arena; each circle applies a different curse |

**Mastery (1–50 per Manuscript):** unlocks move variants at 10/20/30 (e.g. Dracula Q → "Bat Cyclone"), an alternate Awakening skin at 40, and a mastery title + golden ink VFX at 50. Mastery gives about 60 % of a character's late-game power, so commons with high mastery beat fresh Legendaries.

### 6.3 Traits (one slot, two with Mythic trait or Reprint 3)

| Tier | Total | # | Each | Traits |
|---|---|---|---|---|
| Common | 60 % | 8 | 7.5 % | *Night Owl* (+8 % dmg at night) · *Bookish* (+10 % mastery XP) · *Thick-Skinned* (+6 % HP) · *Quick Hands* (−5 % cooldowns) · *Light-Footed* (+1 dodge charge regen) · *Iron Lungs* (+15 % sprint) · *Penny-Wise* (+10 % Ink) · *Keen-Eyed* (+4 % crit) |
| Rare | 30 % | 6 | 5.0 % | *Insomniac* (+15 % night dmg, −5 % day) · *Gaslighter* (hits have a 10 % chance to fear) · *Pickpocket* (steals Ink on PvP hit) · *Stoic* (+20 % posture) · *Duelist* (+10 % 1v1 dmg) · *Fog-Walker* (invisible in fog when still) |
| Legendary | 9 % | 4 | 2.25 % | *Prodigy* (+25 % mastery XP, +1 move variant early) · *Bloodhound* (case clues highlighted, +15 % PvE dmg) · *Last Chapter* (+30 % dmg below 25 % HP) · *Silver Tongue* (AI witnesses reveal +1 fact) |
| Mythic | 1 % | 2 | 0.5 % | *Author's Pen* (2 Awakening charges) · *Marginalia* (second Trait slot) |
| **Total** | **100 %** | 20 | | |

Trait pity: Legendary+ guaranteed by 60 Trait Spins.

### 6.4 Fighting Styles & Origins

**Styles (Style Spin):** Street Brawling 35 % · Pugilism (Queensberry boxing) 25 % · Savate 18 % · Canne de Combat (cane) 12 % · Sabre Fencing 7 % · **Bartitsu** (Victorian cane + jujitsu hybrid) 3 % = **100 %**. Each style has its own 5-hit M1 string, heavy attack, and grab. Rarer styles get longer combo routes and better frame data, but every style can win.

**Origins (Origin Spin, Ink only):** Street Urchin 20 % (+speed, slum dialogue) · Dockhand 20 % (+HP, Thames contacts) · Ex-Soldier 20 % (+posture, Crown dialogue) · Scholar 15 % (+mastery XP, Society dialogue) · Immigrant 15 % (+Ink, unique side-story) · Peer's Heir 10 % (+Ink trade discount, Mayfair access) = **100 %**.

### 6.5 Anti-frustration systems (key for retention *and* trust)
- **Lock slots:** keep up to 2 Manuscripts saved (base 1 + 1 at level 20; +2 via pass; +1 per Reprint). You can swap freely in hub. This removes "I rerolled away my Legendary".
- **Binding Thread (spark):** every Manuscript Spin gives 1 Thread; duplicates give extra Thread by rarity (Common 1 · Uncommon 2 · Rare 5 · Epic 15 · Legendary 40). **1,000 Thread = choose any non-Mythic Manuscript** at the **Bindery** (fixed-price, non-random shop). This caps worst-case bad luck and doubles as the fallback for PolicyService-restricted players.
- **Lock-a-Trait reroll:** reroll your Trait slot while keeping a chosen stat line (inspired by Type Soul's locked rerolls).
- **Mastery is per Manuscript and kept forever.** Return to an old Manuscript and its mastery is still there.
- **No reroll ever wipes level, gear, or story progress** (unlike Type Soul's Soul Ticket).

---

## 7. Combat Design

### 7.1 Stats
Players earn 3 points per level, spread across:

| Stat | Effect per point |
|---|---|
| **Vitality** | +12 HP, +0.2 % damage reduction |
| **Might** | +1 % M1/style damage |
| **Wit** | +1 % Manuscript damage, +0.25 % cooldown reduction |
| **Agility** | +0.5 % move speed, +1 % dodge regen |
| **Ink** | +2 max Ink (ability resource), +0.5 % Ink regen |

Soft caps at 60 points per stat. Respec: first one free, then Ink cost (a sink).

**Damage formula:**
`Damage = Base × (1 + Stat%) × (1 + 0.01 × Mastery) × TraitMult × GearMult × CritMult × (1 − TargetDR)`
- Crit: base 5 %, ×1.5. DR is capped at 40 %. PvP applies **ranked normalization**: Manuscript base values are clamped to a ±10 % band across rarities, and gear is flattened.

### 7.2 Moves & frame data (baseline)
| Action | Numbers |
|---|---|
| M1 string | 5 hits; hit 4 launches; hit 5 knockback; 0.35 s per hit |
| Heavy | 0.6 s windup, breaks block; 6 s cooldown |
| Dodge | 0.35 s dash, **0.2 s i-frames**, 2 charges, 2.5 s recharge each |
| Block | −70 % damage; drains posture |
| **Posture** | 100; at 0 → **guard break**, stunned 1.2 s |
| **Parry** | 0.18 s window at block start → attacker staggered 0.8 s, you regain 20 posture |
| Ink (resource) | 100 base; abilities cost 15–40; regen 5/s; +3 per M1 hit |
| Awakening meter | Fills from damage dealt/taken; lasts 15–20 s; 1 charge (2 with *Author's Pen*) |
| Grab | Unblockable, beaten by dodge; 8 s cooldown |
| Combo rules | Hitstun decay after 8 hits (prevents infinite combos); "burst" escape costs 50 Ink |

### 7.3 Status effects
Bleed (DoT), Burn (DoT + −heal), Chill (−30 % speed), Fear (no abilities 1.5 s), Silence (no Manuscript 2 s), Mark (+15 % damage taken from the marker), Root (no movement 1.5 s). Diminishing returns on repeat crowd control within 10 s.

### 7.4 PvE
- **Case templates (12):** Witness Interrogation (AI) · Pickpocket Chase · Rooftop Pursuit · Warehouse Raid · Escort the Informant · Séance Gone Wrong (horror) · Smuggler Intercept · Ballroom Infiltration (stealth) · Body-Snatcher Graveyard · Runaway Omnibus · Forged Manuscript (puzzle) · Bounty Hunt. Templates × 7 districts × enemy sets × modifiers = hundreds of variations.
- **The Undercroft:** procedural dungeon from Highgate Catacombs; 5 floors, random room graph, a floor modifier (e.g. "Thick Fog: −vision, +loot"), mini-boss on floor 3, boss on floor 5. Solo-scaled or party of 4.
- **Story bosses** (hand-built): *The Scaffold Duel* on unfinished Tower Bridge; *The Underground Express* (fight on a moving steam train); *The Masquerade* (Mayfair ballroom).
- **Night Events / world bosses:** *The Fog Leviathan* (Thames), *The Burning Press* (Fleet Street fire), *The Resurrection Men* (Highgate horde). Server-wide damage leaderboard; everyone who contributes gets loot.

### 7.5 PvP
- **Open-world night PvP** in Whitechapel and the Docks only. Entering is an opt-in with a clear warning; leaving is safe after 10 s out of combat. Repeat killers get a **bounty** (visible, claimable by anyone).
- **Ranked Duels and 2v2** in an arena instance: Elo; ranks **Pamphlet → Penny Dreadful → Novella → Novel → Classic → Canon**; resets each season with exclusive ink-trail cosmetics per rank.
- **Territory War** (Sat–Sun): factions capture control points in the Docks/Whitechapel; the winners get +10 % Ink for the week and their banner on hub lampposts.
- Losing in PvP costs a little Ink (2 %) and nothing else. No gear loss and no paid "insurance" (lesson from Deepwoken).

---

## 8. AI NPCs (Roblox TextGenerator)

`TextGenerator` lets an experience call an LLM with a system prompt plus a player prompt. NPC dialogue is its main documented use. Rate limits started around 100 requests/min and scale with CCU, but the docs contradict each other, so verify. Testing requires Team Test.

| Feature | How it works | Why it helps engagement |
|---|---|---|
| **Witness Interrogation** | The server seeds a case with a culprit and 3 hidden facts. Each witness gets a persona prompt plus the facts it knows. The player asks questions (free text or quick-reply buttons). The **server**, not the LLM, checks the reply for fact keywords to award clues. The player accuses a suspect. | Every case feels different; playing detective is the core BSD fantasy |
| **Faction leaders with memory** | Stores a 3-line summary of your recent missions/defections in DataStore and feeds it into the leader's prompt | Makes players feel noticed, so they get attached |
| ***The Penny Ledger*** **(daily newspaper)** | Each server day, structured data (top bounty, world-boss MVP, territory winner, rare pulls) → LLM writes 5 headlines; newsboys shout them in-world | Players see their own names in the news, which they love to share |
| **Hub café owner** | Hints, lore, gossip | Lore delivery without walls of text |

**Guardrails:**
- Strict persona prompt; temperature 0.3–0.5; replies ≤ ~60 tokens.
- All player input **and** all output go through `TextService:FilterStringAsync`.
- Player names in headlines appear only after filtering, and players can opt out in settings.
- Per-player cooldown (≈1 msg / 4 s) and a per-server budget; scripted dialogue trees as fallback.
- **The LLM never decides rewards, damage, or drops.**

---

## 9. Progression

| Track | Range | Notes |
|---|---|---|
| Player Level | 1–100 | ~60 h to max for an engaged free player |
| **Reprint** (prestige) | Unlimited | Resets level; keeps everything else; +1 Lock slot (up to 3), title, ink-color VFX; Reprint 3 unlocks a 2nd Trait slot |
| Manuscript Mastery | 1–50 each | §6.2 |
| Faction Rank | 10 per faction | Unlocks faction gear, chapters, hub areas |
| Gear | Coat, gloves, charm, cane/blade cosmetic | Rarity Common → Legendary; upgrade +1…+10 with Ink + mats (failure never destroys gear) |
| **The Library** (collection) | All Manuscripts, traits, bosses, cases | Completion rewards: titles, Quills, Thread |
| Battle Pass | 60 tiers | §10.3 |

---

## 10. Economy & Monetization

### 10.1 Principles
1. **Everything that affects power can be earned free.** Robux buys speed and choice.
2. **Cosmetics are the biggest long-term revenue line.** The audience is very aware of how they look in clips.
3. **Transparent RNG**, pity, and spark (Binding Thread).
4. **Never charge for recovering from a loss.**

### 10.2 Currencies & faucets/sinks (mid-game, per active hour)

| Currency | Faucets (≈/hour) | Sinks |
|---|---|---|
| **Ink** (soft) | Cases 12 × 80 = 960 · mobs ~400 · Undercroft ~500 · dailies (amortized) ~200 → **~2,000/h** | Gear upgrades (200 → 6,000 each, escalating) · Trait Spin 300 · Style Spin 200 · Origin 150 · Look 100 · cab fare 10–30 · tonics 50 · respec 1,000 · faction donations · dye 500 |
| **Spin Shards** (earned, 10 = 1 Manuscript Spin) | Case drop 10 % × 12 ≈ 1.2 · Undercroft boss 2 · Night Event 3 · daily cases 15/day · login streak ~3/day → **~12/h** for a 1.5 h/day player | Manuscript Spins |
| **Quills** (premium) | Robux; free BP track ~300/season; weekly raid first clear 30; Library milestones | Spins, cosmetics, Bindery shortcuts, slots |
| **Binding Thread** (spark) | 1 per Manuscript Spin; duplicates +1/2/5/15/40 by rarity → **~300/month** for a free player | Bindery: choose a Manuscript (1,000) |

**Inflation target:** sinks absorb 85–95 % of Ink faucets at every level band. Escalating gear upgrade costs are the main late-game sink. Track the Ink balance distribution weekly; if the median grows more than 20 % per week, add sinks (cosmetic dyes, Reprint costs).

**Trading:** cosmetics only, between players with 10+ hours played. **No Manuscript trading.** This prevents real-money trading, scams, and bypassing the paid-random-item rules, and keeps spins meaningful.

### 10.3 Robux price sheet (start; A/B test ±20 %)

Quills are bought in packs; spins cost **160 Quills** each (10-pull 1,600).

| Pack | Robux | Quills | Robux per spin |
|---|---|---|---|
| Handful | 99 | 800 | ~19.8 |
| Pouch | 399 | 3,400 (+6 %) | ~18.8 |
| Satchel | 799 | 7,200 (+13 %) | ~17.8 |
| Chest | 1,999 | 19,000 (+19 %) | ~16.8 |
| Vault | 3,999 | 40,000 (+25 %) | ~16.0 |
| **First-purchase bonus** | — | doubles the first buy of each pack size (one-time) | |

| Product | Robux | Notes |
|---|---|---|
| **Starter Satchel** (once per account, available 72 h) | 149 | 10 spins + Victorian greatcoat + 1 h 2× XP |
| Game pass: **+2 Lock slots** | 399 | Top seller in the genre |
| Game pass: **2× Ink** | 349 | |
| Game pass: **Bulk spin (10×) + skip animation** | 149 | Quality of life |
| Game pass: **Extra character** | 299 | Up to 3 |
| Game pass: **Fast-travel cab whistle** | 199 | Call a cab anywhere |
| Private server | 100/mo | |
| **Society Membership** (Roblox Subscription) | ~$4.99/mo tier | Daily 100 Quills + 3 Shards, +15 % XP, monthly exclusive coat, gold name in *The Penny Ledger* |
| **Battle Pass** (8-week season) | 499 (premium) / 1,299 (+20 tiers) | Free track keeps ~40 % of the value incl. ~300 Quills |
| **Luck Tonic** (1 h, Epic+ ×1.25 relative) | 99 | Live-updated odds shown while active |
| **Cosmetics**: coats, top hats, canes, ink auras, finisher animations, Manuscript recolors | 75–999 | Rotating shop + permanent catalogue |
| **Wardrobe Spin** (cosmetic gacha, odds shown) | 80 Quills / spin | Attire sets; duplicates → dye tokens |
| **Rewarded video** | — | 13+, after 100 K+ avg DAU over 28 days; 2 Shards per view, max 5/day |

### 10.4 Free vs paid: what a player actually gets per month

| Player type | Play | Manuscript spins/month | Epic+ /month | Legendary+ /month |
|---|---|---|---|---|
| Free | 1.5 h/day | ~55 (shards) + codes ~20 → **~75** | ~6 | ~1.5 |
| Member ($4.99) | 1.5 h/day | 75 + 9 (shards) + 19 (Quills) → **~103** | ~8 | ~2 |
| Member + BP | 1.5 h/day | ~115 | ~9 | ~2.3 |
| Heavy spender | — | 300+ | 24+ | 6+ |

Plus Binding Thread: a free player reaches a guaranteed choice (1,000 Thread) about every 3–4 months. **A free player can collect every Legendary in about 6–9 months.** This is the fairness line we promise publicly.

**Value check:** one spin ≈ R$17–20. A free player earns about R$1,300–1,500 of spin value per month, enough that paying feels like a shortcut, not the only way to progress.

### 10.5 Payer segmentation (expected mix for genre)
| Segment | % of DAU | Monthly spend | % of revenue |
|---|---|---|---|
| Non-payer | 96–98 % | 0 | 0 % (they're the community, PvP opponents, and algorithm signal) |
| Minnow | 1.5–2.5 % | R$100–500 | ~25 % |
| Dolphin | 0.4–0.8 % | R$500–3,000 | ~40 % |
| Whale | 0.05–0.15 % | R$3,000+ | ~35 % |

Responsible guardrails: monthly spend summary in settings, purchase confirmation with odds, and an optional self-set monthly cap. Roblox parental spend controls apply as well.

### 10.6 Banner calendar (one season = 8 weeks)
| Week | Featured banner | Other |
|---|---|---|
| 1–2 | New Legendary (season headliner) + new Epic | Season launch, BP starts |
| 3–4 | New Rare/Epic pair | Wardrobe set A |
| 5–6 | **Rerun** of a past Legendary | Territory War finals |
| 7–8 | New Legendary #2 | "Final Chapter" story event, Wardrobe set B |
The Standard banner gains each featured Manuscript 2 seasons after its debut.

---

## 11. Unit Economics & Revenue Model

### 11.1 Retention curve (target)
Modeled as `r(t) = 0.35 · t^-0.53` (fits D1 35 %, D7 12.5 %, D30 5.8 %):

| Day | 1 | 7 | 14 | 30 | 60 | 90 | 180 |
|---|---|---|---|---|---|---|---|
| Retained | 35 % | 12.5 % | 8.6 % | 5.8 % | 4.0 % | 3.2 % | 2.2 % |

**Expected active days per install (180-day horizon) ≈ 9.0.**

### 11.2 LTV per install
| ARPDAU | Gross Robux | Net to dev (×0.7 marketplace × $0.0038 DevEx) |
|---|---|---|
| R$4 | R$36 | **$0.096** |
| R$5 | R$45 | **$0.12** |
| R$6 | R$54 | **$0.14** |

(18+ US spend earns a higher DevEx rate, so blended net could be 10–20 % higher depending on audience mix.)

### 11.3 Monthly revenue scenarios
| Scenario | Avg CCU | ≈ DAU | ARPDAU | Gross R$/mo | ≈ Net USD/mo |
|---|---|---|---|---|---|
| Niche | 2 K | 15 K | R$4 | 1.8 M | ~$4.8 K |
| Solid | 10 K | 75 K | R$5 | 11.25 M | ~$30 K |
| Hit (Gakuran's level today) | 15–20 K | 110–150 K | R$5 | 16.5–22.5 M | ~$44–60 K |
| Breakout (Gakuran-peak months) | 60 K+ | 450 K+ | R$5 | 67 M+ | ~$180 K+ |

Cross-check: Gakuran is estimated at ~$203 K in the last 30 days and ~$2.3 M in its first year. That fits the Breakout row during spikes and the Hit row on average.

### 11.4 Extra revenue streams
Creator Rewards (engagement-based payouts), rewarded video (+5–15 %), and immersive ad placements (newspaper billboards fit the setting).

### 11.5 Implication for growth
At ~$0.12 net LTV per install, **paid user acquisition (sponsored ads) only breaks even at roughly <$0.10 CPI.** Use ads only for launch-week algorithm seeding. Sustainable growth must come from **Roblox recommendations (driven by retention, session length, and like ratio), codes, TikTok clips, and creators** (§14).

---

## 12. Engagement & Retention

**First session (FTUE):**
- 0:00 Cold open: fog, a scream in Whitechapel, your Manuscript awakens mid-fight (scripted Rare+).
- 1:30 First combo tutorial woven into a chase.
- 3:00 First real Manuscript Spin, **guaranteed Rare+** (sets the hook; Roblox players decide whether to stay in under 3 minutes).
- 5:00 Choose a faction (shown as a story choice).
- 8:00 First boss, then Society HQ hub reveal.
- 12:00 First AI interrogation case.
- 20:00 First night bell, a world event, and a taste of night PvP from a safe vantage point.

**Ongoing hooks:** 7-day login cycle (day 7 = 5 Shards), daily free banner spin, 3 dailies, group-join reward (10 spins), milestone codes, leaderboards (server/faction/global), Library completion, a seasonal pass, opt-in experience notifications ("The Fog Leviathan rises tonight").

**Guardrails (protect players and the game's standing on Roblox):**
- No fake near-miss spin animations; results are decided server-side first and shown honestly.
- No countdown timers on spin purchases (limited-time offers are for cosmetic bundles only).
- Monthly spend summary and an optional self-set cap.
- Optional 2-hour break reminder in the game's voice ("The candle burns low, detective. London will keep.").
- A large share of the audience is 13–17. Predatory design brings regulator attention, chargebacks, Roblox moderation, and bad press. Over time, players who trust the game spend more.

---

## 13. Live Ops Roadmap

| Phase | Timing | Content |
|---|---|---|
| Closed alpha | M-2 | Strand + Whitechapel, 12 Manuscripts, 1 Undercroft floor set, duels |
| **Launch: Volume I "The Fog"** | M0 | 5 districts, 30 Manuscripts, 4 factions, story arc 1, Undercroft, ranked duels, BP Season 1 |
| Patch | +2 wks | Balance, QoL, new codes, new world boss |
| **Volume II "The Bridge"** | +8 wks | Tower Bridge set piece, 6 Manuscripts, 2v2 ranked, Territory War |
| **Volume III "Below"** | +16 wks | Metropolitan Railway expansion, 4-player raid, Awakening tier 2 |
| Seasonal | — | **Halloween** (Poe/Le Fanu banner, horror cases), **Winter** (*A Christmas Carol* event, snow, Dickens banner), **Anniversary** (Mythic #2) |

**Cadence:** small patch every 2 weeks and a major update every 8. Gakuran's ~32 % monthly decline after its spike and Shindo Life's collapse both come from content gaps and power creep.

---

## 14. Launch & Growth

1. **Clip-first combat:** every Awakening is a 3–5 s set piece built to look good in 9:16. Ship a photo/replay mode with a subtle watermark.
2. **Creator program:** early access + personal codes for 20–50 anime and Roblox-RPG creators (10 K–1 M subs). Give them a creator-only cosmetic for their fans.
3. **Codes economy:** like/visit milestones ("15K likes = 20 spins"). Code-guide sites (PocketGamer, AllThings.how, PlayNews, BlueStacks, games.gg…) give free coverage in many languages, as they did for Gakuran.
4. **Group-join + favorite rewards** (Gakuran pattern).
5. **Discord:** tier-list debates, lore theories, featured-banner leaks, fan art contests.
6. **Aesthetic crossover:** gothic/dark-academia TikTok is a large, organic 16–22 community. Post city-ambience shorts (fog, rain, gaslamps) in addition to combat clips.
7. **Timing:** launch Friday ~4 PM EST; a seasonal tie-in (Halloween is ideal for gothic London).
8. **Paid ads:** launch week only, to seed the algorithm (see §11.5).

---

## 15. Technical Architecture

- **Data:** session-locked profiles (ProfileStore-style) on DataStoreService; versioned schema migrations; `MarketplaceService.ProcessReceipt` with idempotent purchase IDs so spins are never lost or duplicated.
- **RNG:** server-only `Random.new()`; result + pity + Thread saved **before** the client animation; every roll logged to an audit store.
- **Odds config:** a single source-of-truth module drives both the RNG **and** the odds UI, so displayed odds always match real odds. A unit test asserts every table adds up to 100 % and pity math matches the docs.
- **PolicyService:** checked on join and cached; paid spin UI hidden when restricted, Bindery shown instead.
- **Anti-exploit:** server-authoritative damage, cooldowns, and positions; hitbox validation with ~150 ms lag compensation; rate-limited RemoteEvents; movement sanity checks.
- **Performance:** StreamingEnabled, `CollectionService` tags, pooled VFX, ≤ 60 active NPCs and 20–30 players per server.
- **Analytics:** `AnalyticsService` funnels (FTUE steps, first spin, first case, first purchase), economy sources/sinks, retention, per-banner conversion.
- **Code:** Rojo + strict Luau. Modules: Combat, Stats, Manuscripts, Spins/Pity, Economy, Cases, Factions, AINPC, Ledger, Shop.

---

## 16. KPI Targets

| Metric | Genre top-10 % (industry estimate) | Target |
|---|---|---|
| D1 / D7 / D30 | 30–40 % / 10–15 % / 4–6 % | 35 % / 12 % / 5 % |
| Avg session | 25–40 min | ≥ 45 min |
| Sessions per DAU | 1.5–2 | ≥ 1.8 |
| Payer conversion | 1–3 % | 2–4 % |
| ARPDAU | R$3–6 | ≥ R$5 |
| Like ratio | 85–90 % (Gakuran 89 %, AoT Rev 96 %) | ≥ 90 % |
| FTUE completion (first boss) | — | ≥ 70 % |
| % of free players reaching first Legendary by D30 | — | ≥ 50 % of D30-retained players |

---

## 17. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| DMCA (BSD) | PD works only, ⚑ overlap review, no BSD branding |
| "P2W" backlash | Free earn rates (§10.4), pity, Thread spark, Lock slots, ranked normalization |
| Spin inflation (JJI-style 100-spin codes) | Codes give 10–30; spin value modeled in §10.4 |
| Paid random item violation | Checklist §3.3, single odds config, audits |
| Spike-then-decline (Gakuran) | 2-week cadence, banner calendar, seasonal ranked |
| Loss-recovery backlash (Deepwoken) | Tiny PvP losses, no paid insurance or restores |
| LLM off-script or unsafe | Filtering, low temperature, persona lock, fallback trees, no LLM rewards |
| Exploiters | Server authority, reports + replays |
| Mobile performance | 3 graphics tiers, LOD, streaming |
| Historical sensitivity | No real crime victims; fictional cases only |

---

## 18. MVP Scope (~10–12 weeks, 3–5 people)

1. The Strand hub + Whitechapel (fog, gaslamps, day/night, rain).
2. Combat core: stats, M1 string, dodge, block/parry/posture, heavy, grab, 4 moves, Awakening.
3. 12 Manuscripts (#1, 2, 4, 6, 9, 12, 15, 17, 19, 23, 24, 27), Standard banner, odds UI, pity, Binding Thread, 2 Lock slots.
4. Trait, Style, and Look spins.
5. 3 case templates incl. AI Witness Interrogation.
6. Undercroft: 3 floors + boss.
7. Ranked 1v1.
8. Shop: Quill packs, Starter Satchel, Lock pass, 2× Ink; PolicyService gating + Bindery.
9. Persistence, receipts, analytics funnels, roll audit log.

---

## Sources

**Competitors**
- [profitable.app — Gakuran stats & revenue estimate](https://profitable.app/roblox/games/gakuran) · [profitable.app — Gakuran developer](https://profitable.app/roblox/developers/gakuran)
- [RoWatcher — Gakuran](https://rowatcher.com/games/9199655655/gakuran) · [Is Gakuran dying?](https://rowatcher.com/games/9199655655/gakuran/dying) · [Gakuran Explodes (Sept 2026)](https://rowatcher.com/news/gakuran-explodes-brainrot-rules-week-of-sept-5-2026)
- [AllThings.how — Gakuran rerolls](https://allthings.how/gakuran-how-to-get-free-rerolls-with-codes-roblox/) · [PocketGamer — Gakuran codes](https://www.pocketgamer.com/roblox/gakuran-codes/) · [iGeeksBlog — Gakuran codes](https://www.igeeksblog.com/gakuran-codes/) · [BlueStacks — Gakuran codes](https://www.bluestacks.com/blog/redeem-codes/roblox-gakuran-redeem-codes-en.html)
- [GGRecon — Type Soul codes & rerolls](https://www.ggrecon.com/guides/type-soul-codes/) · [PCGamesN — Type Soul codes](https://www.pcgamesn.com/type-soul/codes) · [Pocket Tactics — Type Soul tier list](https://www.pockettactics.com/type-soul/tier-list) · [Deltia's — Type Soul race tier list](https://deltiasgaming.com/?p=334774)
- [Dexerto — Jujutsu Infinite codes](https://www.dexerto.com/roblox/jujutsu-infinite-codes-3254080) · [Sportskeeda — JJI spins](https://sportskeeda.com/roblox-news/how-get-spins-jujutsu-infinite) · [Earnaldo — JJI tier list 2026](https://earnaldo.com/blog/jujutsu-infinite-tier-list-2026)
- [RoWatcher — Attack on Titan Revolution](https://rowatcher.com/games/4658598196/attack-on-titan-revolution) · [RoWatcher — Blox Fruits](https://rowatcher.com/games/994732206/blox-fruits) · [RoWatcher — Deepwoken](https://rowatcher.com/games/1359573625/deepwoken) · [BetaHub — Deepwoken restore-system backlash](https://app.betahub.io/projects/pr-8346521607/issues/1883)
- [RoWatcher — Best Roblox RPGs 2026](https://rowatcher.com/news/best-roblox-rpgs-in-2026-ranking-the-top-10-by-gameplay-and-player-retention) · [Highest-earning Roblox games 2026](https://rowatcher.com/news/the-10-highest-earning-roblox-games-in-2026-and-what-they-mean-for-the-platform) · [PlayNews — Best anime Roblox games 2026](https://www.playnews.gg/en/guides/roblox-the-10-best-anime-games-in-2026)

**Platform & policy**
- [Roblox — Paid random items policy](https://create.roblox.com/docs/production/monetization/paid-random-items) · [TechTimes — Korea's loot box rules push Roblox to disclose odds worldwide](https://www.techtimes.com/articles/319148/20260626/koreas-loot-box-rules-push-roblox-disclose-item-odds-worldwide.htm)
- [Roblox — Content maturity](https://create.roblox.com/docs/production/promotion/content-maturity) · [Experience guidelines](https://create.roblox.com/docs/production/promotion/experience-guidelines) · [Safety by age](https://about.roblox.com/safety-by-age) · [MacMyths — chat age checks](https://macmyths.com/roblox-now-requires-age-checks-to-limit-chat-between-adults-and-minors/)
- [Roblox — TextGenerator](https://create.roblox.com/docs/reference/engine/classes/TextGenerator.md) · [Generate text guide](https://create.roblox.com/docs/characters/generate-text) · [DevForum — GDC 2025 recap](https://devforum.roblox.com/t/weekly-recap-gdc-2025-edition/3560345)
- [Roblox — Monetization overview](https://create.roblox.com/docs/get-started/monetization.md) · [DevForum — Rewarded video expansion](https://devforum.roblox.com/t/more-creators-can-now-use-rewarded-video-ads/3838678) · [eMarketer — Rewarded video](https://www.emarketer.com/content/roblox-expands-rewarded-video-tools-creators-advertisers)

**Market**
- [Roblox newsroom — DevEx +42 % for 18+](https://about.roblox.com/newsroom/2026/04/roblox-fuels-high-fidelity-games-over-18-players-increases-qualifying-devex-rate-42) · [RoWatcher — DevEx math 2026](https://rowatcher.com/news/roblox-devex-math-what-you-actually-take-home-in-2026)
- [Roblox Q4 2025 shareholder letter](https://s27.q4cdn.com/984876518/files/doc_financials/2025/q4/Q4-2025-Shareholder-Letter.pdf) · [SEC filing](https://last10k.com/sec-filings/rblx/0001628280-26-051082.htm) · [Interspace — DAU 123 M Q2 2026](https://interspacemusic.com/blog/roblox-daily-active-users-fall-to-123-million-in-q2-2026/) · [Exploding Topics — Roblox stats](https://explodingtopics.com/blog/roblox-stats) · [Konvoy — Roblox is not aging up](https://konvoy.vc/content/roblox-is-not-aging-up)
- [RoWatcher — 12 M concurrent](https://rowatcher.com/news/roblox-hit-12-million-concurrent-players-where-are-they-all-playing) · [Anime owns the charts (Aug 2026)](https://rowatcher.com/news/anime-owns-the-charts-again-week-of-august-15-2026) · [Fastest-growing, Mar 2026](https://rowatcher.com/news/the-10-fastest-growing-roblox-games-in-march-2026)

*Third-party player counts and revenue figures are model-based and often disagree; KPI benchmarks are industry estimates. Re-check live trackers and official Roblox docs before making decisions.*
