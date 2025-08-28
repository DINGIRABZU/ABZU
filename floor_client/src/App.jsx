import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import Floor from './components/Floor.jsx';

const floors = {
  ground: ['alpha', 'beta'],
  first: ['gamma', 'delta'],
};

const socket = io('http://localhost:8000/ws');

export default function App() {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    socket.on('message', (data) => {
      setMessages((m) => [...m, data]);
    });
    return () => {
      socket.off('message');
    };
  }, []);

  return (
    <div className="p-4 space-y-4">
      {Object.entries(floors).map(([floor, channels]) => (
        <Floor
          key={floor}
          name={floor}
          channels={channels}
          socket={socket}
          messages={messages}
        />
      ))}
    </div>
  );
}
