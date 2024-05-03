FROM python:3.11-slim

WORKDIR /appfe

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

RUN mkdir -p data

EXPOSE 8501

ENTRYPOINT ["streamlit","run"]

CMD ["Welcome.py"]
