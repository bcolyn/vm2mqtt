import logging
from dataclasses import dataclass
import requests
from typing import List
import mmh3
from vm2mqtt import VirtualMachine, VMManager, VMStatus


@dataclass(frozen=True)
class Stack(VirtualMachine):
    endpointId: str

    def unique_id(self) -> str:
        return f"{self.manager.uid}/stack/{self.vmid}"


class PortainerManager(VMManager):
    _url: str
    _token: str
    _verify_ssl: bool

    def __init__(self):
        super().__init__()
        self.name = "Portainer"

    def connect(self, url, token, verify_ssl: bool = True):
        self._url = url
        self._token = token
        self._verify_ssl = verify_ssl
        self.uid = f"portainer-{mmh3.hash(url)}"

    def root_url(self):
        return f"{self._url}/api"

    def _get(self, rel_url: str, params=None):
        return self._request("GET", rel_url, params=params)

    def _post(self, rel_url: str, params=None):
        return self._request("POST", rel_url, params=params)

    def _request(self, method, rel_url: str, data=None, params=None):
        url = self.root_url() + rel_url
        headers = {
            'X-API-Key': self._token,
            'Content-Type': 'application/json'
        }
        response = requests.request(method, url, headers=headers, verify=self._verify_ssl,
                                    data=data, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Error: {response.status_code} - {response.text}")

    def list_vms(self) -> List[VMStatus]:
        json_array = self._get("/stacks")

        def map_status(status: int) -> bool:
            return status == 1

        def from_json(json) -> VMStatus:
            return VMStatus(
                Stack(json['Id'], json['Name'], self, str(json['EndpointId'])),
                map_status(json['Status']))

        return [from_json(obj) for obj in json_array]

    def start(self, vm: Stack):
        self._post(f"/stacks/{vm.vmid}/start", params={"endpointId": vm.endpointId})

    def shutdown(self, vm: Stack):
        self._post(f"/stacks/{vm.vmid}/stop", params={"endpointId": vm.endpointId})
