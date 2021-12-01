FROM python:3.7-slim

RUN pip3 install nltk pysolr requests unidecode validators bs4 uvicorn fastapi pydantic
COPY install_dictionary.py /install_dictionary.py
RUN python3 /install_dictionary.py
EXPOSE 8094

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8094"]