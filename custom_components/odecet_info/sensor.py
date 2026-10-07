"""Meter registers and the timestamp of the next allowed manual sync."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_import_statistics
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit_conversion import EnergyConverter, VolumeConverter

from custom_components.odecet_info.const import CONF_MEDIUMS, DOMAIN
from custom_components.odecet_info.coordinator import OdecetCoordinator
from custom_components.odecet_info.entry import OdecetConfigEntry
from custom_components.odecet_info.models import Medium, Meter
from custom_components.odecet_info.parse import SCALE_UNIT, measurement_kind
from custom_components.odecet_info.statistics import hourly_statistics

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OdecetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one register sensor per enabled meter, plus the cooldown sensor."""
    coordinator: OdecetCoordinator = entry.runtime_data
    known: set[str] = set()
    account = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    via_device_id = account.id if account is not None else None

    def _add_meters() -> None:
        if not coordinator.data:
            return
        enabled = set(entry.options.get(CONF_MEDIUMS, []))
        fresh: list[MeterSensor] = []
        for meter in coordinator.data.meters():
            if meter.medium.value not in enabled:
                continue
            unique = f"{entry.entry_id}_{meter.medium.value}_{meter.serial}"
            if unique in known:
                continue
            known.add(unique)
            fresh.append(MeterSensor(coordinator, meter, unique, via_device_id))
        if fresh:
            async_add_entities(fresh)

    entry.async_on_unload(coordinator.async_add_listener(_add_meters))
    _add_meters()
    async_add_entities([NextManualSyncSensor(coordinator)])


class MeterSensor(CoordinatorEntity[OdecetCoordinator], SensorEntity):
    """Latest register value for one physical meter."""

    _attr_has_entity_name = True
    _attr_translation_key = "reading"
    _attr_suggested_display_precision = 3

    def __init__(
        self,
        coordinator: OdecetCoordinator,
        meter: Meter,
        unique_id: str,
        via_device_id: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._serial = meter.serial
        self._medium = meter.medium
        self._attr_unique_id = unique_id
        entry_id = coordinator.config_entry.entry_id
        device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{meter.medium.value}_{meter.serial}")},
            name=f"{meter.medium.label} [S/N {meter.serial}]",
            translation_key=meter.medium.value,
            translation_placeholders={"serial": meter.serial},
            manufacturer="odecet.info",
            model=meter.medium.label,
            serial_number=meter.serial,
        )
        # Newer Home Assistant wants the registry id. Older releases still
        # take the (domain, identifier) tuple.
        if via_device_id is not None and "via_device_id" in DeviceInfo.__annotations__:
            device_info["via_device_id"] = via_device_id  # type: ignore[typeddict-unknown-key]
        else:
            device_info["via_device"] = (DOMAIN, entry_id)
        self._attr_device_info = device_info

    def _meter(self) -> Meter | None:
        if not self.coordinator.data:
            return None
        for meter in self.coordinator.data.meters():
            if meter.serial == self._serial and meter.medium is self._medium:
                return meter
        return None

    @property
    def available(self) -> bool:
        """Unavailable when the latest successful fetch no longer includes this meter."""
        return super().available and self._meter() is not None

    @property
    def native_value(self) -> float | None:
        meter = self._meter()
        if meter is None:
            return None
        return float(meter.latest.value)

    @property
    def native_unit_of_measurement(self) -> str | None:
        meter = self._meter()
        if meter is None:
            return None
        return meter.unit

    @property
    def device_class(self) -> SensorDeviceClass | None:
        meter = self._meter()
        if meter is None or measurement_kind(meter.unit) is None:
            return None
        if meter.medium in {Medium.COLD_WATER, Medium.HOT_WATER}:
            if measurement_kind(meter.unit) == "volume":
                return SensorDeviceClass.WATER
        if meter.medium is Medium.HEAT and measurement_kind(meter.unit) == "energy":
            return SensorDeviceClass.ENERGY
        return None

    @property
    def state_class(self) -> SensorStateClass | None:
        meter = self._meter()
        if meter is None:
            return None
        if meter.unit == SCALE_UNIT or measurement_kind(meter.unit) is not None:
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        meter = self._meter()
        if meter is None:
            return {}
        return {
            "serial": meter.serial,
            "module_serial": meter.module_serial,
            "raw_unit": meter.raw_unit,
            "medium": meter.medium.value,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._import_statistics()

    def _handle_coordinator_update(self) -> None:
        self._import_statistics()
        super()._handle_coordinator_update()

    def _import_statistics(self) -> None:
        """Write hourly history onto this entity. Skip meters with no known unit."""
        meter = self._meter()
        kind = measurement_kind(meter.unit) if meter else None
        if meter is None or self.entity_id is None:
            return
        if kind is None and meter.unit != SCALE_UNIT:
            return
        points = hourly_statistics(meter.readings)
        if not points:
            return
        name = self.name if isinstance(self.name, str) else self.entity_id
        if kind == "volume":
            unit_class: str | None = VolumeConverter.UNIT_CLASS
        elif kind == "energy":
            unit_class = EnergyConverter.UNIT_CLASS
        else:
            unit_class = None
        metadata: StatisticMetaData = {
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": name,
            "source": "recorder",
            "statistic_id": self.entity_id,
            "unit_class": unit_class,
            "unit_of_measurement": meter.unit,
        }
        statistics: list[StatisticData] = []
        for point in points:
            row: StatisticData = {
                "start": point.start,
                "state": point.state,
                "sum": point.sum,
            }
            if point.last_reset is not None:
                row["last_reset"] = point.last_reset
            statistics.append(row)
        try:
            async_import_statistics(self.hass, metadata, statistics)
        except (HomeAssistantError, KeyError):
            # KeyError is the recorder not running. The live register still updates.
            _LOGGER.exception("Could not import statistics for meter %s", self._serial)


class NextManualSyncSensor(CoordinatorEntity[OdecetCoordinator], SensorEntity):
    """When the one-minute gate opens again. Home Assistant renders this as a countdown."""

    _attr_has_entity_name = True
    _attr_translation_key = "next_manual_sync"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OdecetCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_next_manual_sync"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="odecet.info",
            model="Account",
            configuration_url="https://odecet.info/",
        )

    @property
    def available(self) -> bool:
        """Stay visible while a failed sync is cooling down."""
        return True

    @property
    def native_value(self) -> datetime:
        return self.coordinator.next_manual_sync
