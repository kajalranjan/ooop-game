"""ooop — play Swoop online with friends. Run with:  streamlit run app.py"""
import html

import streamlit as st

from game import (JOKER, TARGET, WILD, Store, cards_left, deck_setup,
                  rank_name, top_run, MIN_PLAYERS, MAX_PLAYERS)

st.set_page_config(page_title="ooop", page_icon="●", layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_resource
def get_store():
    return Store()  # one shared store for every visitor


store = get_store()

# ---------------------------------------------------------------- look & feel
# Each "suit" is a colour + shape, so colour is never the only clue.
SUITS = {0: ("●", "#1d4ed8"), 1: ("▲", "#b91c1c"), 2: ("■", "#15803d"),
         3: ("◆", "#7e22ce"), 4: ("★", "#b45309"), "J": ("✦", "#111827")}

suit_css = "\n".join(
    f'div[class*="st-key-c_"][class*="_suit{k}"] button p {{ color: {c} !important; }}'
    for k, (_, c) in SUITS.items())

st.markdown(f"""
<style>
html, body, [class*="css"] {{ font-size: 18px; }}
.block-container {{ padding-top: 1.2rem; max-width: 1400px; }}
.title {{ font-size: 4.2rem; font-weight: 800; letter-spacing: -0.05em; line-height: 1; margin: 0; }}
.title span {{ color: #1d4ed8; }}
.sub {{ font-size: 1.2rem; color: #4b5563; margin: .3rem 0 1.4rem; }}
.code {{ font-size: 3.2rem; font-weight: 800; letter-spacing: .25em; font-family: ui-monospace, monospace;
        background: #f3f4f6; border: 2px dashed #9ca3af; border-radius: 14px; padding: .3rem 1rem;
        display: inline-block; }}
.banner {{ padding: .8rem 1.1rem; border-radius: 12px; font-size: 1.35rem; font-weight: 700; margin: .4rem 0 .8rem; }}
.banner.me {{ background: #dcfce7; border: 3px solid #15803d; color: #14532d; }}
.banner.wait {{ background: #f3f4f6; border: 2px solid #d1d5db; color: #374151; }}
.banner.mystery {{ background: #fef3c7; border: 3px solid #b45309; color: #78350f; }}
.label {{ font-size: 1.05rem; font-weight: 700; color: #374151; margin: .6rem 0 .3rem; }}

/* static cards (pile, opponents) */
.pc {{ display: inline-flex; flex-direction: column; align-items: center; justify-content: center;
      background: #fff; border: 2px solid #1f2937; border-radius: 12px; box-shadow: 0 2px 0 #1f2937;
      font-weight: 800; position: relative; vertical-align: top; }}
.pc .r {{ line-height: 1; }}
.pc .w {{ position: absolute; bottom: 3px; font-size: .55rem; letter-spacing: .08em; text-transform: uppercase; color: #6b7280; }}
.pc.lg {{ width: 92px; height: 128px; }} .pc.lg .r {{ font-size: 2.6rem; }} .pc.lg .s {{ font-size: 1.5rem; }}
.pc.sm {{ width: 40px; height: 56px; border-radius: 8px; }} .pc.sm .r {{ font-size: 1.05rem; }} .pc.sm .s {{ font-size: .7rem; }}
.pc.sm .w {{ display: none; }}
.pc.slot {{ width: 100%; height: 92px; }} .pc.slot .r {{ font-size: 1.9rem; }} .pc.slot .s {{ font-size: 1.1rem; }}
.pc.jk .r {{ font-size: 45% !important; letter-spacing: .05em; }}
.pc.lg.jk .r {{ font-size: 1.15rem !important; }}
.pc.back {{ background: repeating-linear-gradient(45deg,#1f2937 0 8px,#374151 8px 16px); color: #fff; }}
.pc.empty {{ background: transparent; border: 2px dashed #d1d5db; box-shadow: none; }}
.pc.reveal {{ outline: 4px solid #b45309; outline-offset: 2px; }}
.fan {{ display: flex; align-items: flex-end; min-height: 136px; padding: 4px 0; }}
.fan .pc + .pc {{ margin-left: -46px; }}
.pile-box {{ background: #f9fafb; border: 2px solid #e5e7eb; border-radius: 16px; padding: .8rem 1.1rem; margin-bottom: .6rem; }}
.pile-info {{ font-size: 1.15rem; color: #111827; margin-top: .3rem; }}

.opps {{ display: flex; flex-wrap: wrap; gap: .6rem; margin-bottom: .6rem; }}
.opp {{ border: 2px solid #e5e7eb; border-radius: 14px; padding: .5rem .7rem; background: #fff; min-width: 200px; }}
.opp.turn {{ border: 3px solid #15803d; background: #f0fdf4; }}
.opp .nm {{ font-weight: 800; font-size: 1.15rem; }}
.opp .meta {{ color: #374151; font-size: .95rem; margin-bottom: .3rem; }}
.opp .row {{ display: flex; gap: 4px; margin-top: 4px; }}

table.sc {{ width: 100%; border-collapse: collapse; font-size: 1.05rem; }}
table.sc td, table.sc th {{ padding: .35rem .4rem; border-bottom: 1px solid #e5e7eb; text-align: left; }}
table.sc th {{ color: #6b7280; font-weight: 600; font-size: .9rem; }}
table.sc tr.turn td {{ font-weight: 800; background: #f0fdf4; }}
table.sc td.num, table.sc th.num {{ text-align: right; }}
.log {{ font-size: .98rem; color: #374151; line-height: 1.5; }}
.log div {{ border-bottom: 1px solid #f3f4f6; padding: .15rem 0; }}

/* tappable cards */
div[class*="st-key-c_"] button {{ min-height: 92px; background: #fff; border: 2px solid #1f2937;
      border-radius: 12px; box-shadow: 0 2px 0 #1f2937; padding: 2px; transition: transform .08s; }}
div[class*="st-key-c_"] button p {{ font-size: 1.9rem; font-weight: 800; line-height: 1.1; }}
div[class*="st-key-c_"] button:hover {{ border-color: #1d4ed8; background: #fff; }}
div[class*="st-key-c_"] button[data-testid="stBaseButton-primary"],
div[class*="st-key-c_"] button[data-testid="stBaseButton-primary"]:hover {{
      background: #fde68a; border: 4px solid #111827; transform: translateY(-8px); box-shadow: 0 6px 0 #111827; }}
div[class*="_suitJ"] button p {{ font-size: 1.05rem !important; letter-spacing: .05em; }}
div[class*="st-key-c_d"] button {{ background: repeating-linear-gradient(45deg,#1f2937 0 8px,#374151 8px 16px); }}
div[class*="st-key-c_d"] button p {{ color: #fff !important; }}
div[class*="st-key-c_d"] button:hover {{ background: #374151; border-color: #b45309; }}
{suit_css}

/* keep card rows side by side on phones */
div[class*="st-key-row_"] div[data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: .4rem; }}
div[class*="st-key-row_"] div[data-testid="stColumn"] {{ min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }}

/* big, friendly action buttons */
div[class*="st-key-act_"] button {{ min-height: 3.2rem; font-size: 1.2rem; font-weight: 700; border-radius: 12px; }}
div[class*="st-key-act_"] button p {{ font-size: 1.2rem; font-weight: 700; }}

@media (max-width: 640px) {{
  .title {{ font-size: 3rem; }}
  div[class*="st-key-c_"] button {{ min-height: 66px; }}
  div[class*="st-key-c_"] button p {{ font-size: 1.2rem; }}
  .pc.slot {{ height: 66px; }} .pc.slot .r {{ font-size: 1.2rem; }}
  .pc.lg {{ width: 70px; height: 98px; }} .pc.lg .r {{ font-size: 2rem; }}
  .fan .pc + .pc {{ margin-left: -40px; }}
}}
</style>
""", unsafe_allow_html=True)


def esc(s):
    return html.escape(str(s))


def card_label(c):
    sym = SUITS[c["suit"]][0]
    return f"JOKER {sym}" if c["rank"] == JOKER else f"{c['rank']} {sym}"


def card_html(c, size="lg", extra=""):
    sym, col = SUITS[c["suit"]]
    jk = c["rank"] == JOKER
    r = "JOKER" if jk else c["rank"]
    wild = '<div class="w">swoop</div>' if c["rank"] in WILD else ""
    cls = f"pc {size} {'jk' if jk else ''} {extra}"
    return (f'<div class="{cls}" style="color:{col}"><div class="r">{r}</div>'
            f'<div class="s">{sym}</div>{wild}</div>')


def back_html(size="lg"):
    return f'<div class="pc back {size}"><div class="r">?</div></div>'


def empty_html(size="lg"):
    return f'<div class="pc empty {size}"></div>'


def sort_key(c):
    order = {"10": 98, JOKER: 99}
    rank = order.get(c["rank"], None) or ["1", "2", "3", "4", "5", "6", "7", "8", "9",
                                          "J", "Q", "K"].index(c["rank"]) + 1
    return (rank, str(c["suit"]))


# ---------------------------------------------------------------- session
ss = st.session_state
ss.setdefault("sel", [])
ss.setdefault("flash", "")


def enter_room(code, name):
    ss.room, ss.name, ss.sel, ss.flash = code, name, [], ""
    st.query_params.update(room=code, name=name)


def exit_room():
    for k in ("room", "name"):
        ss.pop(k, None)
    ss.sel = []
    st.query_params.clear()


# A refreshed browser tab keeps its place through the URL.
if "room" not in ss:
    qp_room, qp_name = st.query_params.get("room"), st.query_params.get("name")
    if qp_room and qp_name:
        ok, _, code, name = store.join_room(qp_room, qp_name)
        if ok:
            enter_room(code, name)
        else:
            st.query_params.clear()


# ---------------------------------------------------------------- home
def home():
    _, mid, _ = st.columns([1, 2.2, 1])
    with mid:
        st.markdown('<p class="title">ooop<span>.</span></p>'
                    '<p class="sub">Swoop with friends. No sign-up — just a nickname.</p>',
                    unsafe_allow_html=True)
        nick = st.text_input("Your nickname", max_chars=16, placeholder="e.g. Grandma Jo").strip()
        st.write("")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("### Start a new game")
            size = st.selectbox("How many people are playing (including you)?",
                                list(range(MIN_PLAYERS, MAX_PLAYERS + 1)), index=1)
            decks, suits = deck_setup(size)
            st.caption(f"Uses {decks} decks" + (" with a fifth suit (party mode)." if suits == 5 else "."))
            if st.button("Create room", type="primary", key="act_create", use_container_width=True):
                if not nick:
                    st.error("Please type a nickname first.")
                else:
                    code = store.create_room(nick, size)
                    enter_room(code, nick)
                    st.rerun()
        with right:
            st.markdown("### Join a game")
            code_in = st.text_input("Room code", max_chars=5, placeholder="ABCDE").strip().upper()
            st.caption("Rejoining? Use the same nickname you played with.")
            if st.button("Join room", key="act_join", use_container_width=True):
                if not nick:
                    st.error("Please type a nickname first.")
                elif not code_in:
                    st.error("Please type the room code.")
                else:
                    ok, msg, code, name = store.join_room(code_in, nick)
                    if ok:
                        enter_room(code, name)
                        st.rerun()
                    else:
                        st.error(msg)
        with st.expander("How to play Swoop"):
            st.markdown(f"""
- Everyone gets **11 cards in hand, 4 face-up and 4 face-down** (mystery) cards.
- On your turn play **1–4 cards of the same rank** from your hand and/or face-up cards.
- **Equal or lower** than the top of the pile: it goes on the pile.
  **Higher**: you pick up the whole pile (including what you played) and your turn ends.
- **10s and Jokers** can be played any time — they **swoop** the pile away and you go again.
- Making the **top four cards the same rank** is also a swoop. You may never make more than four.
- A mystery card unlocks when the card above it is gone. Flip it at the start of a turn; you must play it.
- When someone runs out, everyone else scores what they still hold:
  1 = 1 point, 2–9 face value, J/Q/K = 10, 10s and Jokers = 50.
- The session ends when someone reaches **{TARGET}**. **Lowest score wins.**
""")


# ---------------------------------------------------------------- room views
def lobby(room, me):
    st.markdown('<p class="title" style="font-size:2.6rem">ooop<span>.</span></p>', unsafe_allow_html=True)
    st.markdown("**Share this room code with the other players:**")
    st.markdown(f'<div class="code">{esc(room["code"])}</div>', unsafe_allow_html=True)
    n, size = len(room["players"]), room["size"]
    st.markdown(f"### Players joined: {n} of {size}")
    for p in room["players"]:
        tag = " (host)" if p["name"] == room["host"] else ""
        you = " — you" if p["name"] == me else ""
        st.markdown(f"- **{esc(p['name'])}**{tag}{you}")
    is_host = room["host"] == me
    c1, c2, _ = st.columns([1.3, 1, 2])
    with c1:
        if is_host:
            label = "Start game" if n == size else f"Waiting for {size - n} more…"
            if st.button(label, type="primary", disabled=n != size, key="act_start", use_container_width=True):
                ok, msg = store.start_game(room["code"], me)
                if not ok:
                    st.error(msg)
                st.rerun()
        else:
            st.info("Waiting for the host to start the game.")
    with c2:
        if st.button("Leave room", key="act_leave", use_container_width=True):
            store.leave_room(room["code"], me)
            exit_room()
            st.rerun()


def toggle(ref):
    if ref in ss.sel:
        ss.sel.remove(ref)
    else:
        ss.sel.append(ref)


def do_play(code, name, has_mystery):
    hand_ids = [r for k, r in ss.sel if k == "h"]
    up_slots = [r for k, r in ss.sel if k == "u"]
    ok, msg = store.play(code, name, hand_ids, up_slots)
    if ok:
        ss.sel = []
        ss.flash = ""
    else:
        ss.flash = msg


def do_flip(code, name, slot):
    ok, msg = store.flip(code, name, slot)
    ss.sel = []
    ss.flash = "" if ok else msg


def pile_view(room):
    pile = room["pile"]
    if not pile:
        inner = '<div class="pile-info"><b>The pile is empty.</b> Any card starts a new pile.</div>'
        fan = f'<div class="fan">{empty_html("lg")}</div>'
    else:
        shown = pile[-8:]
        fan = '<div class="fan">' + "".join(card_html(c, "lg") for c in shown) + "</div>"
        top = pile[-1]["rank"]
        run = top_run(pile, top)
        word = {1: "one", 2: "two", 3: "three"}.get(run, str(run))
        inner = (f'<div class="pile-info">Top card: <b>{esc(rank_name(top))}</b> '
                 f'({word} on top) · {len(pile)} card{"s" if len(pile) != 1 else ""} in the pile. '
                 f'Play <b>{esc(rank_name(top))} or lower</b>, or a 10 / Joker.</div>')
    st.markdown(f'<div class="pile-box"><div class="label" style="margin-top:0">Play pile</div>{fan}{inner}</div>',
                unsafe_allow_html=True)


def opponents_view(room, my_i):
    n = len(room["players"])
    rev = room["revealed"]
    blocks = []
    for k in range(1, n):
        j = (my_i + k) % n
        p = room["players"][j]
        ups = "".join(card_html(c, "sm") if c else empty_html("sm") for c in p["up"])
        downs = ""
        for s, c in enumerate(p["down"]):
            if c is None:
                downs += empty_html("sm")
            elif rev and rev["player"] == j and rev["slot"] == s:
                downs += card_html(c, "sm", "reveal")
            else:
                downs += back_html("sm")
        cls = "opp turn" if room["turn"] == j else "opp"
        arrow = " ▶ playing" if room["turn"] == j else ""
        blocks.append(f'<div class="{cls}"><div class="nm">{esc(p["name"])}{arrow}</div>'
                      f'<div class="meta">{len(p["hand"])} in hand · {cards_left(p)} cards left</div>'
                      f'<div class="row">{ups}</div><div class="row">{downs}</div></div>')
    st.markdown(f'<div class="label">Other players (in turn order)</div><div class="opps">{"".join(blocks)}</div>',
                unsafe_allow_html=True)


def side_panel(room):
    rows = ""
    for i, p in enumerate(room["players"]):
        cls = ' class="turn"' if room["turn"] == i and room["status"] == "playing" else ""
        rows += (f'<tr{cls}><td>{esc(p["name"])}</td><td class="num">{cards_left(p)}</td>'
                 f'<td class="num">{p["total"]}</td></tr>')
    st.markdown(f'<div class="label">Scores — round {room["round"]} · first to {TARGET} ends it, lowest wins</div>'
                f'<table class="sc"><tr><th>Player</th><th class="num">Cards</th><th class="num">Points</th></tr>'
                f'{rows}</table>', unsafe_allow_html=True)
    log = "".join(f"<div>{esc(x)}</div>" for x in reversed(room["log"]))
    st.markdown(f'<div class="label">What just happened</div><div class="log">{log}</div>',
                unsafe_allow_html=True)
    st.caption(f"Room code: {room['code']}")


def card_row(items, row_key, per_row):
    """items: list of (kind, ref, card or None, mode). mode: 'tap', 'flip', 'html'."""
    for start in range(0, max(len(items), 1), per_row):
        chunk = items[start:start + per_row]
        with st.container(key=f"{row_key}_{start}"):
            cols = st.columns(per_row)
            for col, (kind, ref, html_or_card, mode) in zip(cols, chunk):
                with col:
                    if mode == "tap":
                        c = html_or_card
                        st.button(card_label(c), key=f"c_{kind}{ref}_suit{c['suit']}",
                                  type="primary" if (kind, ref) in ss.sel else "secondary",
                                  on_click=toggle, args=((kind, ref),), use_container_width=True)
                    elif mode == "flip":
                        st.button("?", key=f"c_d{ref}_back", on_click=html_or_card[0],
                                  args=html_or_card[1], use_container_width=True,
                                  help="Flip this mystery card and play it")
                    else:
                        st.markdown(html_or_card, unsafe_allow_html=True)


def table_view(room, me):
    code = room["code"]
    my_i = next(i for i, p in enumerate(room["players"]) if p["name"] == me)
    p = room["players"][my_i]
    my_turn = room["turn"] == my_i
    rev = room["revealed"] if room["revealed"] and room["revealed"]["player"] == my_i else None

    # drop stale selections
    hand_ids = {c["id"] for c in p["hand"]}
    ss.sel = [(k, r) for k, r in ss.sel
              if (k == "h" and r in hand_ids) or (k == "u" and p["up"][r] is not None)]

    main, side = st.columns([3, 1.1], gap="large")
    with main:
        if rev:
            r = rank_name(rev["card"]["rank"])
            st.markdown(f'<div class="banner mystery">Your mystery card is a {esc(r)}. You must play it — '
                        f'tap any other {esc(r)}s to add them, then press Play.</div>', unsafe_allow_html=True)
        elif my_turn:
            st.markdown('<div class="banner me">Your turn — tap the cards you want to play, then press Play.</div>',
                        unsafe_allow_html=True)
        else:
            who = room["players"][room["turn"]]["name"]
            st.markdown(f'<div class="banner wait">Waiting for {esc(who)} to play…</div>', unsafe_allow_html=True)

        opponents_view(room, my_i)
        pile_view(room)

        # actions
        a1, a2, _ = st.columns([1.4, 1, 1.6])
        with a1:
            n_sel = len(ss.sel) + (1 if rev else 0)
            label = "Play mystery card" if rev and not ss.sel else (f"Play {n_sel} card{'s' if n_sel != 1 else ''}"
                                                                   if n_sel else "Play")
            st.button(label, type="primary", key="act_play", use_container_width=True,
                      disabled=not my_turn or n_sel == 0,
                      on_click=do_play, args=(code, me, bool(rev)))
        with a2:
            st.button("Clear", key="act_clear", use_container_width=True, disabled=not ss.sel,
                      on_click=lambda: ss.update(sel=[], flash=""))
        if ss.flash:
            st.error(ss.flash)

        # my table cards
        st.markdown('<div class="label">Your face-up cards</div>', unsafe_allow_html=True)
        ups = [("u", s, c, "tap") if c else ("u", s, empty_html("slot"), "html") for s, c in enumerate(p["up"])]
        card_row(ups, "row_up", 4)

        st.markdown('<div class="label">Your mystery cards (unlock when the card above is played)</div>',
                    unsafe_allow_html=True)
        downs = []
        for s, c in enumerate(p["down"]):
            if c is None:
                downs.append(("d", s, empty_html("slot"), "html"))
            elif rev and rev["slot"] == s:
                downs.append(("d", s, card_html(c, "slot", "reveal"), "html"))
            elif my_turn and not rev and p["up"][s] is None:
                downs.append(("d", s, (do_flip, (code, me, s)), "flip"))
            else:
                downs.append(("d", s, back_html("slot"), "html"))
        card_row(downs, "row_down", 4)

        st.markdown(f'<div class="label">Your hand ({len(p["hand"])} cards)</div>', unsafe_allow_html=True)
        hand = sorted(p["hand"], key=sort_key)
        if hand:
            card_row([("h", c["id"], c, "tap") for c in hand], "row_hand", 7)
        else:
            st.caption("No cards in hand — play your face-up cards, then your mystery cards.")
    with side:
        side_panel(room)


def results_table(room, show_round=True):
    players = sorted(room["players"], key=lambda p: p["total"])
    rows = ""
    for place, p in enumerate(players, 1):
        rnd = f'<td class="num">+{p["last"]}</td>' if show_round else ""
        rows += f'<tr><td>{place}</td><td>{esc(p["name"])}</td>{rnd}<td class="num">{p["total"]}</td></tr>'
    head = '<th class="num">This round</th>' if show_round else ""
    st.markdown(f'<table class="sc" style="font-size:1.25rem"><tr><th>#</th><th>Player</th>{head}'
                f'<th class="num">Total</th></tr>{rows}</table>', unsafe_allow_html=True)


def round_over_view(room, me):
    st.markdown(f'<div class="banner me">{esc(room["round_winner"])} went out! Round {room["round"]} is over.</div>',
                unsafe_allow_html=True)
    results_table(room)
    nxt = room["players"][(room["starter"] + 1) % len(room["players"])]["name"]
    st.write("")
    st.markdown(f"Next round, **{esc(nxt)}** goes first. The session ends when someone reaches {TARGET}.")
    if room["host"] == me:
        if st.button("Deal next round", type="primary", key="act_next"):
            store.next_round(room["code"], me)
            ss.sel = []
            st.rerun()
    else:
        st.info("Waiting for the host to deal the next round.")


def finished_view(room, me):
    players = sorted(room["players"], key=lambda p: p["total"])
    best = players[0]["total"]
    winners = ", ".join(p["name"] for p in players if p["total"] == best)
    st.markdown('<p class="title" style="font-size:2.6rem">Game over</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="banner me">🏆 {esc(winners)} win{"s" if "," not in winners else ""} '
                f'with the lowest score ({best}).</div>', unsafe_allow_html=True)
    st.markdown("### Final leaderboard")
    results_table(room)
    st.write("")
    st.caption("This session is over. To play again, create a new room.")
    if st.button("Back to start", type="primary", key="act_home"):
        exit_room()
        st.rerun()


@st.fragment(run_every=2)
def room_view():
    room = store.snapshot(ss.get("room"))
    me = ss.get("name")
    if room is None or not any(p["name"] == me for p in room["players"]):
        st.warning("This room no longer exists (it may have expired or the server restarted).")
        if st.button("Back to start", key="act_gone"):
            exit_room()
            st.rerun()
        return
    status = room["status"]
    if status == "lobby":
        lobby(room, me)
    elif status == "playing":
        table_view(room, me)
    elif status == "round_over":
        round_over_view(room, me)
    else:
        finished_view(room, me)


if "room" in ss:
    room_view()
else:
    home()
