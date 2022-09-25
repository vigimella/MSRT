FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install spacy
RUN python3 -m spacy download en_core_web_sm

RUN pip install --no-cache-dir -r requirements.txt


COPY . .

CMD ["python", "main.py"]
