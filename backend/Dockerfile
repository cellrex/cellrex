FROM python:3.11-slim

WORKDIR /appbe

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000" ,"--log-config", "log_conf.yaml", "--reload"]
