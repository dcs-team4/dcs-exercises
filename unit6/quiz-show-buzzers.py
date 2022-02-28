from stmpy import Driver, Machine
from threading import Thread
import paho.mqtt.client as mqtt


class QuizMachine:
    stm: Machine

    def buzz(self):
        print(f"Someone buzzed!")

    def on_start_question(self):
        print(f"Question asked!")

    def on_timeout(self):
        print("Timeout")


class MQTT_Client:
    def __init__(self, quiz_machine: QuizMachine):
        self.count = 0
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.quiz_machine = quiz_machine

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        print("on_message(): topic: {}".format(msg.topic))
        if msg.topic == "Buzz":
            self.quiz_machine.stm.send("buzzed")
        elif msg.topic == "AskQuestion":
            self.quiz_machine.stm.send("start_question")

    def start(self, broker, port):
        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe("Buzz")
        self.client.subscribe("AskQuestion")

        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()


transitions = [
    {"source": "initial", "target": "start"},
    {
        "trigger": "start_question",
        "source": "start",
        "target": "question_asked",
        "effect": "on_start_question",
    },
    {
        "trigger": "t",
        "source": "question_asked",
        "target": "start",
        "effect": "on_timeout",
    },
    {
        "trigger": "buzzed",
        "source": "question_asked",
        "target": "start",
        "effect": "buzz",
    },
]

states = [
    {"name": "start"},
    {"name": "question_asked", "entry": "start_timer('t', 20000)"},
]

quiz_machine_obj = QuizMachine()
quiz_machine = Machine(
    name="quiz_machine", transitions=transitions, obj=quiz_machine_obj, states=states
)
quiz_machine_obj.stm = quiz_machine

driver = Driver()
driver.add_machine(quiz_machine)
driver.start()

mqtt_client = MQTT_Client(quiz_machine_obj)
broker, port = "mqtt.item.ntnu.no", 1883
mqtt_client.start(broker, port)
