import React from 'https://esm.sh/react@18';

export default function MissionWizard({ onComplete }) {
  const [step, setStep] = React.useState(() => Number(localStorage.getItem('missionWizardStep') || 0));

  const steps = [
    { title: 'Create Mission', tip: 'Open the mission builder and compose a mission with blocks.' },
    { title: 'Run Mission', tip: 'Use "Save & Run" to store the mission and dispatch it.' },
    { title: 'All Set', tip: 'Mission dispatched.' }
  ];

  const total = steps.length - 1;
  const progress = Math.min((step / total) * 100, 100);

  function next() {
    const nextStep = Math.min(step + 1, steps.length - 1);
    setStep(nextStep);
    localStorage.setItem('missionWizardStep', nextStep);
    if (nextStep === steps.length - 1) {
      localStorage.setItem('missionWizardCompleted', 'true');
      onComplete();
    }
  }

  function back() {
    const prev = Math.max(step - 1, 0);
    setStep(prev);
    localStorage.setItem('missionWizardStep', prev);
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
        React.createElement('div', { className: 'progress-bar', style: { width: `${progress}%` } })
      ),
      React.createElement('h2', { title: current.tip }, current.title),
      step === 0
        ? React.createElement('a', { href: '../mission_builder/index.html', target: '_blank', rel: 'noopener' }, 'Open Mission Builder')
        : null,
      step > 0
        ? React.createElement('button', { onClick: back, style: { marginRight: '0.5rem' } }, 'Back')
        : null,
      step < steps.length - 1
        ? React.createElement('button', { onClick: next }, 'Next')
        : React.createElement('button', { onClick: next }, 'Finish')
    )
  );
}
