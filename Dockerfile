FROM python:3.10.10-buster

WORKDIR /code

COPY ./requirements.txt /code

COPY . /code

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

CMD ["python", "main.py", "Cost", "Emissions"]


