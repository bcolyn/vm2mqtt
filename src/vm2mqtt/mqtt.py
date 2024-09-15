import hashlib
import json
import logging
import re
from typing import Set, NamedTuple

import paho.mqtt.client as mqtt
from bidict import bidict

from vm2mqtt import VMManager, VirtualMachine


class BridgeConfig(NamedTuple):
    ha_discovery_topic_prefix: str
    bridge_topic_prefix: str


class MQTTBridge:
    _client: mqtt.Client
    _vm_status: dict[VirtualMachine, bool]
    _vm_mapping: bidict[VirtualMachine, str]
    _managers: Set[VMManager]
    config: BridgeConfig

    def __init__(self):
        self._managers = set()
        self._vm_status = dict()
        self._vm_mapping = bidict()
        self.config = BridgeConfig(ha_discovery_topic_prefix="homeassistant",
                                   bridge_topic_prefix="vm2mqtt")  # TODO Config

    def hook_manager(self, vm_manager: VMManager):
        if vm_manager not in self._managers:
            self._managers.add(vm_manager)
            vms = vm_manager.list_vms()
            for vm_status in vms:
                vm = vm_status.vm
                self.add_vm(vm, vm_status.status)

    def start(self):
        logging.info(f"Waiting for messages.")
        self._client.loop_start()

    def refresh(self):
        for manager in self._managers:
            vms = manager.list_vms()
            for vm_status in vms:
                vm = vm_status.vm
                new_status = vm_status.status
                if vm in self._vm_status:
                    if new_status != self._vm_status[vm]:
                        logging.debug(f"New status {new_status} for vm {vm.unique_id()}")
                        self.send_status(vm, new_status)
                        self._vm_status[vm] = new_status
                else:
                    logging.debug(f"Adding vm {vm.unique_id()} with status {new_status}")
                    self.add_vm(vm, new_status)
            # TODO: check for removed VMs

    def stop(self):
        for vm in list(self._vm_status.keys()):
            self.remove_vm(vm)
        self._client.loop_stop()
        self._client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected with result " + str(rc))

    def on_message(self, client, userdata, msg):
        payload: str = msg.payload.decode()
        topic: str = msg.topic
        logging.debug(f"Received message: {topic} {payload}")
        if topic == f"{self.config.ha_discovery_topic_prefix}/status" and payload == "online":
            self.republish_all()
            return
        match = re.match(f"{self.config.bridge_topic_prefix}/switch/(.*)/set", topic)
        if match:
            unique_id = match.group(1)
            try:
                self.start_stop_vm(payload, unique_id)
            except Exception as e:
                logging.error(e)

    def start_stop_vm(self, payload, unique_id):
        vm = self._vm_mapping.inverse[unique_id]
        state = self._vm_status[vm]
        if payload == "ON":
            if not state:
                logging.debug(f"Powering on vm {vm.unique_id()}")
                vm.manager.start(vm)
                self._vm_status[vm] = True
            else:
                logging.debug(f"Vm {vm.unique_id()} is already powered on.")
        else:
            if state:
                logging.debug(f"Stopping vm {vm.unique_id()}")
                vm.manager.shutdown(vm)
                self._vm_status[vm] = False
            else:
                logging.debug(f"Vm {vm.unique_id()} is already powered off.")
        # Always update the state at HA's side, if incorrect refresh will catch it
        self.send_status(vm, self._vm_status[vm])

    def republish_all(self):
        """" In case HA reloads and loses the discovery information, resend it all """
        for vm in self._vm_mapping.keys():
            self.send_discovery(vm)

    def connect(self, host: str, username: str, password: str):
        self._client = mqtt.Client()
        self._client.username_pw_set(username, password)
        self._client.on_message = self.on_message
        self._client.on_connect = self.on_connect
        self._client.connect(host, 1883, 60)  # TODO Config
        self._client.subscribe(f"{self.config.ha_discovery_topic_prefix}/status")

    def send_discovery(self, vm: VirtualMachine):
        logging.info(f"Publishing {vm.name} on {self.discovery_topic(vm)}")
        discovery_payload = {
            "~": self.root_topic(vm),
            "name": vm.name,
            "cmd_t": "~/set",
            "stat_t": "~/state",
            "uniq_id": self.object_id(vm),
            "device": {
                "identifiers": [vm.manager.uid],
                "name": vm.manager.name,
            }
        }
        discovery_payload_json = json.dumps(discovery_payload)
        logging.debug(discovery_payload_json)
        # Not retained to avoid ghost devices
        self._client.publish(self.discovery_topic(vm), discovery_payload_json, retain=False)

    def remove_discovery(self, vm: VirtualMachine):
        logging.info(f"Unpublishing {vm.name}")
        self._client.publish(self.discovery_topic(vm), "", retain=False)

    def send_status(self, vm: VirtualMachine, status: bool | None):
        match status:
            case True:
                payload = "ON"
            case False:
                payload = "OFF"
            case _:
                payload = None
        logging.debug(f"Sending {payload} to {self.state_topic(vm)}")
        self._client.publish(self.state_topic(vm), payload, retain=True)

    def root_topic(self, vm):
        return f"{self.config.bridge_topic_prefix}/switch/{vm.unique_id()}"

    def command_topic(self, vm):
        return f"{self.root_topic(vm)}/set"

    def state_topic(self, vm):
        return f"{self.root_topic(vm)}/state"

    def discovery_topic(self, vm):
        return f"{self.config.ha_discovery_topic_prefix}/switch/vm2mqtt/{self.object_id(vm)}/config"

    def object_id(self, vm):
        """ object id is used in the discovery topic and as the HomeAssistant unique id """
        return hashlib.sha1(self._vm_mapping[vm].encode()).hexdigest()

    def remove_vm(self, vm):
        self.send_status(vm, None)
        self.remove_discovery(vm)
        del self._vm_mapping[vm]
        del self._vm_status[vm]

    def add_vm(self, vm, status):
        self._vm_status[vm] = status
        self._vm_mapping[vm] = vm.unique_id()
        self.send_discovery(vm)
        self._client.subscribe(self.command_topic(vm))
        self.send_status(vm, status)
