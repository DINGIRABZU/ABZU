import React, { useState } from 'react';

export default function Channel({ floor, name, socket }) {
  const [input, setInput] = useState('');
  const room = { floor, channel: name };

  const send = () => {
    if (input.trim()) {
      socket.emit('message', { ...room, message: input });
      setInput('');
    }
  };

  return (
    <div className="border rounded p-2 w-40">
      <div className="font-semibold">{name}</div>
      <input
        className="border w-full p-1 mt-1"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="message"
      />
      <button
        className="mt-1 bg-blue-500 text-white px-2 py-1 rounded"
        onClick={send}
      >
        send
      </button>
    </div>
  );
}
