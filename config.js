module.exports = {
  platform: 'gitlab',
  logLevel: 'debug',
  labels: ['renovate', 'dependencies', 'automated'],
  onboarding: true,
  onboardingConfig: {
    extends: ['config:recommended']
  },
  cacheDir: "/tmp/renovate",
  recreateClosed: true,
  ignoreDeps: ["python"],
  hostRules: [
    {
      matchHost: "https://pypi.org/simple",
      username: "admin",
      password: process.env.RENOVATE_PYPI_PASS
    },
  ],
  enabledManagers: [
    "pep621"
  ],
  "ignoreDeps": ["ray"],
  packageRules: [
    {
      matchManagers: ["pep621"]
    }
  ],
  lockFileMaintenance: {
  enabled: true,
  lockfile: "uv.lock"
  }
};
