import aioble
import bluetooth
import uasyncio as aio
from drivers.pcf85063a import set_external_rtc
import enums

from library.logger import Log
log = Log(__name__, Log.INFO).get_logger()

"""
    MicroPython BLE Manager Module
    ------------------
    This module is responsible for managing the BLE connection between the firmware and the phone app.
    It is responsible for:
    - Initialising the BLE connection
    - Sending and receiving data from the phone app
    - Handling the BLE connection
    - Handling the BLE disconnection
    - Handling the BLE reconnection
"""

# Davey AP Services UUID
_lights_Service_UUID = bluetooth.UUID(0xDA10)
_heat_Service_UUID = bluetooth.UUID(0xDA20)
_wf_Service_UUID = bluetooth.UUID(0xDA30)
_gl_Service_UUID = bluetooth.UUID(0xDA40)
_config_Service_UUID = bluetooth.UUID(0xDA50)
_spa_refill_Service_UUID = bluetooth.UUID(0xDA60)
_status_Service_UUID = bluetooth.UUID(0xDA70)

# Davey AP Characteristics UUID
_SCHEDULE_1_Char_UUID = bluetooth.UUID(0xFFA1)
_SCHEDULE_2_Char_UUID = bluetooth.UUID(0xFFA2)
_MANUAL_CONFIG_Char_UUID = bluetooth.UUID(0xFFA3)
_MODE_Char_UUID = bluetooth.UUID(0xFFA4)
_STATUS_Char_UUID = bluetooth.UUID(0xFFA5)

_LIGHTS_BRAND_UUID = bluetooth.UUID(0xFFB1)
_TIME_SYNC_UUID = bluetooth.UUID(0xFFB2)

_WATER_TEMPERATURE_UUID = bluetooth.UUID(0xFFC1)


def get_ble_mac():
    # Get BLE MAC for device name:
    # return '0000'
    bt = bluetooth.BLE()
    if not bt.active():
        bt.active(True)
    mac = bt.config('mac')  # mac example: (0, b'd\xe83c3\x1a')
    mac_str = ''.join('{:02X}'.format(b) for b in mac[1])
    return mac_str


class BLEManager:
    # How frequently to send advertising beacons.
    _ADV_INTERVAL_MS = 250_000

    # Lights
    # Schedule 1: Start, End, Days, Enabled, Config
    # Schedule 2: Start, End, Days, Enabled, Config
    # Manual Config: Black, Red, Green, Blue, White, Yellow, Purple, Aqua, Slow, Fast
    # Mode: Off, Manual, Auto
    # Status: TRANSITION, Manual Off, Manual On, Scheduled Off, Scheduled Timer 1 On, Scheduled Timer 2 On
    #                 -1,          0,       1,            2,                   3,                   4

    # Water Feature (WF)
    # Schedule 1: Start, End, Days, Enabled
    # Schedule 2: Start, End, Days, Enabled
    # Manual Config: N/A
    # Mode: Off, Manual, Auto
    # Status: TRANSITION, Manual Off, Manual On, Scheduled Off, Scheduled Timer 1 On, Scheduled Timer 2 On

    # Heat
    # Schedule 1: Start, End, Days, Enabled, Config, Mode(Pool/Spa)
    # Schedule 2: Start, End, Days, Enabled, Config, Mode(Pool/Spa)
    # Manual Config: Pool Temp, Spa Temp
    # Mode: Off/Filter, Pool, Spa, Auto
    # Status: TRANSITION, Manual Off/Filter, Manual Pool, Manual Spa, Scheduled Off/Filter, Scheduled Timer 1 On, Scheduled Timer 2 On

    # Garden Light (GL)
    # Schedule 1: Start, End, Days, Enabled
    # Schedule 2: Start, End, Days, Enabled
    # Manual Config: N/A
    # Mode: Off, Manual, Auto
    # Status: TRANSITION, Manual Off, Manual On, Scheduled Off, Scheduled Timer 1 On, Scheduled Timer 2 On

    # Spa Refill
    # Manual Config: 1,2,3,4,5,6,7,8,9,10 (minutes)
    # Mode: Off, On
    # Status: TRANSITION, Manual Off, Manual On

    def __init__(self, i2c):
        self.i2c = i2c
        self.serial_number = get_ble_mac()
        self._connection = None
        # Create the BLE Services and Characteristics
        # Light GATT Service
        self.lights_service = aioble.Service(_lights_Service_UUID)
        self.lights_schedule1_char = aioble.Characteristic(
            self.lights_service, _SCHEDULE_1_Char_UUID, read=True, write=True)
        self.lights_schedule2_char = aioble.Characteristic(
            self.lights_service, _SCHEDULE_2_Char_UUID, read=True, write=True)
        self.lights_manual_config_char = aioble.Characteristic(
            self.lights_service, _MANUAL_CONFIG_Char_UUID, read=True, write=True,  notify=True)
        self.lights_mode_char = aioble.Characteristic(
            self.lights_service, _MODE_Char_UUID, read=True, write=True)
        self.lights_status_char = aioble.Characteristic(
            self.lights_service, _STATUS_Char_UUID, read=True, notify=True)
        # Water Feature GATT Service
        self.wf_service = aioble.Service(_wf_Service_UUID)
        self.wf_schedule1_char = aioble.Characteristic(
            self.wf_service, _SCHEDULE_1_Char_UUID, read=True, write=True)
        self.wf_schedule2_char = aioble.Characteristic(
            self.wf_service, _SCHEDULE_2_Char_UUID, read=True, write=True)
        self.wf_mode_char = aioble.Characteristic(
            self.wf_service, _MODE_Char_UUID, read=True, write=True)
        self.wf_status_char = aioble.Characteristic(
            self.wf_service, _STATUS_Char_UUID, read=True, notify=True)
        # Heat GATT Service
        self.heat_service = aioble.Service(_heat_Service_UUID)
        self.heat_schedule1_char = aioble.Characteristic(
            self.heat_service, _SCHEDULE_1_Char_UUID, read=True, write=True)
        self.heat_schedule2_char = aioble.Characteristic(
            self.heat_service, _SCHEDULE_2_Char_UUID, read=True, write=True)
        self.heat_manual_config_char = aioble.Characteristic(
            self.heat_service, _MANUAL_CONFIG_Char_UUID, read=True, write=True, notify=True)
        self.heat_mode_char = aioble.Characteristic(
            self.heat_service, _MODE_Char_UUID, read=True, write=True)
        self.heat_status_char = aioble.Characteristic(
            self.heat_service, _STATUS_Char_UUID, read=True, notify=True)
        # Garden Light GATT Service
        self.gl_service = aioble.Service(_gl_Service_UUID)
        self.gl_schedule1_char = aioble.Characteristic(
            self.gl_service, _SCHEDULE_1_Char_UUID, read=True, write=True)
        self.gl_schedule2_char = aioble.Characteristic(
            self.gl_service, _SCHEDULE_2_Char_UUID, read=True, write=True)
        self.gl_mode_char = aioble.Characteristic(
            self.gl_service, _MODE_Char_UUID, read=True, write=True)
        self.gl_status_char = aioble.Characteristic(
            self.gl_service, _STATUS_Char_UUID, read=True, notify=True)

        # Spa Refill GATT Service
        self.spa_refill_service = aioble.Service(_spa_refill_Service_UUID)
        self.spa_refill_manual_config_char = aioble.Characteristic(
            self.spa_refill_service, _MANUAL_CONFIG_Char_UUID, read=True, write=True)
        self.spa_refill_mode_char = aioble.Characteristic(
            self.spa_refill_service, _MODE_Char_UUID, read=True, write=True)
        self.spa_refill_status_char = aioble.Characteristic(
            self.spa_refill_service, _STATUS_Char_UUID, read=True, notify=True)

        # Config GATT Service
        self.config_service = aioble.Service(_config_Service_UUID)
        self.lights_brand_char = aioble.Characteristic(
            self.config_service, _LIGHTS_BRAND_UUID, read=True, write=True)
        self.time_sync_char = aioble.Characteristic(
            self.config_service, _TIME_SYNC_UUID, read=True, write=True, notify=True)

        # Status GATT Service
        self.status_service = aioble.Service(_status_Service_UUID)
        self.water_temperature_char = aioble.Characteristic(
            self.status_service, _WATER_TEMPERATURE_UUID, read=True, notify=True)

        # Initialise the BLE Peripheral Task
        try:
            aioble.register_services(
                self.lights_service,
                self.wf_service,
                self.heat_service,
                self.gl_service,
                self.config_service,
                self.spa_refill_service,
                self.status_service,
            )
        except Exception as e:
            log.error(f"BLE Services Registration Error: {e}")

    '''
    Lights
    '''

    async def _task_lights_schedule1(self):
        while True:
            await self.lights_schedule1_char.written()
            schedule = self.lights_schedule1_char.read()
            log.info(f"Lights Schedule 1 Updated:{schedule}")
            # Update the lights schedule 1
            # call the lights schedule 1 update function

    async def _task_lights_schedule2(self):
        while True:
            await self.lights_schedule2_char.written()
            schedule = self.lights_schedule2_char.read()
            log.info(f"Lights Schedule 2 Updated:{schedule}")
            # Update the lights schedule 2
            # call the lights schedule 2 update function

    async def _task_lights_manual_config(self):
        while True:
            await self.lights_manual_config_char.written()
            manual_config = self.lights_manual_config_char.read()
            log.info(f"Lights Manual Config Updated:{manual_config}")
            # Update the lights manual config

    async def _task_lights_mode(self):
        while True:
            await self.lights_mode_char.written()
            mode = self.lights_mode_char.read()
            log.info(f"Lights Mode Updated:{mode}")
            self.update_char(self.lights_status_char, mode)

    '''
    Water Feature
    '''

    async def _task_wf_schedule1(self):
        while True:
            await self.wf_schedule1_char.written()
            schedule = self.wf_schedule1_char.read()
            log.info(f"Water Feature Schedule 1 Updated:{schedule}")
            # Update the water feature schedule 1
            # call the water feature schedule 1 update function

    async def _task_wf_schedule2(self):
        while True:
            await self.wf_schedule2_char.written()
            schedule = self.wf_schedule2_char.read()
            log.info(f"Water Feature Schedule 2 Updated:{schedule}")
            # Update the water feature schedule 2
            # call the water feature schedule 2 update function

    async def _task_wf_mode(self):
        while True:
            await self.wf_mode_char.written()
            mode = self.wf_mode_char.read()
            log.info(f"Water Feature Mode Updated:{mode}")
            # Update the water feature mode
            # call the water feature mode update function

    '''
    Heat
    '''

    async def _task_heat_schedule1(self):
        while True:
            await self.heat_schedule1_char.written()
            schedule = self.heat_schedule1_char.read()
            log.info(f"Heat Schedule 1 Updated:{schedule}")
            # Update the heat schedule 1
            # call the heat schedule 1 update function

    async def _task_heat_schedule2(self):
        while True:
            await self.heat_schedule2_char.written()
            schedule = self.heat_schedule2_char.read()
            log.info(f"Heat Schedule 2 Updated:{schedule}")
            # Update the heat schedule 2
            # call the heat schedule 2 update function

    async def _task_heat_manual_config(self):
        while True:
            await self.heat_manual_config_char.written()
            manual_config = self.heat_manual_config_char.read()
            pool = manual_config[0]
            spa = manual_config[1]
            log.info(
                f"Heat Manual Config Updated: {hex(manual_config[0]), hex(manual_config[1])}; Pool: {pool}C, Spa: {spa}C")
            # Update the heat manual config
            # call the heat manual config update function

    async def _task_heat_mode(self):
        while True:
            await self.heat_mode_char.written()
            mode = self.heat_mode_char.read()
            log.info(f"Heat Mode Updated:{mode}")
            if mode != enums.HeaterModes.Automatic:
                self.update_char(self.heat_status_char,
                                 enums.HeaterStatus.transition_)
            # Update the heat mode
            # call the heat mode update function

    '''
    Garden Light
    '''

    async def _task_gl_schedule1(self):
        while True:
            await self.gl_schedule1_char.written()
            schedule = self.gl_schedule1_char.read()
            log.info(f"Garden Light Schedule 1 Updated:{schedule}")
            # Update the garden light schedule 1
            # call the garden light schedule 1 update function

    async def _task_gl_schedule2(self):
        while True:
            await self.gl_schedule2_char.written()
            schedule = self.gl_schedule2_char.read()
            log.info(f"Garden Light Schedule 2 Updated:{schedule}")
            # Update the garden light schedule 2
            # call the garden light schedule 2 update function

    async def _task_gl_mode(self):
        while True:
            await self.gl_mode_char.written()
            mode = self.gl_mode_char.read()
            log.info(f"Garden Light Mode Updated:{mode}")
            # Update the garden light mode
            # call the garden light mode update function

    '''
    Spa Refill
    '''

    async def _task_spa_refill_manual_config(self):
        while True:
            await self.spa_refill_manual_config_char.written()
            manual_config = self.spa_refill_manual_config_char.read()
            log.info(f"Spa Refill Manual Config Updated:{manual_config}")
            # Update the spa refill manual config
            # call the spa refill manual config update function

    async def _task_spa_refill_mode(self):
        while True:
            await self.spa_refill_mode_char.written()
            mode = self.spa_refill_mode_char.read()
            log.info(f"Spa Refill Mode Updated:{mode}")
            self.update_char(self.spa_refill_status_char,
                             enums.Status.transition)
            # Update the spa refill mode
            # call the spa refill mode update function

    '''
    Config
    '''

    async def _task_lights_brand(self):
        while True:
            await self.lights_brand_char.written()
            brand = self.lights_brand_char.read()
            if brand is not None:
                log.info(f"Lights Brand Updated: {brand}")
            else:
                log.info(f"Lights Brand Updated: None")

    async def _task_time_sync(self):
        while True:
            await self.time_sync_char.written()
            time_sync = self.time_sync_char.read()
            try:
                t = time_sync.hex()
                yyyy, mm, dd, HH, MM, SS = (int(i) for i in (
                    t[0:4], t[4:6], t[6:8], t[8:10], t[10:12], t[12:14]))
                if t is not None:
                    log.info(
                        f"Time Sync Updated: {time_sync} {t}: {yyyy, mm, dd, HH, MM, SS}")
                    set_external_rtc(datetimeTuple=(yyyy, mm, dd, 0, HH, MM, SS, 0),
                                     i2c=self.i2c)
                else:
                    log.info(f"Time Sync Updated: None")
            except Exception as e:
                log.error(f"Time Sync Error: {e}")

    '''
    Status
    '''
    # NOTE: Status are read only, so they don't need a task
    # Water Temperature

    '''
    BLE Peripheral Task
    '''

    async def _task_ble_peripheral(self):
        while True:
            name = "dwap-" + self.serial_number[:8]
            # name = "apdw-" + self.serial_number[:8]
            log.critical(f"Advertising as {name}")
            async with await aioble.advertise(
                BLEManager._ADV_INTERVAL_MS,
                name=name,
                services=[
                    _lights_Service_UUID,
                    _wf_Service_UUID,
                    _heat_Service_UUID,
                    _gl_Service_UUID,
                    _spa_refill_Service_UUID,
                    _config_Service_UUID,
                    _status_Service_UUID,
                ],
            ) as self._connection:  # type: ignore
                log.warning(f"Connection from {self._connection.device}")
                await self._connection.disconnected()
                log.warning("Disconnected!")
                self._connection = None

    async def tasks(self):
        await aio.gather(
            self._task_ble_peripheral(),

            self._task_lights_schedule1(),
            self._task_lights_schedule2(),
            self._task_lights_manual_config(),
            self._task_lights_mode(),

            self._task_wf_schedule1(),
            self._task_wf_schedule2(),
            self._task_wf_mode(),

            self._task_heat_schedule1(),
            self._task_heat_schedule2(),
            self._task_heat_manual_config(),
            self._task_heat_mode(),

            self._task_gl_schedule1(),
            self._task_gl_schedule2(),
            self._task_gl_mode(),

            self._task_spa_refill_manual_config(),
            self._task_spa_refill_mode(),

            self._task_lights_brand(),
            self._task_time_sync(),
        )

    def write_char(self, char, value):
        '''
        Write a value to a characteristic
        Char must be a Characteristic object
        Value must be a bytes object
        '''
        char.write(value)

    def notify_char(self, char, value=None):
        '''
        Notify a value to a characteristic
        Char must be a Characteristic object
        Value must be a bytes object,
            if Value is None, then the characteristic is notified with last value
        '''
        if self._connection is not None:
            # check if notify is enabled
            try:
                if value is not None:
                    char.notify(self._connection, value)
                else:
                    char.notify(self._connection)
                return True
            except ValueError:
                log.debug("BLE Notify Failed: notify not enabled")
                return False
        log.debug("BLE Notify Failed: No Connection")
        return False

    def update_char(self, char, value):
        '''
        Write and notify a value to a characteristic
        Char must be a Characteristic object
        Value must be a bytes object
        '''
        self.write_char(char, value)
        return self.notify_char(char, value)

    def byte_to_int(self, byte):
        return int.from_bytes(byte, "little")

    def is_connected(self):
        return self._connection is not None
