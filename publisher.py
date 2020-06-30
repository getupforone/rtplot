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
        pub_msg = "hello"
        pub_id = "pub"
        time.sleep(1)
        worker.send_string( pub_msg)
        print("[pub]sent: ", [pub_id, pub_msg])



if __name__ == "__main__":
    main()
