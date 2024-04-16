FROM python:3.10.10-buster

WORKDIR /code

COPY ./requirements.txt /code

COPY . /code

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["python", "main.py", "Cost", "Emissions", "140", "0", "100", "40", "0.785714", "0", "1", "0.25", "1", "2", "A"]


