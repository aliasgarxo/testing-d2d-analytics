FROM python:3.9

WORKDIR /app
COPY campaign_controller.py /app/
RUN pip install fastapi kubernetes uvicorn pydantic

CMD ["uvicorn", "campaign_controller:app", "--host", "0.0.0.0", "--port", "8000"]

