wt.exe `
  new-tab --profile "Ubuntu" --title "Flask" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && flask run --host=0.0.0.0" `
  `; new-tab --profile "Ubuntu" --title "Celery" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && celery -A tasks.celery worker --loglevel=info -P gevent -c 100" `
  `; new-tab --profile "Ubuntu" --title "Shell" `
    wsl -d Ubuntu --cd ~/Projects/NewFieldWork -e bash -c "source ./venv/bin/activate && echo 'Development shell ready' && exec bash"
