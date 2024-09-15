from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class VirtualMachine:
    vmid: str
    name: str
    manager: "VMManager"

    def unique_id(self) -> str:
        raise NotImplementedError


@dataclass
class VMStatus:
    vm: VirtualMachine
    status: bool


class VMManager:
    name: str
    uid: str

    def list_vms(self) -> List[VMStatus]:
        raise NotImplementedError

    def start(self, vm: VirtualMachine):
        raise NotImplementedError

    def shutdown(self, vm: VirtualMachine):
        raise NotImplementedError

    def __repr__(self):
        return self.name
