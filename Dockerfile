FROM python:3.10

WORKDIR /chat

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "AiBot.py"]