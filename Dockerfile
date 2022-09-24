FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install spacy
RUN python3 -m spacy download en_core_web_sm

COPY . .

CMD ["python", "main.py"]
