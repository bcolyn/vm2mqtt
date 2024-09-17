# vm2mqtt

VM2MQTT exposes Proxmox LXC containers and virtual machines or Portainer Docker Stacks to MQTT via the HomeAssistant
MQTT Discovery protocol.

This enables you (or your family/housemates!) to start/stop VMs and containers via the familiar HomeAssistant user
interface, without granting them full access to the hypervisor or container management interface.

On top of that, you can use HomeAssistant Automations to start/stop services based on things like timing, presence
detection, physical buttons, ...

For me, this enables me to offer services (like private a Minecraft server) running in my homelab to my family members
without having those services eating resources 24/7.

## Binaries

Binaries are available on Docker Hub:
https://hub.docker.com/repository/docker/bennycolyn/vm2mqtt/general

## Environment Variables

### MQTT

| Name	     | Description	                       |
|-----------|------------------------------------|
| MQTT_HOST | Hostname of the Mosquitto instance |
| MQTT_USER | Mosquitto username                 |
| MQTT_PASS | Mosquitto password                 |

### Proxmox

| Name	               | Description	                                            |
|---------------------|---------------------------------------------------------|
| PROXMOX_HOST 	      | Proxmox hostname or IP                                  |
| PROXMOX_USER 	      | Proxmox Username                                        |
| PROXMOX_TOKEN_NAME  | Login token name                                        |
| PROXMOX_TOKEN_VALUE | Login token value                                       |
| PROXMOX_VMIDS       | Comma-separated list of vmids of the containers exposed |

For Proxmox login, configure a token and make sure it has the necessary permissions. The user must also have these
permissions, as proxmox ultimately applies the intersection of user and token permissions.

### Portainer

| Name	                | Description	                                                                               |
|----------------------|--------------------------------------------------------------------------------------------|
| PORTAINER_URL        | Url of the portainer manager                                                               |
| PORTAINER_TOKEN      | Authentication token                                                                       |
| PORTAINER_VERIFY_SSL | Enable/disable SSL cert verification, for use with the default self-signed portainer certs |


