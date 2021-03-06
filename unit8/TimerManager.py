import paho.mqtt.client as mqtt
import stmpy
import logging
from threading import Thread
import json

MQTT_BROKER = "mqtt.item.ntnu.no"
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = "ttm4115/team_4/command"
MQTT_TOPIC_OUTPUT = "ttm4115/team_4/answer"


class TimerLogic:
    """
    State Machine for a named timer.

    This is the support object for a state machine that models a single timer.
    """

    def __init__(self, name, duration, component: "TimerManagerComponent"):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.duration = duration
        self.component = component

        transitions = [
            {"source": "initial", "target": "active", "effect": "started"},
            {
                "trigger": "report",
                "source": "active",
                "target": "active",
                "effect": "report_status",
            },
            {
                "trigger": "t",
                "source": "active",
                "target": "completed",
                "effect": "timer_completed",
            },
        ]

        self.stm = stmpy.Machine(name=name, transitions=transitions, obj=self)

    def started(self):
        self.stm.start_timer("t", self.duration * 1000)

    def report_status(self):
        milliseconds_left = self.stm.get_timer(timer_id="t")
        seconds_left = round(milliseconds_left / 1000)

        self.component.mqtt_client.publish(
            topic=MQTT_TOPIC_OUTPUT,
            payload=f"You have {seconds_left} seconds left on the {self.name} timer.",
        )

    def timer_completed(self):
        self.component.mqtt_client.publish(
            topic=MQTT_TOPIC_OUTPUT, payload=f"Your {self.name} timer is ready!"
        )

        self.component.remove_timer(self.name)


class TimerManagerComponent:
    """
    The component to manage named timers in a voice assistant.

    This component connects to an MQTT broker and listens to commands.
    To interact with the component, do the following:

    * Connect to the same broker as the component. You find the broker address
    in the value of the variable `MQTT_BROKER`.
    * Subscribe to the topic in variable `MQTT_TOPIC_OUTPUT`. On this topic, the
    component sends its answers.
    * Send the messages listed below to the topic in variable `MQTT_TOPIC_INPUT`.

        {"command": "new_timer", "name": "spaghetti", "duration":50}

        {"command": "status_all_timers"}

        {"command": "status_single_timer", "name": "spaghetti"}

    """

    def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug("MQTT connected to {}".format(client))

    def on_message(self, client, userdata, msg):
        """
        Processes incoming MQTT messages.

        We assume the payload of all received MQTT messages is an UTF-8 encoded
        string, which is formatted as a JSON object. The JSON object contains
        a field called `command` which identifies what the message should achieve.

        As a reaction to a received message, we can for example do the following:

        * create a new state machine instance to handle the incoming messages,
        * route the message to an existing state machine session,
        * handle the message right here,
        * throw the message away.

        """
        self._logger.debug(f"Incoming message to topic {msg.topic}")

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as err:
            self._logger.error(
                f"Message sent to topic {msg.topic} had no valid JSON. Message ignored. {err}"
            )
            return

        command = payload.get("command")

        if command == "new_timer":
            timer_name = payload.get("name")
            timer_duration = payload.get("duration")
            timer = TimerLogic(timer_name, timer_duration, self)

            self.stm_driver.add_machine(timer.stm)
            self.active_timers[timer.name] = timer

            return

        if command == "status_all_timers":
            message = f"You have {len(self.active_timers)} active timers: "
            for timer_name in self.active_timers:
                message += f"{timer_name}, "
            message = message[0:-2]

            self.mqtt_client.publish(
                topic=MQTT_TOPIC_OUTPUT,
                payload=message,
            )

            return

        if command == "status_single_timer":
            timer_name = payload.get("name")
            timer = self.active_timers.get(timer_name)

            if timer:
                timer.stm.send("report")

    def __init__(self):
        """
        Start the component.

        ## Start of MQTT
        We subscribe to the topic(s) the component listens to.
        The client is available as variable `self.client` so that subscriptions
        may also be changed over time if necessary.

        The MQTT client reconnects in case of failures.

        ## State Machine driver
        We create a single state machine driver for STMPY. This should fit
        for most components. The driver is available from the variable
        `self.driver`. You can use it to send signals into specific state
        machines, for instance.

        """
        # get the logger object for the component
        self._logger = logging.getLogger(__name__)
        print("logging under name {}.".format(__name__))
        self._logger.info("Starting Component")

        # create a new MQTT client
        self._logger.debug(
            "Connecting to MQTT broker {}??at port {}".format(MQTT_BROKER, MQTT_PORT)
        )
        self.mqtt_client = mqtt.Client()
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        # subscribe to proper topic(s) of your choice
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        # we start the stmpy driver, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)
        self._logger.debug("Component initialization finished")

        self.active_timers: dict[str, TimerLogic] = {}

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the state machine Driver
        self.stm_driver.stop()

    def remove_timer(self, timer_name):
        self.active_timers.pop(timer_name)


# logging.DEBUG: Most fine-grained logging, printing everything
# logging.INFO:  Only the most important informational log items
# logging.WARN:  Show only warnings and errors.
# logging.ERROR: Show only error messages.
debug_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter("%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

t = TimerManagerComponent()
