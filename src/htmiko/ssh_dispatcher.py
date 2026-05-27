# Originally from Netmiko https://github.com/ktbyers/netmiko
# see licenses/LICENSE-NETMIKO
# Copyright 2016-2026 Kirk Byers
# Copyright 2026 HyeTech

"""Controls selection of proper class based on the device type."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional
from typing import Type

from htmiko.a10 import A10SSH
from htmiko.accedian import AccedianSSH
from htmiko.adtran import AdtranOSSSH
from htmiko.adtran import AdtranOSTelnet
from htmiko.adva import AdvaAosFsp150F2SSH
from htmiko.adva import AdvaAosFsp150F3SSH
from htmiko.alaxala import AlaxalaAx36sSSH
from htmiko.alcatel import AlcatelAosSSH
from htmiko.allied_telesis import AlliedTelesisAwplusSSH
from htmiko.apc import ApcAosSSH
from htmiko.apresia import ApresiaAeosSSH
from htmiko.apresia import ApresiaAeosTelnet
from htmiko.arista import AristaFileTransfer
from htmiko.arista import AristaSSH
from htmiko.arista import AristaTelnet
from htmiko.arris import ArrisCERSSH
from htmiko.aruba import ArubaCxSSH
from htmiko.aruba import ArubaOsFileTransfer
from htmiko.aruba import ArubaOsSSH
from htmiko.asterfusion import AsterfusionAsterNOSSSH
from htmiko.audiocode import Audiocode66SSH
from htmiko.audiocode import Audiocode66Telnet
from htmiko.audiocode import Audiocode72SSH
from htmiko.audiocode import Audiocode72Telnet
from htmiko.audiocode import AudiocodeShellSSH
from htmiko.audiocode import AudiocodeShellTelnet
from htmiko.bintec import BintecBossSSH
from htmiko.bintec import BintecBossTelnet
from htmiko.broadcom import BroadcomIcosSSH
from htmiko.brocade import BrocadeFOSSSH
from htmiko.calix import CalixB6SSH
from htmiko.calix import CalixB6Telnet
from htmiko.calix import CalixExaSSH
from htmiko.calix import CalixExaTelnet
from htmiko.casa import CasaCMTSSSH
from htmiko.cdot import CdotCrosSSH
from htmiko.centec import CentecOSSSH
from htmiko.centec import CentecOSTelnet
from htmiko.checkpoint import CheckPointGaiaSSH
from htmiko.ciena import CienaSaos10SSH
from htmiko.ciena import CienaSaosFileTransfer
from htmiko.ciena import CienaSaosSSH
from htmiko.ciena import CienaSaosTelnet
from htmiko.ciena import CienaWaveserverSSH
from htmiko.cisco import CiscoApicSSH
from htmiko.cisco import CiscoApSSH
from htmiko.cisco import CiscoAsaFileTransfer
from htmiko.cisco import CiscoAsaSSH
from htmiko.cisco import CiscoFtdSSH
from htmiko.cisco import CiscoIosFileTransfer
from htmiko.cisco import CiscoIosSerial
from htmiko.cisco import CiscoIosSSH
from htmiko.cisco import CiscoIosTelnet
from htmiko.cisco import CiscoNxosFileTransfer
from htmiko.cisco import CiscoNxosSSH
from htmiko.cisco import CiscoNxosTelnet
from htmiko.cisco import CiscoS200SSH
from htmiko.cisco import CiscoS200Telnet
from htmiko.cisco import CiscoS300SSH
from htmiko.cisco import CiscoS300Telnet
from htmiko.cisco import CiscoTpTcCeSSH
from htmiko.cisco import CiscoViptelaSSH
from htmiko.cisco import CiscoWlcSSH
from htmiko.cisco import CiscoXrFileTransfer
from htmiko.cisco import CiscoXrSSH
from htmiko.cisco import CiscoXrTelnet
from htmiko.citrix import NetscalerSSH
from htmiko.cloudgenix import CloudGenixIonSSH
from htmiko.corelight import CorelightLinuxSSH
from htmiko.coriant import CoriantSSH
from htmiko.cumulus import CumulusLinuxSSH
from htmiko.dell import DellDNOS6SSH
from htmiko.dell import DellDNOS6Telnet
from htmiko.dell import DellForce10SSH
from htmiko.dell import DellIsilonSSH
from htmiko.dell import DellOS10FileTransfer
from htmiko.dell import DellOS10SSH
from htmiko.dell import DellPowerConnectSSH
from htmiko.dell import DellPowerConnectTelnet
from htmiko.dell import DellSonicSSH
from htmiko.digi import DigiTransportSSH
from htmiko.dlink import DlinkDSSSH
from htmiko.dlink import DlinkDSTelnet
from htmiko.edgecore import EdgecoreSonicSSH
from htmiko.ekinops import EkinopsEk360SSH
from htmiko.eltex import EltexEsrSSH
from htmiko.eltex import EltexSSH
from htmiko.endace import EndaceSSH
from htmiko.enterasys import EnterasysSSH
from htmiko.ericsson import EricssonIposSSH
from htmiko.ericsson import EricssonMinilink63SSH
from htmiko.ericsson import EricssonMinilink66SSH
from htmiko.exceptions import ConnectionException
from htmiko.exceptions import HTMikoAuthenticationException
from htmiko.exceptions import HTMikoTimeoutException
from htmiko.extreme import ExtremeErsSSH
from htmiko.extreme import ExtremeExosFileTransfer
from htmiko.extreme import ExtremeExosSSH
from htmiko.extreme import ExtremeExosTelnet
from htmiko.extreme import ExtremeNetironSSH
from htmiko.extreme import ExtremeNetironTelnet
from htmiko.extreme import ExtremeNosSSH
from htmiko.extreme import ExtremeSlxSSH
from htmiko.extreme import ExtremeTierraSSH
from htmiko.extreme import ExtremeVspSSH
from htmiko.extreme import ExtremeWingSSH
from htmiko.f5 import F5LinuxSSH
from htmiko.f5 import F5TmshSSH
from htmiko.fiberstore import FiberstoreFsosSSH
from htmiko.fiberstore import FiberstoreFsosV2SSH
from htmiko.fiberstore import FiberstoreFsosV2Telnet
from htmiko.fiberstore import FiberstoreNetworkOSSSH
from htmiko.flexvnf import FlexvnfSSH
from htmiko.fortinet import FortinetSSH
from htmiko.garderos import GarderosGrsSSH
from htmiko.genexis import GenexisSOLT33Telnet
from htmiko.hillstone import HillstoneStoneosSSH
from htmiko.hp import HPComwareSSH
from htmiko.hp import HPComwareTelnet
from htmiko.hp import HPProcurveSSH
from htmiko.hp import HPProcurveTelnet
from htmiko.huawei import HuaweiSmartAXSSH
from htmiko.huawei import HuaweiSmartAXSSHMMI
from htmiko.huawei import HuaweiSSH
from htmiko.huawei import HuaweiTelnet
from htmiko.huawei import HuaweiVrpv8SSH
from htmiko.infinera import InfineraPacketSSH
from htmiko.infinera import InfineraPacketTelnet
from htmiko.ipinfusion import IpInfusionOcNOSSSH
from htmiko.ipinfusion import IpInfusionOcNOSTelnet
from htmiko.juniper import JuniperFileTransfer
from htmiko.juniper import JuniperScreenOsSSH
from htmiko.juniper import JuniperSSH
from htmiko.juniper import JuniperTelnet
from htmiko.keymile import KeymileNOSSSH
from htmiko.keymile import KeymileSSH
from htmiko.lancom import LancomLCOSSX4SSH
from htmiko.linux import LinuxFileTransfer
from htmiko.linux import LinuxSSH
from htmiko.maipu import MaipuSSH
from htmiko.maipu import MaipuTelnet
from htmiko.mellanox import MellanoxMlnxosSSH
from htmiko.mikrotik import MikrotikRouterOsFileTransfer
from htmiko.mikrotik import MikrotikRouterOsSSH
from htmiko.mikrotik import MikrotikSwitchOsSSH
from htmiko.moxa import MoxaNosSSH
from htmiko.mrv import MrvLxSSH
from htmiko.mrv import MrvOptiswitchSSH
from htmiko.nec import NecIxSSH
from htmiko.nec import NecIxTelnet
from htmiko.netapp import NetAppcDotSSH
from htmiko.netgear import NetgearProSafeSSH
from htmiko.nokia import NokiaIsamSSH
from htmiko.nokia import NokiaSrlSSH
from htmiko.nokia import NokiaSrosFileTransfer
from htmiko.nokia import NokiaSrosSSH
from htmiko.nokia import NokiaSrosTelnet
from htmiko.oneaccess import OneaccessOneOSSSH
from htmiko.oneaccess import OneaccessOneOSTelnet
from htmiko.opengear import OpengearLinuxSSH
from htmiko.optilink import OptilinkEOLT9702Telnet
from htmiko.optilink import OptilinkEOLT11444Telnet
from htmiko.optilink import OptilinkGOLT924Telnet
from htmiko.ovs import OvsLinuxSSH
from htmiko.paloalto import PaloAltoPanosSSH
from htmiko.paloalto import PaloAltoPanosTelnet
from htmiko.perle import PerleIolanSSH
from htmiko.pluribus import PluribusSSH
from htmiko.quanta import QuantaMeshSSH
from htmiko.rad import RadETXSSH
from htmiko.rad import RadETXTelnet
from htmiko.raisecom import RaisecomRoapSSH
from htmiko.raisecom import RaisecomRoapTelnet
from htmiko.ruckus import RuckusFastironSSH
from htmiko.ruckus import RuckusFastironTelnet
from htmiko.ruijie import RuijieOSSSH
from htmiko.ruijie import RuijieOSTelnet
from htmiko.silverpeak import SilverPeakVXOASSH
from htmiko.sixwind import SixwindOSSSH
from htmiko.smartoptics import SmartOpticsDWDMSSH
from htmiko.sophos import SophosSfosSSH
from htmiko.supermicro import SmciSwitchSmisSSH
from htmiko.supermicro import SmciSwitchSmisTelnet
from htmiko.telcosystems import TelcoSystemsBinosSSH
from htmiko.telcosystems import TelcoSystemsBinosTelnet
from htmiko.teldat import TeldatCITSSH
from htmiko.teldat import TeldatCITTelnet
from htmiko.terminal_server import TerminalServerSSH
from htmiko.terminal_server import TerminalServerTelnet
from htmiko.tplink import TPLinkJetStreamSSH
from htmiko.tplink import TPLinkJetStreamTelnet
from htmiko.ubiquiti import UbiquitiEdgeRouterFileTransfer
from htmiko.ubiquiti import UbiquitiEdgeRouterSSH
from htmiko.ubiquiti import UbiquitiEdgeSSH
from htmiko.ubiquiti import UbiquitiUnifiSwitchSSH
from htmiko.vertiv import VertivMPHSSH
from htmiko.vyos import VyOSSSH
from htmiko.watchguard import WatchguardFirewareSSH
from htmiko.yamaha import YamahaSSH
from htmiko.yamaha import YamahaTelnet
from htmiko.zte import ZteZxrosSSH
from htmiko.zte import ZteZxrosTelnet
from htmiko.zyxel import ZyxelSSH

if TYPE_CHECKING:
    from htmiko.base_connection import BaseConnection
    from htmiko.scp_handler import BaseFileTransfer

GenericSSH = TerminalServerSSH
GenericTelnet = TerminalServerTelnet

# The keys of this dictionary are the supported device_types
CLASS_MAPPER_BASE = {
    "a10": A10SSH,
    "accedian": AccedianSSH,
    "adtran_os": AdtranOSSSH,
    "adva_fsp150f2": AdvaAosFsp150F2SSH,
    "adva_fsp150f3": AdvaAosFsp150F3SSH,
    "alaxala_ax36s": AlaxalaAx36sSSH,
    "alaxala_ax26s": AlaxalaAx36sSSH,
    "alcatel_aos": AlcatelAosSSH,
    "alcatel_sros": NokiaSrosSSH,
    "allied_telesis_awplus": AlliedTelesisAwplusSSH,
    "apc_aos": ApcAosSSH,
    "apresia_aeos": ApresiaAeosSSH,
    "arista_eos": AristaSSH,
    "arris_cer": ArrisCERSSH,
    "aruba_os": ArubaOsSSH,
    "aruba_aoscx": ArubaCxSSH,
    "aruba_osswitch": HPProcurveSSH,
    "aruba_procurve": HPProcurveSSH,
    "asterfusion_asternos": AsterfusionAsterNOSSSH,
    "audiocode_72": Audiocode72SSH,
    "audiocode_66": Audiocode66SSH,
    "audiocode_shell": AudiocodeShellSSH,
    "avaya_ers": ExtremeErsSSH,
    "avaya_vsp": ExtremeVspSSH,
    "bintec_boss": BintecBossSSH,
    "broadcom_icos": BroadcomIcosSSH,
    "brocade_fos": BrocadeFOSSSH,
    "brocade_fastiron": RuckusFastironSSH,
    "brocade_netiron": ExtremeNetironSSH,
    "brocade_nos": ExtremeNosSSH,
    "brocade_vdx": ExtremeNosSSH,
    "brocade_vyos": VyOSSSH,
    "checkpoint_gaia": CheckPointGaiaSSH,
    "calix_b6": CalixB6SSH,
    "calix_exa": CalixExaSSH,
    "casa_cmts": CasaCMTSSSH,
    "cdot_cros": CdotCrosSSH,
    "centec_os": CentecOSSSH,
    "ciena_saos": CienaSaosSSH,
    "ciena_saos10": CienaSaos10SSH,
    "ciena_waveserver": CienaWaveserverSSH,
    "cisco_ap": CiscoApSSH,
    "cisco_apic": CiscoApicSSH,
    "cisco_asa": CiscoAsaSSH,
    "cisco_ftd": CiscoFtdSSH,
    "cisco_ios": CiscoIosSSH,
    "cisco_nxos": CiscoNxosSSH,
    "cisco_s200": CiscoS200SSH,
    "cisco_s300": CiscoS300SSH,
    "cisco_tp": CiscoTpTcCeSSH,
    "cisco_viptela": CiscoViptelaSSH,
    "cisco_wlc": CiscoWlcSSH,
    "cisco_ioswlc": CiscoIosSSH,
    "cisco_xe": CiscoIosSSH,
    "cisco_xr": CiscoXrSSH,
    "cloudgenix_ion": CloudGenixIonSSH,
    "corelight_linux": CorelightLinuxSSH,
    "coriant": CoriantSSH,
    "cumulus_linux": CumulusLinuxSSH,
    "dell_dnos9": DellForce10SSH,
    "dell_force10": DellForce10SSH,
    "dell_os6": DellDNOS6SSH,
    "dell_os9": DellForce10SSH,
    "dell_os10": DellOS10SSH,
    "dell_sonic": DellSonicSSH,
    "dell_powerconnect": DellPowerConnectSSH,
    "dell_isilon": DellIsilonSSH,
    "dlink_ds": DlinkDSSSH,
    "digi_transport": DigiTransportSSH,
    "edgecore_sonic": EdgecoreSonicSSH,
    "endace": EndaceSSH,
    "ekinops_ek360": EkinopsEk360SSH,
    "eltex": EltexSSH,
    "eltex_esr": EltexEsrSSH,
    "enterasys": EnterasysSSH,
    "ericsson_ipos": EricssonIposSSH,
    "ericsson_mltn63": EricssonMinilink63SSH,
    "ericsson_mltn66": EricssonMinilink66SSH,
    "extreme": ExtremeExosSSH,
    "extreme_ers": ExtremeErsSSH,
    "extreme_exos": ExtremeExosSSH,
    "extreme_netiron": ExtremeNetironSSH,
    "extreme_nos": ExtremeNosSSH,
    "extreme_slx": ExtremeSlxSSH,
    "extreme_tierra": ExtremeTierraSSH,
    "extreme_vdx": ExtremeNosSSH,
    "extreme_vsp": ExtremeVspSSH,
    "extreme_wing": ExtremeWingSSH,
    "f5_ltm": F5TmshSSH,
    "f5_tmsh": F5TmshSSH,
    "f5_linux": F5LinuxSSH,
    "fiberstore_fsos": FiberstoreFsosSSH,
    "fiberstore_fsosv2": FiberstoreFsosV2SSH,
    "fiberstore_networkos": FiberstoreNetworkOSSSH,
    "flexvnf": FlexvnfSSH,
    "fortinet": FortinetSSH,
    "garderos_grs": GarderosGrsSSH,
    "generic": GenericSSH,
    "generic_termserver": TerminalServerSSH,
    "h3c_comware": HPComwareSSH,
    "hillstone_stoneos": HillstoneStoneosSSH,
    "hp_comware": HPComwareSSH,
    "hp_procurve": HPProcurveSSH,
    "huawei": HuaweiSSH,
    "huawei_smartaxmmi": HuaweiSmartAXSSHMMI,
    "huawei_smartax": HuaweiSmartAXSSH,
    "huawei_olt": HuaweiSmartAXSSH,
    "huawei_vrp": HuaweiSSH,
    "huawei_vrpv8": HuaweiVrpv8SSH,
    "infinera_packet": InfineraPacketSSH,
    "ipinfusion_ocnos": IpInfusionOcNOSSSH,
    "juniper": JuniperSSH,
    "juniper_junos": JuniperSSH,
    "juniper_screenos": JuniperScreenOsSSH,
    "keymile": KeymileSSH,
    "keymile_nos": KeymileNOSSSH,
    "lancom_lcossx4": LancomLCOSSX4SSH,
    "linux": LinuxSSH,
    "mikrotik_routeros": MikrotikRouterOsSSH,
    "mikrotik_switchos": MikrotikSwitchOsSSH,
    "mellanox": MellanoxMlnxosSSH,
    "mellanox_mlnxos": MellanoxMlnxosSSH,
    "moxa_nos": MoxaNosSSH,
    "mrv_lx": MrvLxSSH,
    "mrv_optiswitch": MrvOptiswitchSSH,
    "nec_ix": NecIxSSH,
    "netapp_cdot": NetAppcDotSSH,
    "netgear_prosafe": NetgearProSafeSSH,
    "netscaler": NetscalerSSH,
    "nokia_isam": NokiaIsamSSH,
    "nokia_sros": NokiaSrosSSH,
    "nokia_srl": NokiaSrlSSH,
    "oneaccess_oneos": OneaccessOneOSSSH,
    "opengear_linux": OpengearLinuxSSH,
    "ovs_linux": OvsLinuxSSH,
    "paloalto_panos": PaloAltoPanosSSH,
    "pluribus": PluribusSSH,
    "perle_iolan": PerleIolanSSH,
    "quanta_mesh": QuantaMeshSSH,
    "rad_etx": RadETXSSH,
    "raisecom_roap": RaisecomRoapSSH,
    "ruckus_fastiron": RuckusFastironSSH,
    "ruijie_os": RuijieOSSSH,
    "silverpeak_vxoa": SilverPeakVXOASSH,
    "sixwind_os": SixwindOSSSH,
    "smartoptics_dwdm": SmartOpticsDWDMSSH,
    "sophos_sfos": SophosSfosSSH,
    "supermicro_smis": SmciSwitchSmisSSH,
    "telcosystems_binos": TelcoSystemsBinosSSH,
    "teldat_cit": TeldatCITSSH,
    "tplink_jetstream": TPLinkJetStreamSSH,
    # ubiquiti_airos - Placeholder agreed to with NTC (if this driver is created in future)
    "ubiquiti_edge": UbiquitiEdgeSSH,
    "ubiquiti_edgerouter": UbiquitiEdgeRouterSSH,
    "ubiquiti_edgeswitch": UbiquitiEdgeSSH,
    "ubiquiti_unifiswitch": UbiquitiUnifiSwitchSSH,
    "vertiv_mph": VertivMPHSSH,
    "vyatta_vyos": VyOSSSH,
    "vyos": VyOSSSH,
    "watchguard_fireware": WatchguardFirewareSSH,
    "zte_zxros": ZteZxrosSSH,
    "yamaha": YamahaSSH,
    "zyxel_os": ZyxelSSH,
    "maipu": MaipuSSH,
}

FILE_TRANSFER_MAP = {
    "aruba_os": ArubaOsFileTransfer,
    "arista_eos": AristaFileTransfer,
    "ciena_saos": CienaSaosFileTransfer,
    "cisco_asa": CiscoAsaFileTransfer,
    "cisco_ios": CiscoIosFileTransfer,
    "cisco_nxos": CiscoNxosFileTransfer,
    "cisco_ioswlc": CiscoIosFileTransfer,
    "cisco_xe": CiscoIosFileTransfer,
    "cisco_xr": CiscoXrFileTransfer,
    "dell_os10": DellOS10FileTransfer,
    "extreme_exos": ExtremeExosFileTransfer,
    "juniper_junos": JuniperFileTransfer,
    "linux": LinuxFileTransfer,
    "nokia_sros": NokiaSrosFileTransfer,
    "mikrotik_routeros": MikrotikRouterOsFileTransfer,
    "ubiquiti_edgerouter": UbiquitiEdgeRouterFileTransfer,
}

# Also support keys that end in _ssh
new_mapper = {}
for k, v in CLASS_MAPPER_BASE.items():
    new_mapper[k] = v
    alt_key = k + "_ssh"
    new_mapper[alt_key] = v
CLASS_MAPPER = new_mapper

new_mapper = {}
for k, v in FILE_TRANSFER_MAP.items():
    new_mapper[k] = v
    alt_key = k + "_ssh"
    new_mapper[alt_key] = v
FILE_TRANSFER_MAP = new_mapper

# Add telnet drivers
CLASS_MAPPER["adtran_os_telnet"] = AdtranOSTelnet
CLASS_MAPPER["apresia_aeos_telnet"] = ApresiaAeosTelnet
CLASS_MAPPER["arista_eos_telnet"] = AristaTelnet
CLASS_MAPPER["aruba_procurve_telnet"] = HPProcurveTelnet
CLASS_MAPPER["audiocode_72_telnet"] = Audiocode72Telnet
CLASS_MAPPER["audiocode_66_telnet"] = Audiocode66Telnet
CLASS_MAPPER["audiocode_shell_telnet"] = AudiocodeShellTelnet
CLASS_MAPPER["bintec_boss_telnet"] = BintecBossTelnet
CLASS_MAPPER["brocade_fastiron_telnet"] = RuckusFastironTelnet
CLASS_MAPPER["brocade_netiron_telnet"] = ExtremeNetironTelnet
CLASS_MAPPER["calix_b6_telnet"] = CalixB6Telnet
CLASS_MAPPER["calix_exa_telnet"] = CalixExaTelnet
CLASS_MAPPER["centec_os_telnet"] = CentecOSTelnet
CLASS_MAPPER["ciena_saos_telnet"] = CienaSaosTelnet
CLASS_MAPPER["cisco_ios_telnet"] = CiscoIosTelnet
CLASS_MAPPER["cisco_nxos_telnet"] = CiscoNxosTelnet
CLASS_MAPPER["cisco_ioswlc_telnet"] = CiscoIosTelnet
CLASS_MAPPER["cisco_xe_telnet"] = CiscoIosTelnet
CLASS_MAPPER["cisco_xr_telnet"] = CiscoXrTelnet
CLASS_MAPPER["cisco_s200_telnet"] = CiscoS200Telnet
CLASS_MAPPER["cisco_s300_telnet"] = CiscoS300Telnet
CLASS_MAPPER["dell_dnos6_telnet"] = DellDNOS6Telnet
CLASS_MAPPER["dell_powerconnect_telnet"] = DellPowerConnectTelnet
CLASS_MAPPER["dlink_ds_telnet"] = DlinkDSTelnet
CLASS_MAPPER["extreme_telnet"] = ExtremeExosTelnet
CLASS_MAPPER["extreme_exos_telnet"] = ExtremeExosTelnet
CLASS_MAPPER["extreme_netiron_telnet"] = ExtremeNetironTelnet
CLASS_MAPPER["fiberstore_fsosv2_telnet"] = FiberstoreFsosV2Telnet
CLASS_MAPPER["generic_telnet"] = GenericTelnet
CLASS_MAPPER["generic_termserver_telnet"] = TerminalServerTelnet
CLASS_MAPPER["genexis_solt33_telnet"] = GenexisSOLT33Telnet
CLASS_MAPPER["hp_procurve_telnet"] = HPProcurveTelnet
CLASS_MAPPER["hp_comware_telnet"] = HPComwareTelnet
CLASS_MAPPER["huawei_telnet"] = HuaweiTelnet
CLASS_MAPPER["huawei_olt_telnet"] = HuaweiSmartAXSSH
CLASS_MAPPER["infinera_packet_telnet"] = InfineraPacketTelnet
CLASS_MAPPER["ipinfusion_ocnos_telnet"] = IpInfusionOcNOSTelnet
CLASS_MAPPER["juniper_junos_telnet"] = JuniperTelnet
CLASS_MAPPER["maipu_telnet"] = MaipuTelnet
CLASS_MAPPER["nec_ix_telnet"] = NecIxTelnet
CLASS_MAPPER["nokia_sros_telnet"] = NokiaSrosTelnet
CLASS_MAPPER["oneaccess_oneos_telnet"] = OneaccessOneOSTelnet
CLASS_MAPPER["optilink_eolt9702_telnet"] = OptilinkEOLT9702Telnet
CLASS_MAPPER["optilink_eolt11444_telnet"] = OptilinkEOLT11444Telnet
CLASS_MAPPER["optilink_golt924_telnet"] = OptilinkGOLT924Telnet
CLASS_MAPPER["paloalto_panos_telnet"] = PaloAltoPanosTelnet
CLASS_MAPPER["rad_etx_telnet"] = RadETXTelnet
CLASS_MAPPER["raisecom_telnet"] = RaisecomRoapTelnet
CLASS_MAPPER["ruckus_fastiron_telnet"] = RuckusFastironTelnet
CLASS_MAPPER["ruijie_os_telnet"] = RuijieOSTelnet
CLASS_MAPPER["supermicro_smis_telnet"] = SmciSwitchSmisTelnet
CLASS_MAPPER["telcosystems_binos_telnet"] = TelcoSystemsBinosTelnet
CLASS_MAPPER["teldat_cit_telnet"] = TeldatCITTelnet
CLASS_MAPPER["tplink_jetstream_telnet"] = TPLinkJetStreamTelnet
CLASS_MAPPER["yamaha_telnet"] = YamahaTelnet
CLASS_MAPPER["zte_zxros_telnet"] = ZteZxrosTelnet

# Add serial drivers
CLASS_MAPPER["cisco_ios_serial"] = CiscoIosSerial

# Add general terminal_server driver and autodetect
CLASS_MAPPER["terminal_server"] = TerminalServerSSH
CLASS_MAPPER["autodetect"] = TerminalServerSSH

platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_base = list(CLASS_MAPPER_BASE.keys())
platforms_base.sort()
platforms_str = "\n".join(platforms_base)
platforms_str = "\n" + platforms_str

scp_platforms = list(FILE_TRANSFER_MAP.keys())
scp_platforms.sort()
scp_platforms_str = "\n".join(scp_platforms)
scp_platforms_str = "\n" + scp_platforms_str

telnet_platforms = [x for x in platforms if "telnet" in x]
telnet_platforms_str = "\n".join(telnet_platforms)
telnet_platforms_str = "\n" + telnet_platforms_str


def ConnectHandler(*args: Any, **kwargs: Any) -> "BaseConnection":
    """Factory function selects the proper class and creates object based on device_type."""
    device_type = kwargs["device_type"]
    if device_type not in platforms:
        if device_type is None:
            msg_str = platforms_str
        else:
            msg_str = telnet_platforms_str if "telnet" in device_type else platforms_str
        raise ValueError(
            "Unsupported 'device_type' currently supported platforms are: {}".format(
                msg_str,
            ),
        )
    ConnectionClass = ssh_dispatcher(device_type)
    return ConnectionClass(*args, **kwargs)


def TelnetFallback(*args: Any, **kwargs: Any) -> "BaseConnection":
    """If an SSH connection fails, try to fallback to Telnet."""
    alternative_device = None
    try:
        return ConnectHandler(*args, **kwargs)
    except (HTMikoTimeoutException, ConnectionRefusedError):
        device_type = kwargs["device_type"]
        # platforms_str is the base form (i.e. does not have the '_ssh' suffix)
        if device_type in platforms_str:
            alternative_device = f"{device_type}_telnet"
        elif "_ssh" in device_type:
            alternative_device = re.sub("_ssh", "_telnet", device_type)

        if alternative_device in platforms:
            kwargs["device_type"] = alternative_device
            return ConnectHandler(*args, **kwargs)
        raise


def ConnLogOnly(
    log_file: str = "htmiko.log",
    log_level: Optional[int] = None,
    log_format: Optional[str] = None,
    **kwargs: Any,
) -> Optional["BaseConnection"]:
    """
    Dispatcher function that will return either: htmiko_object or None

    Excluding errors in logging configuration should never generate an exception
    all errors should be logged.
    """

    import logging

    if log_level is None:
        log_level = logging.ERROR
    if log_format is None:
        log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"

    logging.basicConfig(filename=log_file, level=log_level, format=log_format)
    logger = logging.getLogger(__name__)

    try:
        kwargs["auto_connect"] = False
        net_connect = ConnectHandler(**kwargs)
        hostname = net_connect.host
        port = net_connect.port
        device_type = net_connect.device_type

        net_connect._open()
        msg = f"HTMiko connection succesful to {hostname}:{port}"
        logger.info(msg)
        return net_connect
    except HTMikoAuthenticationException as e:
        msg = (
            f"Authentication failure to: {hostname}:{port} ({device_type})\n\n{str(e)}"
        )
        logger.error(msg)
        return None
    except HTMikoTimeoutException as e:
        if "DNS failure" in str(e):
            msg = f"Device failed due to a DNS failure, hostname {hostname}"
        elif "TCP connection to device failed" in str(e):
            msg = f"HTMiko was unable to reach the provided host and port: {hostname}:{port}"
            msg += f"\n\n{str(e)}"
        else:
            msg = f"An unknown HTMikoTimeoutException occurred:\n\n{str(e)}"
        logger.error(msg)
        return None
    except Exception as e:
        msg = f"An unknown exception occurred during connection:\n\n{str(e)}"
        logger.error(msg)
        return None


def ConnUnify(
    **kwargs: Any,
) -> "BaseConnection":
    try:
        kwargs["auto_connect"] = False
        net_connect = ConnectHandler(**kwargs)
        hostname = net_connect.host
        port = net_connect.port
        device_type = net_connect.device_type
        general_msg = f"Connection failure to {hostname}:{port} ({device_type})\n\n"

        net_connect._open()
        return net_connect
    except HTMikoAuthenticationException as e:
        msg = general_msg + str(e)
        raise ConnectionException(msg)
    except HTMikoTimeoutException as e:
        msg = general_msg + str(e)
        raise ConnectionException(msg)
    except Exception as e:
        msg = f"An unknown exception occurred during connection:\n\n{str(e)}"
        raise ConnectionException(msg)


def ssh_dispatcher(device_type: str) -> Type["BaseConnection"]:
    """Select the class to be instantiated based on vendor/platform."""
    return CLASS_MAPPER[device_type]


def redispatch(
    obj: "BaseConnection",
    device_type: str,
    session_prep: bool = True,
) -> None:
    """Dynamically change connection object's class to proper class.
    Generally used with terminal_server device_type when you need to redispatch after interacting
    with terminal server.
    """
    new_class = ssh_dispatcher(device_type)
    obj.device_type = device_type
    obj.__class__ = new_class
    if session_prep:
        obj._try_session_preparation()


def FileTransfer(*args: Any, **kwargs: Any) -> "BaseFileTransfer":
    """Factory function selects the proper SCP class and creates object based on device_type."""
    if len(args) >= 1:
        device_type = args[0].device_type
    else:
        device_type = kwargs["ssh_conn"].device_type
    if device_type not in scp_platforms:
        raise ValueError(
            "Unsupported SCP device_type: currently supported platforms are: {}".format(
                scp_platforms_str,
            ),
        )
    FileTransferClass: Type["BaseFileTransfer"]
    FileTransferClass = FILE_TRANSFER_MAP[device_type]
    return FileTransferClass(*args, **kwargs)
