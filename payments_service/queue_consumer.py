import json, os, threading, time, sqlite3
import pika
from db import conn, cursor

RABBIT_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")


def _get_channel():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            ch = connection.channel()
            ch.queue_declare(queue="payment_queue", durable=True)
            return ch
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready – retrying in 2 s")
            time.sleep(2)


def _handle(ch, method, _properties, body):
    msg = json.loads(body)
    order_id = msg["order_id"]
    user_id = msg["user_id"]
    amount = msg["amount"]

    try:
        cursor.execute(
            "INSERT INTO processed_messages(message_id) VALUES (?)",
            (order_id,),
        )
    except sqlite3.IntegrityError:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    cursor.execute(
        """
        UPDATE balances
        SET balance = balance - ?
        WHERE user_id = ? AND balance >= ?
        """,
        (amount, user_id, amount),
    )
    conn.commit()
    ch.basic_ack(delivery_tag=method.delivery_tag)


def _consume():
    ch = _get_channel()
    ch.basic_consume(
        queue="payment_queue",
        on_message_callback=_handle,
        auto_ack=False
    )
    ch.start_consuming()


threading.Thread(target=_consume, daemon=True).start()
