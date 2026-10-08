FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MCP_HOST=0.0.0.0
ENV PORT=8000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "mcp[cli]==1.30.0" python-dotenv

COPY waze_mcp_server.py openweb_ninja_waze.py chatgpt_server.py ./

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["python", "chatgpt_server.py"]
