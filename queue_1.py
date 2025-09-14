# queue_1.py
from queue import Queue
from threading import Thread
from time import sleep

task_queue = Queue()

def add_to_queue(note_id: int):
    task_queue.put(note_id)
    print(f"[LOG] Note {note_id} added to queue")

def worker_loop(summarize_fn):
    while True:
        note_id = task_queue.get()
        try:
            summarize_fn(note_id)
        except Exception as e:
            print(f"[LOG] Task {note_id} failed in worker_loop: {e}")
        task_queue.task_done()
        sleep(0.1)
