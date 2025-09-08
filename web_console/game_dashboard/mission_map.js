import React from 'https://esm.sh/react@18';

export default function MissionMap({ buttons }) {
  const [focusIndex, setFocusIndex] = React.useState(0);

  React.useEffect(() => {
    const btn = document.getElementById(buttons[focusIndex].id + '-btn');
    if (btn) btn.focus();
  }, [focusIndex, buttons]);

  React.useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'ArrowRight') setFocusIndex((i) => (i + 1) % buttons.length);
      if (e.key === 'ArrowLeft') setFocusIndex((i) => (i + buttons.length - 1) % buttons.length);
      if (e.key === 'Enter' || e.key === ' ') buttons[focusIndex].action();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [focusIndex, buttons]);

  React.useEffect(() => {
    let raf;
    const poll = () => {
      const [gp] = navigator.getGamepads ? navigator.getGamepads() : [];
      if (gp) {
        if (gp.buttons[14]?.pressed) setFocusIndex((i) => (i + buttons.length - 1) % buttons.length);
        if (gp.buttons[15]?.pressed) setFocusIndex((i) => (i + 1) % buttons.length);
        if (gp.buttons[0]?.pressed) buttons[focusIndex].action();
      }
      raf = requestAnimationFrame(poll);
    };
    window.addEventListener('gamepadconnected', poll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('gamepadconnected', poll);
    };
  }, [focusIndex, buttons]);

  return React.createElement(
    'div',
    { className: 'mission-map' },
    buttons.map((btn) =>
      React.createElement(
        'button',
        {
          id: btn.id + '-btn',
          key: btn.id,
          onClick: btn.action
        },
        btn.label
      )
    )
  );
}

