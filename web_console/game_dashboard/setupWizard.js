import React from 'https://esm.sh/react@18';
import { BASE_URL } from '../main.js';

export default function SetupWizard({ onComplete }) {
  const [status, setStatus] = React.useState({ avatar: false, tokens: false });
  const [step, setStep] = React.useState(() => Number(localStorage.getItem('wizardStep') || 0));

  const steps = [
    {
      id: 'avatar',
      title: 'Avatar Config',
      tip: 'Ensure avatar_config.toml is available on the server.',
      check: status.avatar,
    },
    {
      id: 'tokens',
      title: 'API Tokens',
      tip: 'Define required API tokens in secrets.env.',
      check: status.tokens,
    },
    {
      id: 'done',
      title: 'All Set',
      tip: 'Setup complete.',
      check: true,
    },
  ];

  async function check() {
    const avatar = await fetch('/avatar_config.toml', { method: 'HEAD' })
      .then((r) => r.ok)
      .catch(() => false);
    const tokens = await fetch(`${BASE_URL}/token-status`)
      .then((r) => r.ok)
      .catch(() => false);
    setStatus({ avatar, tokens });
    if (avatar && tokens) {
      localStorage.setItem('setupWizardCompleted', 'true');
      onComplete();
    }
  }

  React.useEffect(() => {
    check();
  }, []);

  const total = steps.length - 1; // exclude final done step for progress
  const progress = Math.min((step / total) * 100, 100);

  function next() {
    const nextStep = Math.min(step + 1, steps.length - 1);
    setStep(nextStep);
    localStorage.setItem('wizardStep', nextStep);
    if (nextStep === steps.length - 1) {
      localStorage.setItem('setupWizardCompleted', 'true');
      onComplete();
    }
  }

  function back() {
    const prev = Math.max(step - 1, 0);
    setStep(prev);
    localStorage.setItem('wizardStep', prev);
  }

  const current = steps[step];

  return React.createElement(
    'div',
    { className: 'modal-overlay' },
    React.createElement(
      'div',
      { className: 'modal' },
      React.createElement(
        'div',
        { className: 'progress' },
        React.createElement('div', {
          className: 'progress-bar',
          style: { width: `${progress}%` },
        })
      ),
      React.createElement('h2', { title: current.tip }, current.title),
      !current.check && step < steps.length - 1
        ? React.createElement('p', null, 'Not detected. ', current.tip)
        : null,
      step > 0
        ? React.createElement(
            'button',
            { onClick: back, style: { marginRight: '0.5rem' } },
            'Back'
          )
        : null,
      step < steps.length - 1
        ? React.createElement(
            React.Fragment,
            null,
            React.createElement(
              'button',
              { onClick: check, style: { marginRight: '0.5rem' } },
              'Re-check'
            ),
            React.createElement('button', { onClick: next }, 'Next')
          )
        : React.createElement('button', { onClick: next }, 'Finish')
    )
  );
}
