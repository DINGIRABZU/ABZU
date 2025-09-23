import React from 'https://esm.sh/react@18';

export default function MissionMap({ stages }) {
  const flattened = React.useMemo(
    () =>
      stages.flatMap((stage) =>
        stage.actions.map((action) => ({
          ...action,
          stageId: stage.id,
        }))
      ),
    [stages]
  );
  const [focusIndex, setFocusIndex] = React.useState(0);

  React.useEffect(() => {
    if (!flattened.length) {
      return;
    }
    setFocusIndex((index) => Math.min(index, flattened.length - 1));
  }, [flattened.length]);

  React.useEffect(() => {
    if (!flattened.length) {
      return;
    }
    const safeIndex = focusIndex % flattened.length;
    const btn = document.getElementById(`${flattened[safeIndex].id}-btn`);
    if (btn) btn.focus();
  }, [focusIndex, flattened]);

  React.useEffect(() => {
    if (!flattened.length) {
      return;
    }
    const total = flattened.length;
    const handleKey = (e) => {
      if (e.key === 'ArrowRight') setFocusIndex((i) => (i + 1) % total);
      if (e.key === 'ArrowLeft') setFocusIndex((i) => (i + total - 1) % total);
      if (e.key === 'Enter' || e.key === ' ') {
        const active = flattened[focusIndex % total];
        if (active) active.action();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [focusIndex, flattened]);

  React.useEffect(() => {
    if (!flattened.length) {
      return;
    }
    let raf;
    const total = flattened.length;
    const poll = () => {
      const [gp] = navigator.getGamepads ? navigator.getGamepads() : [];
      if (gp) {
        if (gp.buttons[14]?.pressed)
          setFocusIndex((i) => (i + total - 1) % total);
        if (gp.buttons[15]?.pressed)
          setFocusIndex((i) => (i + 1) % total);
        if (gp.buttons[0]?.pressed) {
          const active = flattened[focusIndex % total];
          if (active) active.action();
        }
      }
      raf = requestAnimationFrame(poll);
    };
    window.addEventListener('gamepadconnected', poll);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('gamepadconnected', poll);
    };
  }, [focusIndex, flattened]);

  return React.createElement(
    'div',
    { className: 'mission-map' },
    stages.map((stage) =>
      React.createElement(
        'section',
        { key: stage.id, className: 'mission-stage' },
        React.createElement('h3', { className: 'mission-stage__title' }, stage.title),
        React.createElement(
          'div',
          { className: 'mission-stage__actions' },
          stage.actions.map((action) =>
            React.createElement(
              React.Fragment,
              { key: action.id },
              React.createElement(
                'button',
                {
                  id: `${action.id}-btn`,
                  onClick: action.action,
                },
                action.label
              ),
              typeof action.renderDetails === 'function'
                ? action.renderDetails() || null
                : null
            )
          )
        ),
        stage.actions.length === 0
          ? React.createElement(
              'p',
              { className: 'mission-stage__empty' },
              'No actions available yet.'
            )
          : null
      )
    )
  );
}

