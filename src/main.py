import logging
import os
from time import sleep

from vm2mqtt.mqtt import MQTTBridge
from vm2mqtt.portainer import PortainerManager
from vm2mqtt.proxmox import ProxmoxManager


def init_proxmox() -> ProxmoxManager:
    result = ProxmoxManager()
    result.connect(os.environ['PROXMOX_HOST'],
                   os.environ['PROXMOX_USER'],
                   os.environ['PROXMOX_TOKEN_NAME'],
                   os.environ['PROXMOX_TOKEN_VALUE'])
    if not 'PROXMOX_VMIDS' in os.environ:
        raise Exception("PROXMOX_VMIDS whitelist not set")
    vmids = os.environ['PROXMOX_VMIDS']
    result.set_vmids([int(vmid.strip()) for vmid in vmids.split(',')])
    return result


def init_portainer():
    def str_to_bool(s):
        return s.lower() == "true"

    result = PortainerManager()
    result.connect(os.environ['PORTAINER_URL'],
                   os.environ['PORTAINER_TOKEN'],
                   verify_ssl=str_to_bool(os.environ['PORTAINER_VERIFY_SSL']))
    return result


def init_mqtt() -> MQTTBridge:
    result = MQTTBridge()
    result.connect(os.environ["MQTT_HOST"], os.environ["MQTT_USER"], os.environ["MQTT_PASS"])
    return result


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    mqtt = init_mqtt()

    if "PROXMOX_HOST" in os.environ:
        proxmox = init_proxmox()
        mqtt.hook_manager(proxmox)

    if "PORTAINER_URL" in os.environ:
        portainer = init_portainer()
        mqtt.hook_manager(portainer)

    mqtt.start()
    try:
        while True:
            sleep(60) # TODO config
            logging.debug("Refreshing")
            mqtt.refresh()
    except KeyboardInterrupt:
        logging.info("Shutting down")
        mqtt.stop()
