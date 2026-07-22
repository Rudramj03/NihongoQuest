module.exports = {
  apps: [
    {
      name: "nihongoquest",
      cwd: "/var/www/NihongoQuest",
      script: "venv/bin/gunicorn",
      args: "--workers 2 --bind 127.0.0.1:5001 --access-logfile - app:app",
      interpreter: "none",
      autorestart: true,
      max_restarts: 10,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
