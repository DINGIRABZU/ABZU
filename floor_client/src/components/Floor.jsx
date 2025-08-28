import React from 'react';
import Channel from './Channel.jsx';

export default function Floor({ name, channels, socket, messages }) {
  return (
    <div className="border rounded p-2">
      <h2 className="font-bold mb-2">{name}</h2>
      <div className="flex gap-2">
        {channels.map((ch) => (
          <Channel
            key={ch}
            floor={name}
            name={ch}
            socket={socket}
            messages={messages.filter((m) => m.floor === name && m.channel === ch)}
          />
        ))}
      </div>
    </div>
  );
}
