import React from 'https://esm.sh/react@18';

export default function MissionMap({ stages }) {
  const normalizedStages = React.useMemo(
    () =>
      stages.map((stage) => {
        const sourceGroups =
          Array.isArray(stage.groups) && stage.groups.length
            ? stage.groups
            : [
                {
                  id: `${stage.id}-default-group`,
                  title: null,
                  actions: Array.isArray(stage.actions) ? stage.actions : [],
                },
              ];
        const groups = sourceGroups.map((group, index) => ({
          id: group.id ?? `${stage.id}-group-${index}`,
          title: group.title ?? null,
          actions: Array.isArray(group.actions) ? group.actions : [],
        }));
        return { ...stage, groups };
      }),
    [stages]
  );

  const flattened = React.useMemo(
    () =>
      normalizedStages.flatMap((stage) =>
        stage.groups.flatMap((group) =>
          group.actions
            .filter((action) => action && action.id)
            .map((action) => ({
              ...action,
              stageId: stage.id,
              groupId: group.id,
            }))
        )
      ),
    [normalizedStages]
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
    normalizedStages.map((stage) => {
      const stageChildren = [
        React.createElement(
          'h3',
          { key: `${stage.id}-title`, className: 'mission-stage__title' },
          stage.title
        ),
      ];

      stage.groups.forEach((group) => {
        const actionNodes = group.actions
          .map((action) => {
            if (!action || !action.id) {
              return null;
            }
            return React.createElement(
              React.Fragment,
              { key: action.id },
              React.createElement(
                'button',
                {
                  id: `${action.id}-btn`,
                  onClick: action.action,
                  className: [
                    'mission-stage__button',
                    action.status ? `mission-stage__button--${action.status}` : null,
                  ]
                    .filter(Boolean)
                    .join(' '),
                },
                action.label
              ),
              typeof action.renderDetails === 'function'
                ? action.renderDetails() || null
                : null
            );
          })
          .filter(Boolean);

        const groupChildren = [];
        if (group.title) {
          groupChildren.push(
            React.createElement(
              'h4',
              {
                key: `${group.id}-title`,
                className: 'mission-stage__group-title',
              },
              group.title
            )
          );
        }
        groupChildren.push(
          React.createElement(
            'div',
            { key: `${group.id}-actions`, className: 'mission-stage__actions' },
            actionNodes
          )
        );
        if (actionNodes.length === 0) {
          groupChildren.push(
            React.createElement(
              'p',
              {
                key: `${group.id}-empty`,
                className: 'mission-stage__empty',
              },
              'No actions available yet.'
            )
          );
        }
        stageChildren.push(
          React.createElement(
            'div',
            { key: group.id, className: 'mission-stage__group' },
            groupChildren
          )
        );
      });

      return React.createElement(
        'section',
        { key: stage.id, className: 'mission-stage' },
        stageChildren
      );
    })
  );
}

