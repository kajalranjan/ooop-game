"""Swoop rules engine and shared room storage for ooop.

All game state lives on the server. Players only ever see what the UI chooses
to render for them, so nobody can peek at another player's cards.
"""
import copy
import secrets
import threading
import time

RANKS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
JOKER = "JK"
RANK_ORDER = {r: i + 1 for i, r in enumerate(RANKS)}
RANK_ORDER[JOKER] = 99
WILD = {"10", JOKER}          # always playable, always swoops
TARGET = 300                  # first to reach this ends the session
HAND, UP, DOWN = 11, 4, 4     # 19 cards per player
MIN_PLAYERS, MAX_PLAYERS = 3, 12
ROOM_TTL = 12 * 3600          # forget idle rooms after 12 hours

_rng = secrets.SystemRandom()  # cryptographic randomness for every shuffle


def card_points(rank):
    if rank in WILD:
        return 50
    if rank in ("J", "Q", "K"):
        return 10
    return int(rank)


def rank_name(rank):
    return "Joker" if rank == JOKER else rank


def deck_setup(n_players):
    """(number of decks, suits per deck)."""
    if n_players <= 4:
        return 2, 4
    if n_players <= 6:
        return 3, 4
    if n_players <= 8:
        return 4, 4
    return 4, 5  # party mode: fifth suit added


def build_shoe(n_players):
    decks, suits = deck_setup(n_players)
    cards = []
    for _ in range(decks):
        for s in range(suits):
            for r in RANKS:
                cards.append({"rank": r, "suit": s})
        cards.append({"rank": JOKER, "suit": "J"})
        cards.append({"rank": JOKER, "suit": "J"})
    for i, c in enumerate(cards):
        c["id"] = i
    _rng.shuffle(cards)
    return cards


def top_run(pile, rank):
    """How many cards of `rank` sit consecutively on top of the pile."""
    n = 0
    for c in reversed(pile):
        if c["rank"] != rank:
            break
        n += 1
    return n


def cards_left(p):
    return (len(p["hand"]) + sum(c is not None for c in p["up"])
            + sum(c is not None for c in p["down"]))


def points_left(p):
    cards = p["hand"] + [c for c in p["up"] if c] + [c for c in p["down"] if c]
    return sum(card_points(c["rank"]) for c in cards)


def _describe(cards):
    r = rank_name(cards[0]["rank"])
    return r if len(cards) == 1 else f"{len(cards)} × {r}"


class Store:
    """In-memory rooms shared by every visitor of the Streamlit app."""

    def __init__(self):
        self.lock = threading.RLock()
        self.rooms = {}

    # ---------- helpers ----------
    def _code(self):
        alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
        while True:
            code = "".join(_rng.choice(alphabet) for _ in range(5))
            if code not in self.rooms:
                return code

    def _purge(self):
        now = time.time()
        for code in [c for c, r in self.rooms.items() if now - r["last_active"] > ROOM_TTL]:
            del self.rooms[code]

    @staticmethod
    def _idx(room, name):
        for i, p in enumerate(room["players"]):
            if p["name"].lower() == name.lower():
                return i
        return None

    @staticmethod
    def _log(room, text):
        room["log"].append(text)
        room["log"] = room["log"][-12:]

    def _get(self, code):
        room = self.rooms.get((code or "").upper().strip())
        if room:
            room["last_active"] = time.time()
        return room

    @staticmethod
    def _new_player(name):
        return {"name": name, "hand": [], "up": [None] * UP, "down": [None] * DOWN,
                "total": 0, "last": 0}

    # ---------- lobby ----------
    def create_room(self, host, size):
        size = max(MIN_PLAYERS, min(MAX_PLAYERS, int(size)))
        with self.lock:
            self._purge()
            code = self._code()
            self.rooms[code] = {
                "code": code, "host": host, "size": size, "status": "lobby",
                "players": [self._new_player(host)], "round": 0, "starter": 0,
                "turn": 0, "pile": [], "discarded": 0, "revealed": None,
                "log": [], "round_winner": None, "last_active": time.time(),
            }
            return code

    def join_room(self, code, name):
        """Returns (ok, message, canonical_code, canonical_name)."""
        with self.lock:
            room = self._get(code)
            if not room:
                return False, "No room with that code. Check it and try again.", None, None
            i = self._idx(room, name)
            if i is not None:  # rejoin with same nickname
                return True, "", room["code"], room["players"][i]["name"]
            if room["status"] != "lobby":
                return False, "That game has already started. To rejoin, use the exact nickname you played with.", None, None
            if len(room["players"]) >= room["size"]:
                return False, "That room is full.", None, None
            room["players"].append(self._new_player(name))
            return True, "", room["code"], name

    def leave_room(self, code, name):
        with self.lock:
            room = self._get(code)
            if not room or room["status"] != "lobby":
                return
            i = self._idx(room, name)
            if i is None:
                return
            room["players"].pop(i)
            if not room["players"]:
                del self.rooms[room["code"]]
            elif room["host"].lower() == name.lower():
                room["host"] = room["players"][0]["name"]

    def snapshot(self, code):
        with self.lock:
            room = self._get(code)
            return copy.deepcopy(room) if room else None

    # ---------- game flow ----------
    def _deal(self, room):
        shoe = build_shoe(len(room["players"]))
        pos = 0
        for p in room["players"]:
            p["down"] = shoe[pos:pos + DOWN]; pos += DOWN
            p["up"] = shoe[pos:pos + UP]; pos += UP
            p["hand"] = shoe[pos:pos + HAND]; pos += HAND
            p["last"] = 0
        # cards beyond pos are simply set aside
        room.update(pile=[], discarded=0, revealed=None, round_winner=None,
                    status="playing", turn=room["starter"], log=[])
        room["round"] += 1
        self._log(room, f"Round {room['round']} — {room['players'][room['starter']]['name']} goes first.")

    def start_game(self, code, name):
        with self.lock:
            room = self._get(code)
            if not room or room["status"] != "lobby":
                return False, "Game can't be started."
            if room["host"].lower() != name.lower():
                return False, "Only the host can start the game."
            if len(room["players"]) != room["size"]:
                return False, "Waiting for everyone to join."
            room["starter"] = 0  # host
            self._deal(room)
            return True, ""

    def next_round(self, code, name):
        with self.lock:
            room = self._get(code)
            if not room or room["status"] != "round_over":
                return False, ""
            if room["host"].lower() != name.lower():
                return False, "Only the host can deal the next round."
            room["starter"] = (room["starter"] + 1) % len(room["players"])
            self._deal(room)
            return True, ""

    def _check_turn(self, room, name):
        if not room or room["status"] != "playing":
            return None, "The game isn't in progress."
        i = self._idx(room, name)
        if i is None:
            return None, "You're not in this game."
        if room["turn"] != i:
            return None, "It's not your turn."
        return i, ""

    def flip(self, code, name, slot):
        with self.lock:
            room = self._get(code)
            i, err = self._check_turn(room, name)
            if i is None:
                return False, err
            p = room["players"][i]
            if room["revealed"]:
                return False, "You already flipped a mystery card — play it."
            if not (0 <= slot < DOWN) or p["down"][slot] is None:
                return False, "No mystery card there."
            if p["up"][slot] is not None:
                return False, "Play the face-up card on top of it first."
            card = p["down"][slot]
            room["revealed"] = {"player": i, "slot": slot, "card": card}
            self._log(room, f"{p['name']} flipped a mystery card: {rank_name(card['rank'])}.")
            return True, ""

    def play(self, code, name, hand_ids, up_slots):
        with self.lock:
            room = self._get(code)
            i, err = self._check_turn(room, name)
            if i is None:
                return False, err
            p = room["players"][i]
            rev = room["revealed"] if room["revealed"] and room["revealed"]["player"] == i else None
            hand_ids = list(dict.fromkeys(hand_ids))
            up_slots = list(dict.fromkeys(up_slots))
            in_hand = {c["id"]: c for c in p["hand"]}

            cards = [rev["card"]] if rev else []
            for h in hand_ids:
                if h not in in_hand:
                    return False, "That card is no longer in your hand."
                cards.append(in_hand[h])
            for s in up_slots:
                if not (0 <= s < UP) or p["up"][s] is None:
                    return False, "That table card is no longer there."
                cards.append(p["up"][s])

            if not cards:
                return False, "Tap one or more cards first."
            if len(cards) > 4:
                return False, "You can play at most four cards at once."
            if len({c["rank"] for c in cards}) != 1:
                if rev:
                    return False, f"Extra cards must match your mystery card ({rank_name(rev['card']['rank'])})."
                return False, "Cards played together must all be the same rank."

            rank = cards[0]["rank"]
            pile = room["pile"]
            higher = bool(pile) and rank not in WILD and RANK_ORDER[rank] > RANK_ORDER[pile[-1]["rank"]]
            if rank not in WILD and not higher and top_run(pile, rank) + len(cards) > 4:
                return False, (f"That would put more than four {rank_name(rank)}s on the pile. "
                               "Play fewer — reaching exactly four is a swoop.")

            # --- commit the play ---
            ids = set(hand_ids)
            p["hand"] = [c for c in p["hand"] if c["id"] not in ids]
            for s in up_slots:
                p["up"][s] = None
            if rev:
                p["down"][rev["slot"]] = None
                room["revealed"] = None

            desc = _describe(cards)
            again = False
            if rank in WILD:
                room["discarded"] += len(pile) + len(cards)
                room["pile"] = []
                self._log(room, f"{p['name']} played {desc} — SWOOP! {p['name']} goes again.")
                again = True
            elif higher:
                picked = pile + cards
                p["hand"].extend(picked)
                room["pile"] = []
                self._log(room, f"{p['name']} played {desc} on {rank_name(pile[-1]['rank'])} "
                                f"and picked up {len(picked)} cards.")
            else:
                pile.extend(cards)
                if top_run(pile, rank) >= 4:
                    room["discarded"] += len(pile)
                    room["pile"] = []
                    self._log(room, f"{p['name']} played {desc} — four {rank_name(rank)}s, SWOOP! "
                                    f"{p['name']} goes again.")
                    again = True
                else:
                    self._log(room, f"{p['name']} played {desc}.")

            if cards_left(p) == 0:
                self._end_round(room, i)
            elif not again:
                room["turn"] = (i + 1) % len(room["players"])
            return True, ""

    def _end_round(self, room, winner):
        for j, p in enumerate(room["players"]):
            pts = 0 if j == winner else points_left(p)
            p["last"] = pts
            p["total"] += pts
        room["round_winner"] = room["players"][winner]["name"]
        room["revealed"] = None
        self._log(room, f"{room['round_winner']} went out!")
        if any(p["total"] >= TARGET for p in room["players"]):
            room["status"] = "finished"
        else:
            room["status"] = "round_over"
