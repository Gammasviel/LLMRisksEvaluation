wt.exe `
  new-tab --profile "Ubuntu" --title "Flask" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && flask run --host=0.0.0.0" `
  `; new-tab --profile "Ubuntu" --title "Celery" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && celery -A app.core.tasks.celery worker --loglevel=info -P gevent -c 100" `
  `; new-tab --profile "Ubuntu" --title "Redis" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && sudo service redis-server start" `
  `; new-tab --profile "Ubuntu" --title "SQLite Web" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && sqlite_web ./instance/evaluation.db --host 0.0.0.0 --port 5001" `
  `; new-tab --profile "Ubuntu" --title "Shell" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && bash"
