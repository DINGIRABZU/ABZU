# Floor Client UI

This React/Tailwind interface renders floors with channel tiles and streams messages over a WebSocket feed.

## Build Steps

1. Install dependencies:
   ```bash
   cd floor_client
   npm install
   ```
   This creates `node_modules/`, which is excluded from version control.
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Create a production build:
   ```bash
   npm run build
   ```
4. Preview the built assets:
   ```bash
   npm run preview
   ```

## Architecture

```
App → Floor → Channel
```

- **App** establishes the WebSocket connection and collects incoming messages.
- **Floor** receives the full message list and filters messages for each channel on that floor.
- **Channel** renders an input box and a scrolling feed of messages for its channel.

Channel tiles use persona metadata defined in `personas.js` to show avatars and color themes.

## UI Walkthrough

1. Floors are displayed in vertical sections. Each section lists its channels horizontally.
2. Every channel shows an emoji avatar, persona color styling, an input box and a message log.
3. Messages sent from any channel are emitted over the WebSocket and appear instantly in the matching channel feed.
4. The interface can be extended by editing `personas.js` to add new avatars or themes.

