FROM python:3.10-bookworm

COPY . /app

RUN pip install inquirer==3.2.4 pomice==2.9.0 py-cord==2.5.0 rich==13.6.0 fuzzywuzzy==0.18.0 pyyaml python-Levenshtein

WORKDIR /app

CMD ["python", "bot_init.py"]
