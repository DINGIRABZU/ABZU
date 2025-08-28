import React, { useState } from 'react';
import personas from '../personas.js';

export default function Channel({ floor, name, socket, messages }) {
  const [input, setInput] = useState('');
  const room = { floor, channel: name };
  const persona = personas[name] || {
    avatar: '❓',
    color: 'bg-gray-100',
    text: 'text-gray-800',
  };

  const send = () => {
    if (input.trim()) {
      socket.emit('message', { ...room, message: input });
      setInput('');
    }
  };

  return (
    <div className={`border rounded p-2 w-40 ${persona.color} ${persona.text}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xl">{persona.avatar}</span>
        <div className="font-semibold">{name}</div>
      </div>
      <input
        className="border w-full p-1"
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
      <div className="mt-2 h-24 overflow-y-auto text-sm">
        {messages.map((m, idx) => (
          <div key={idx}>{m.message}</div>
        ))}
      </div>
    </div>
  );
}
