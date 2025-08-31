module.exports = {
  plugins: [
    {
      rules: {
        'subject-pattern': ({subject}, when = 'always', value = /^did .+ on .+ to obtain .+, expecting behavior .+$/) => {
          const negated = when === 'never';
          const test = value.test(subject);
          return [
            negated ? !test : test,
            `subject must${negated ? ' not' : ''} match ${value}`
          ];
        }
      }
    }
  ],
  rules: {
    'type-enum': [2, 'always', ['feat']],
    'scope-empty': [2, 'never'],
    'subject-empty': [2, 'never'],
    'subject-pattern': [2, 'always']
  }
};
