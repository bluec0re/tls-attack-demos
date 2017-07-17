from __future__ import unicode_literals, absolute_import
import subprocess
import logging
import re

log = logging.getLogger(__name__)

class Vm:
    def __init__(self, uuid=None, name=None):
        if not uuid and not name:
            raise ValueError('name or uuid required')

        self.uuid = uuid
        self.name = name
        self.__info = None

        if not self.uuid:
            self.uuid = self.name
            self.uuid = self.info['UUID']
        if not self.name:
            self.name = self.info['name']

    def __repr__(self):
        return '{}(uuid={})'.format(type(self).__name__, self.uuid)

    @property
    def info(self):
        if not self.__info:
            lines = subprocess.check_output([
                     'VBoxManage', 'showvminfo', self.uuid,
                     '--machinereadable']).decode().split('\n')
            self.__info = {}
            for line in lines:
                if not line:
                    continue
                key, value = line.split('=', 1)
                self.__info[key.strip('"')] = value.strip('"')
        return self.__info

    def start(self, start_type='gui'):
        if start_type not in ('gui', 'sdl', 'headless', 'separate'):
            raise ValueError('Invalid start_type ' + start_type)
        subprocess.call(['VBoxManage', 'startvm', self.uuid,
                         '--type', start_type])

    def clone(self, snapshot=None, mode=None, options=None, name=None,
              groups=None, basefolder=None, uuid=None, register=False):
        args = []
        if snapshot:
            args += ['--snapshot', snapshot]
        if mode:
            args += ['--mode', mode]
        if options:
            args += ['--options', options]
        if name:
            args += ['--name', name]
        if groups:
            args += ['--groups', groups]
        if basefolder:
            args += ['--basefolder', basefolder]
        if uuid:
            args += ['--uuid', uuid]
        if register:
            args += ['--register']
        subprocess.check_output(['VBoxManage', 'clonevm', self.uuid] + args)

    def _control(self, cmd, *args, **kwargs):
        args = list(args)
        for key, value in kwargs.items():
            args += ['--' + key.replace('_', '-'), value]
        return subprocess.check_output(['VBoxManage', 'controlvm', self.uuid] + args)

    def _modify(self, cmd, *args, **kwargs):
        args = list(args)
        for key, value in kwargs.items():
            args += ['--' + key.replace('_', '-'), value]
        return subprocess.check_output(['VBoxManage', 'modifyvm', self.uuid] + args)

    def poweroff(self, force=False):
        if force:
            self._control('poweroff')
        else:
            self._control('acpipowerbutton')

    def savestate(self):
        self._control('savestate')

    def nics(self):
        nic_re = re.compile('^nic\d+$')
        for k, v in self.info.items():
            m = nic_re.match(k)
            if m and v != 'none':
                yield k

    def disconnect_nic(self, nr):
        self._modify(**{'cableconnected{}'.format(nr): 'off'})

    def connect_nic(self, nr):
        self._modify(**{'cableconnected{}'.format(nr): 'on'})

    def remove_nic(self, nr):
        self._modify(**{'nic{}'.format(nr): 'none'})

    def add_nic(self, nr, nictype):
        if nictype not in ('nat', 'bridged', 'intnet', 'hostonly', 'generic',
                           'natnetwork'):
            raise ValueError('Invalid nictype ' + repr(nictype))
        self._modify(**{'nic{}'.format(nr): nictype})

    def set_intnet(self, nr, name):
        self._modify(**{'intnet{}'.format(nr): name})

    def set_hostonly(self, nr, name):
        self._modify(**{'hostonlyadapter{}'.format(nr): name})


class VBox:
    def vms(self):
        vm_re = re.compile(r'^"(?P<name>.+)" \{(?P<uuid>[0-9a-f-]+)\}$')
        for line in subprocess.check_output(['VBoxManage', 'list', 'vms']).decode().split('\n'):
            m = vm_re.match(line)
            if m:
                yield Vm(m['uuid'], m['name'])


VB = VBox()


def get_vns():
    return VB.vms()

