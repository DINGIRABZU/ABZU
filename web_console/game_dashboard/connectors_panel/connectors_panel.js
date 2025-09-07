import React from 'https://esm.sh/react@18';

function ensureBus() {
  const g = globalThis;
  if (!g.signalBus) {
    g.signalBus = {
      _subs: {},
      publish(ch, payload) {
        (this._subs[ch] || []).forEach((cb) => cb(payload));
      },
      subscribe(ch, cb) {
        (this._subs[ch] = this._subs[ch] || []).push(cb);
        return () => {
          this._subs[ch] = (this._subs[ch] || []).filter((f) => f !== cb);
        };
      }
    };
  }
  return g.signalBus;
}

export default function ConnectorsPanel({ bus } = {}) {
  const signalBus = bus || ensureBus();
  const [status, setStatus] = React.useState({});

  React.useEffect(() => {
    const unsub = signalBus.subscribe('connectors', (evt) => {
      setStatus((s) => ({ ...s, [evt.name]: evt.status }));
    });
    return () => unsub();
  }, [signalBus]);

  function restart(name) {
    signalBus.publish('connectors:restart', { name });
  }
  function mute(name) {
    signalBus.publish('connectors:mute', { name });
  }

  return React.createElement(
    'div',
    { id: 'connectors-panel' },
    React.createElement('h3', null, 'Connectors'),
    React.createElement(
      'div',
      { className: 'connector-rows' },
      Object.entries(status).map(([name, s]) =>
        React.createElement(
          'div',
          { key: name, className: 'connector-row' },
          React.createElement('span', { className: 'connector-name' }, name),
          React.createElement('span', { className: 'connector-status' }, s),
          React.createElement(
            'button',
            { onClick: () => restart(name) },
            'Restart'
          ),
          React.createElement(
            'button',
            { onClick: () => mute(name) },
            'Mute'
          )
        )
      )
    )
  );
}
