from dataclasses import dataclass
from io import UnsupportedOperation
from typing import List

from proxmoxer import ProxmoxAPI

from vm2mqtt import VMManager, VirtualMachine, VMStatus


# https://pve.proxmox.com/pve-docs/api-viewer/index.html

@dataclass(frozen=True)
class LXC(VirtualMachine):
    node: str

    def unique_id(self) -> str:
        return f"{self.manager.uid}/{self.node}/lxc/{self.vmid}"


@dataclass(frozen=True)
class QEmu(VirtualMachine):
    node: str

    def unique_id(self) -> str:
        return f"{self.manager.uid}/{self.node}/qemu/{self.vmid}"


def map_status(status: str) -> bool:
    return status == "running"


class ProxmoxManager(VMManager):
    _api = ProxmoxAPI
    _vmids = List[int]

    def __init__(self):
        super().__init__()
        self.name = "Proxmox"

    def connect(self, host, user, token_name, token_value) -> None:
        self.uid = f"proxmox@{host}"
        self._api = ProxmoxAPI(host, user=user, token_name=token_name, token_value=token_value)

    def set_vmids(self, vmids: List[int]):
        self._vmids = vmids

    def list_vms(self) -> List[VMStatus]:
        return [container for node in self.list_nodes() for container in
                (self.list_lxc(node) + self.list_qemu(node))]

    def list_nodes(self) -> List[str]:
        nodes = self._api.nodes.get()
        return [node["node"] for node in nodes if node["status"] == 'online']

    def list_lxc(self, node: str) -> List[VMStatus]:
        lxcs = self._api.nodes(node).lxc.get()
        return [VMStatus(vm=LXC(node=node, vmid=str(lxc['vmid']), name=lxc['name'], manager=self),
                         status=map_status(lxc['status']))
                for lxc
                in lxcs if int(lxc['vmid']) in self._vmids]

    def list_qemu(self, node: str) -> List[VMStatus]:
        qemus = self._api.nodes(node).qemu.get()
        return [VMStatus(vm=QEmu(node=node, vmid=str(qemu['vmid']), name=qemu['name'], manager=self),
                         status=map_status(qemu['status']))
                for qemu
                in qemus if int(qemu['vmid']) in self._vmids]

    def start(self, vm: VirtualMachine):
        if isinstance(vm, LXC):
            return self._api.nodes(vm.node).lxc(vm.vmid).status.start.post()
        elif isinstance(vm, QEmu):
            return self._api.nodes(vm.node).qemu(vm.vmid).status.start.post()
        else:
            raise UnsupportedOperation

    def shutdown(self, vm: VirtualMachine):
        if isinstance(vm, LXC):
            return self._api.nodes(vm.node).lxc(vm.vmid).status.shutdown.post()
        elif isinstance(vm, QEmu):
            return self._api.nodes(vm.node).qemu(vm.vmid).status.shutdown.post()
        else:
            raise UnsupportedOperation