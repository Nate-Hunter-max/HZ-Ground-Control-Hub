"""
Парсер бинарных телеметрических данных
Поддерживает формат TelemetryPacket (34 байта)
"""

import struct
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os


class TelemetryParser:
    """Парсер для бинарных файлов телеметрии в формате TelemetryPacket"""

    # Размер пакета телеметрии в байтах
    PACKET_SIZE = 34

    # Флаги системы (SystemFlags)
    SYSTEM_FLAGS = {
        0x01: 'ARMED',
        0x02: 'GPS_FIX',
        0x04: 'ALTITUDE_HOLD',
        0x08: 'BATTERY_LOW',
        0x10: 'SENSOR_ERROR',
        0x20: 'RECOVERY_MODE',
        0x40: 'DATA_LOGGING',
        0x80: 'TELEMETRY_ACTIVE'
    }

    def __init__(self):
        """Инициализация парсера"""
        self.packets = []
        self.start_time = None

    def parse_file(self, filename: str) -> pd.DataFrame:
        """
        Парсинг бинарного файла телеметрии

        Args:
            filename: Путь к файлу

        Returns:
            DataFrame с телеметрией
        """
        try:
            with open(filename, 'rb') as f:
                data = f.read()

            # Определяем количество пакетов
            total_packets = len(data) // self.PACKET_SIZE

            if len(data) % self.PACKET_SIZE != 0:
                print(f"Предупреждение: Размер файла не кратен {self.PACKET_SIZE} байт. "
                      f"Последние {len(data) % self.PACKET_SIZE} байт будут проигнорированы.")

            packets = []

            for i in range(total_packets):
                offset = i * self.PACKET_SIZE
                packet_data = data[offset:offset + self.PACKET_SIZE]

                try:
                    packet = self._parse_packet(packet_data)
                    packets.append(packet)
                except Exception as e:
                    print(f"Ошибка парсинга пакета {i}: {e}")
                    continue

            # Преобразуем в DataFrame
            if packets:
                df = pd.DataFrame(packets)
                return self._process_dataframe(df)
            else:
                return pd.DataFrame()

        except Exception as e:
            raise Exception(f"Ошибка чтения файла {filename}: {e}")

    def _parse_packet(self, data: bytes) -> Dict[str, Any]:
        """
        Парсинг одного пакета телеметрии (34 байта)

        Структура пакета:
        - time_ms (24-bit): байты 0-2 (+ 1 байт от следующего поля)
        - temp_cC (14-bit): оставшиеся биты + байт 3
        - pressPa (20-bit): байты 4-6 (+ 4 бита от следующего)
        - mag[3] (3x16-bit): байты 6-11
        - accel[3] (3x16-bit): байты 12-17
        - gyro[3] (3x16-bit): байты 18-23
        - lat_1e7 (30-bit): байты 24-27
        - lon_1e7 (30-bit): байты 28-31
        - flags (8-bit): байт 32
        """

        if len(data) != self.PACKET_SIZE:
            raise ValueError(f"Неверный размер пакета: {len(data)} вместо {self.PACKET_SIZE}")

        # Распаковываем как последовательность байтов
        packet_bytes = struct.unpack('34B', data)

        # Парсим битовые поля
        result = {}

        # time_ms (24-bit) - первые 3 байта
        time_ms = (packet_bytes[2] << 16) | (packet_bytes[1] << 8) | packet_bytes[0]
        result['time_ms'] = time_ms

        # temp_cC (14-bit) - биты из 4-го байта + часть 5-го
        temp_raw = ((packet_bytes[4] & 0x3F) << 8) | packet_bytes[3]
        if temp_raw & 0x2000:  # проверяем знак
            temp_raw -= 0x4000
        result['temp_cC'] = temp_raw / 100.0  # конвертируем в °C

        # pressPa (20-bit) - оставшиеся биты 5-го + 6-7 байты
        press_raw = ((packet_bytes[6] & 0x0F) << 16) | (packet_bytes[5] << 8) | ((packet_bytes[4] & 0xC0) >> 6)
        result['pressPa'] = press_raw

        # mag[3] (3x16-bit) - байты 8-13 (с учетом смещения из-за битовых полей)
        mag_start = 7
        result['mag_x'] = struct.unpack('<h', data[mag_start:mag_start + 2])[0]
        result['mag_y'] = struct.unpack('<h', data[mag_start + 2:mag_start + 4])[0]
        result['mag_z'] = struct.unpack('<h', data[mag_start + 4:mag_start + 6])[0]

        # accel[3] (3x16-bit)
        accel_start = mag_start + 6
        result['accel_x'] = struct.unpack('<h', data[accel_start:accel_start + 2])[0]
        result['accel_y'] = struct.unpack('<h', data[accel_start + 2:accel_start + 4])[0]
        result['accel_z'] = struct.unpack('<h', data[accel_start + 4:accel_start + 6])[0]

        # gyro[3] (3x16-bit)
        gyro_start = accel_start + 6
        result['gyro_x'] = struct.unpack('<h', data[gyro_start:gyro_start + 2])[0] / 10.0  # dps*10 -> dps
        result['gyro_y'] = struct.unpack('<h', data[gyro_start + 2:gyro_start + 4])[0] / 10.0
        result['gyro_z'] = struct.unpack('<h', data[gyro_start + 4:gyro_start + 6])[0] / 10.0

        # lat_1e7 и lon_1e7 (2x30-bit) - упрощенная версия как 32-bit
        lat_start = gyro_start + 6
        lat_raw = struct.unpack('<i', data[lat_start:lat_start + 4])[0]
        result['latitude'] = (lat_raw & 0x3FFFFFFF) / 1e7
        if lat_raw & 0x20000000:  # проверяем знак 30-битного числа
            result['latitude'] -= 107.3741824  # 2^30 / 1e7

        lon_start = lat_start + 4
        lon_raw = struct.unpack('<i', data[lon_start:lon_start + 4])[0]
        result['longitude'] = (lon_raw & 0x3FFFFFFF) / 1e7
        if lon_raw & 0x20000000:  # проверяем знак 30-битного числа
            result['longitude'] -= 107.3741824

        # flags (8-bit)
        flags_byte = packet_bytes[32]
        result['flags_raw'] = flags_byte

        # Расшифровываем флаги
        for flag_bit, flag_name in self.SYSTEM_FLAGS.items():
            result[f'flag_{flag_name.lower()}'] = bool(flags_byte & flag_bit)

        return result

    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Постобработка DataFrame"""
        if df.empty:
            return df

        # Создаем абсолютные временные метки
        if 'time_ms' in df.columns:
            # Предполагаем, что первый пакет - начало отсчета
            start_time_ms = df['time_ms'].iloc[0]
            df['timestamp'] = pd.to_datetime(
                (df['time_ms'] - start_time_ms) * 1000000,  # микросекунды
                unit='us'
            )

            # Также создаем относительное время в секундах
            df['time_s'] = (df['time_ms'] - start_time_ms) / 1000.0

        # Вычисляем производные величины
        self._calculate_derived_values(df)

        # Сортируем по времени
        if 'time_ms' in df.columns:
            df = df.sort_values('time_ms').reset_index(drop=True)

        return df

    def _calculate_derived_values(self, df: pd.DataFrame):
        """Вычисление производных величин"""
        if df.empty:
            return

        # Высота из давления (приблизительная формула)
        if 'pressPa' in df.columns:
            sea_level_pressure = 101325  # Па на уровне моря
            df['altitude'] = 44330 * (1 - (df['pressPa'] / sea_level_pressure) ** (1 / 5.255))

        # Общее ускорение
        if all(col in df.columns for col in ['accel_x', 'accel_y', 'accel_z']):
            df['accel_total'] = np.sqrt(
                df['accel_x'] ** 2 + df['accel_y'] ** 2 + df['accel_z'] ** 2
            ) / 1000.0  # mG -> G

        # Общее магнитное поле
        if all(col in df.columns for col in ['mag_x', 'mag_y', 'mag_z']):
            df['mag_total'] = np.sqrt(
                df['mag_x'] ** 2 + df['mag_y'] ** 2 + df['mag_z'] ** 2
            )

        # Скорость (численное дифференцирование координат)
        if 'time_s' in df.columns and all(col in df.columns for col in ['latitude', 'longitude']):
            # Приблизительное вычисление скорости
            lat_diff = df['latitude'].diff()
            lon_diff = df['longitude'].diff()
            time_diff = df['time_s'].diff()

            # Преобразуем градусы в метры (приблизительно)
            lat_m = lat_diff * 111320  # метров на градус широты
            lon_m = lon_diff * 111320 * np.cos(np.radians(df['latitude']))

            speed_ms = np.sqrt(lat_m ** 2 + lon_m ** 2) / time_diff
            df['speed'] = speed_ms.fillna(0)

        # Температура батареи (примерно)
        if 'temp_cC' in df.columns:
            df['temperature'] = df['temp_cC']
            # Имитируем напряжение батареи на основе температуры
            df['battery_voltage'] = 7.4 - (df['temperature'] - 20) * 0.01

        # RSSI (имитируем на основе флагов)
        if 'flag_telemetry_active' in df.columns:
            df['rssi'] = np.where(df['flag_telemetry_active'], -60, -100)
        else:
            df['rssi'] = -70  # значение по умолчанию

        # Roll, pitch, yaw из акселерометра и магнитометра (упрощенно)
        if all(col in df.columns for col in ['accel_x', 'accel_y', 'accel_z']):
            # Roll (крен)
            df['roll'] = np.degrees(np.arctan2(df['accel_y'], df['accel_z']))

            # Pitch (тангаж)
            accel_total_xy = np.sqrt(df['accel_x'] ** 2 + df['accel_y'] ** 2)
            df['pitch'] = np.degrees(np.arctan2(-df['accel_x'], accel_total_xy))

            # Yaw из магнитометра (упрощенно)
            if all(col in df.columns for col in ['mag_x', 'mag_y']):
                df['yaw'] = np.degrees(np.arctan2(df['mag_y'], df['mag_x']))
            else:
                df['yaw'] = 0

    def get_packet_info(self, filename: str) -> Dict[str, Any]:
        """Получение информации о файле телеметрии"""
        try:
            file_size = os.path.getsize(filename)
            total_packets = file_size // self.PACKET_SIZE

            info = {
                'filename': os.path.basename(filename),
                'file_size': file_size,
                'total_packets': total_packets,
                'packet_size': self.PACKET_SIZE,
                'duration_estimate': f"{total_packets * 0.1:.1f} сек" if total_packets > 0 else "N/A",
                'valid': file_size % self.PACKET_SIZE == 0
            }

            return info

        except Exception as e:
            return {'error': str(e)}

    def export_to_csv(self, df: pd.DataFrame, filename: str):
        """Экспорт DataFrame в CSV"""
        try:
            df.to_csv(filename, index=False, float_format='%.6f')
            return True
        except Exception as e:
            raise Exception(f"Ошибка экспорта в CSV: {e}")

    @staticmethod
    def create_test_file(filename: str, num_packets: int = 1000):
        """Создание тестового файла телеметрии"""
        import random
        import math

        with open(filename, 'wb') as f:
            for i in range(num_packets):
                # Создаем тестовый пакет
                packet_data = bytearray(34)

                # time_ms (24-bit)
                time_ms = i * 100  # 100 мс между пакетами
                packet_data[0] = time_ms & 0xFF
                packet_data[1] = (time_ms >> 8) & 0xFF
                packet_data[2] = (time_ms >> 16) & 0xFF

                # temp_cC (14-bit) - 25°C
                temp = int(25 * 100)
                packet_data[3] = temp & 0xFF
                packet_data[4] = (packet_data[4] & 0xC0) | ((temp >> 8) & 0x3F)

                # pressPa (20-bit) - 101325 Па
                press = 101325
                packet_data[4] = (packet_data[4] & 0x3F) | ((press & 0x03) << 6)
                packet_data[5] = (press >> 2) & 0xFF
                packet_data[6] = (packet_data[6] & 0xF0) | ((press >> 10) & 0x0F)

                # mag, accel, gyro (симуляция)
                offset = 7
                for j in range(9):  # 3 по 3 значения
                    if j < 3:  # mag
                        val = int(random.uniform(-500, 500))
                    elif j < 6:  # accel
                        val = int(random.uniform(-2000, 2000))
                    else:  # gyro
                        val = int(random.uniform(-180, 180) * 10)

                    packet_data[offset + j * 2] = val & 0xFF
                    packet_data[offset + j * 2 + 1] = (val >> 8) & 0xFF

                # lat/lon (Москва, примерно)
                lat = int(55.7558 * 1e7)
                lon = int(37.6176 * 1e7)

                struct.pack_into('<I', packet_data, 25, lat & 0x3FFFFFFF)
                struct.pack_into('<I', packet_data, 29, lon & 0x3FFFFFFF)

                # flags
                packet_data[33] = 0x43  # GPS_FIX | DATA_LOGGING | ARMED

                f.write(packet_data)


# Пример использования
if __name__ == "__main__":
    parser = TelemetryParser()

    # Создаем тестовый файл
    test_file = "test_telemetry.bin"
    parser.create_test_file(test_file, 500)
    print(f"Создан тестовый файл: {test_file}")

    # Получаем информацию о файле
    info = parser.get_packet_info(test_file)
    print("Информация о файле:", info)

    # Парсим файл
    df = parser.parse_file(test_file)
    print(f"\nЗагружено {len(df)} пакетов")
    print("\nКолонки данных:")
    for col in df.columns:
        print(f"  {col}")

    # Показываем первые несколько строк
    print("\nПервые 5 записей:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.head())

    # Экспортируем в CSV
    csv_file = "parsed_telemetry.csv"
    parser.export_to_csv(df, csv_file)
    print(f"\nДанные экспортированы в: {csv_file}")