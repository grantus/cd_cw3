import json, time, threading, os
import pika
from db import conn
cursor = conn.cursor()

RABBIT = pika.BlockingConnection(
    pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST"))
).channel()
RABBIT.queue_declare(queue="payment_queue", durable=True)

def run():
    while True:
        rows = cursor.execute(
          "SELECT id, payload FROM outbox WHERE sent=0"
        ).fetchall()
        for oid, payload in rows:
            RABBIT.basic_publish(
              exchange="",
              routing_key="payment_queue",
              body=payload
            )
            cursor.execute("UPDATE outbox SET sent=1 WHERE id=?", (oid,))
            conn.commit()
        time.sleep(1)

threading.Thread(target=run, daemon=True).start()
