import zmq
import time

ENDPOINT = "tcp://*:7777"


def main():
    context = zmq.Context.instance()
    worker = context.socket(zmq.PUB)
    worker.bind(ENDPOINT)

    while True:
        #request = worker.recv_multipart()
        #print("[Worker] received request: ", request)
        #client_id, msg_id, msg = request
        pub_id = "topic1 "
        pub_msg = pub_id + "hello"
        time.sleep(1)
        worker.send_string( pub_msg)
        print("[pub]sent: ", [pub_msg])
        pub_id = "topic1 "
        pub_msg = pub_id + "world"
        time.sleep(1)
        worker.send_string( pub_msg)

        print("[pub]sent: ", [pub_msg])


if __name__ == "__main__":
    main()
