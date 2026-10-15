# ooop — a game

A free, just-for-fun multiplayer Swoop card game built with Streamlit.
No logins: players pick a nickname, the host creates a room, and everyone else joins with the 5-letter code.

## Files

| File | What it does |
|---|---|
| `app.py` | The website: home screen, lobby, game table, round results, final leaderboard |
| `game.py` | The rules engine: dealing, plays, swoops, mystery cards, scoring |
| `requirements.txt` | Tells Streamlit Cloud what to install |
| `.streamlit/config.toml` | Colours and theme |

## Put it online (Streamlit Community Cloud, free)

1. Create a free account at https://github.com and make a new **public** repository called `ooop`.
2. Upload all the files in this folder, keeping the `.streamlit` folder as it is.
   On GitHub: **Add file → Upload files**, drag everything in, then **Commit changes**.
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click **Create app → Deploy a public app from GitHub**, choose your `ooop` repository,
   branch `main`, main file `app.py`.
5. Under **App URL**, type `ooop` (or another name if that one is taken), then click **Deploy**.

After a minute you'll get a link like `https://ooop.streamlit.app` to share with friends.

## Try it on your own computer first (optional)

```
pip install -r requirements.txt
streamlit run app.py
```

Open the address it prints in a few browser tabs to play against yourself.

## How rooms work

- Room size is chosen by the host (3–12 players). The host can start once everyone has joined.
- Decks: 3–4 players use 2 decks, 5–6 use 3, 7–8 use 4, and 9–12 use 4 decks with a fifth suit.
  Every player gets 11 hand cards, 4 face-up and 4 mystery cards; leftover cards are set aside.
- Every deal uses a fresh cryptographic shuffle, and all hands are dealt before anyone plays.
- The host goes first in round 1; the first player moves one seat clockwise each round.
- The session ends when someone reaches 300 points; the lowest score wins.
- **Rejoining:** refreshing the page keeps you in your seat. On another device, choose
  **Join a game** with the same room code and the exact same nickname.

## Good to know

- Rooms are kept in the app's memory. If Streamlit restarts the app or puts it to sleep
  (after a few days with no visitors), games in progress are lost and players need a new room.
- Screens update about every 2 seconds, so other players' moves appear shortly after they happen.
- Idle rooms are cleared automatically after 12 hours.
