# ╔══════════════════════════════════════════════════════════╗
# ║         🎫  TICKET BOT  —  DOCKERFILE                   ║
# ║         Deploy on Render (or any Docker host)           ║
# ╚══════════════════════════════════════════════════════════╝

FROM python:3.11-slim

# Μην φτιάχνει .pyc αρχεία + unbuffered output για logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Εγκατάσταση dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Αντιγραφή κώδικα
COPY . .

# Render περνάει το PORT ως env var — το bot το διαβάζει αυτόματα
EXPOSE 8080

CMD ["python", "bot.py"]
