#!/usr/bin/env python3
"""
Music Downloader from CSV
Скачивает музыку с YouTube по списку из CSV файла
"""

import csv
import subprocess
import os
import re
import json
from pathlib import Path
import sys

def clean_filename(text, max_length=40):
    """Убирает скобки и лишние пробелы из названия, обрезает до max_length"""
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    # Убираем слеши и другие недопустимые символы для файловой системы
    text = re.sub(r'[/\\:*?"<>|]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Обрезаем до максимальной длины
    if len(text) > max_length:
        text = text[:max_length].strip()
        # Убираем обрезанное слово в конце
        if ' ' in text:
            text = text.rsplit(' ', 1)[0]

    # Убираем лишние символы в конце (запятые, дефисы)
    text = text.rstrip(',-–— ').strip()

    return text

def extract_playlist_name(csv_path):
    """Извлекает название плейлиста из первой строки CSV"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            # Проверяем формат: # Playlist: Name
            if first_line.startswith('# Playlist:'):
                playlist_name = first_line.replace('# Playlist:', '').strip()
                return playlist_name
    except:
        pass
    return None

def find_suitable_video(search_query, max_duration=420, max_results=5):
    """
    Ищет подходящее видео на YouTube с ограничением по длительности

    Args:
        search_query: поисковый запрос
        max_duration: максимальная длительность в секундах (по умолчанию 420 = 7 минут)
        max_results: сколько результатов проверить

    Returns:
        URL подходящего видео или None
    """
    try:
        # Получаем топ-N результатов поиска с метаданными
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--skip-download',
            '--quiet',
            '--no-warnings',
            f'ytsearch{max_results}:{search_query}'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Собираем подходящие видео
        suitable_videos = []

        # yt-dlp возвращает по одному JSON на строку
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            video_info = json.loads(line)
            duration = video_info.get('duration', 0)
            title = video_info.get('title', 'Unknown')
            url = video_info.get('webpage_url', '')
            uploader = (video_info.get('uploader') or video_info.get('channel') or '').lower()

            # Проверяем длительность
            if duration and duration <= max_duration:
                suitable_videos.append({
                    'url': url,
                    'title': title,
                    'duration': duration,
                    'uploader': uploader
                })
            else:
                print(f"   ⏩ Пропускаем (слишком длинное {duration}s): {title}")

        if not suitable_videos:
            print(f"   ⚠️  Не найдено видео короче {max_duration}s")
            return None

        # Извлекаем имя артиста из запроса (первое слово/слова до названия песни)
        # Простая эвристика: берём первую часть запроса
        artist_keywords = search_query.lower().split()[:3]  # Первые 3 слова как ключевые

        # Простая транслитерация для кириллицы
        translit_map = {
            'a': 'а', 'b': 'б', 'c': 'с', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
            'h': 'х', 'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н',
            'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'v': 'в',
            'w': 'в', 'x': 'кс', 'y': 'й', 'z': 'з'
        }

        def transliterate(text):
            """Простая транслитерация латиницы в кириллицу"""
            return ''.join(translit_map.get(c, c) for c in text.lower())

        # Приоритизация:
        # 1. Ищем видео с официального канала артиста (канал содержит имя артиста)
        official_channel_videos = []
        for video in suitable_videos:
            uploader_lower = video['uploader']
            # Проверяем совпадение с учётом транслитерации
            matched = False
            for keyword in artist_keywords:
                if len(keyword) <= 3:
                    continue
                # Проверяем прямое совпадение или транслитерированное
                if keyword in uploader_lower or transliterate(keyword) in uploader_lower:
                    matched = True
                    break

            if matched:
                # Дополнительно избегаем live версий
                if 'live' not in video['title'].lower() or 'official' in video['title'].lower():
                    official_channel_videos.append(video)

        # Если нашли видео с официального канала, выбираем самое короткое (обычно студийная версия)
        if official_channel_videos:
            shortest = min(official_channel_videos, key=lambda v: v['duration'])
            print(f"   ✓ Выбрано (официальный канал, самое короткое): {shortest['title']} ({shortest['duration']}s)")
            print(f"      Канал: {shortest['uploader']}")
            return shortest['url']

        # 2. Ищем "official audio" или просто "audio" (приоритет выше чем video)
        for priority_keyword in ['official audio', 'audio']:
            for video in suitable_videos:
                title_lower = video['title'].lower()
                if priority_keyword in title_lower and 'live' not in title_lower:
                    print(f"   ✓ Выбрано: {video['title']} ({video['duration']}s)")
                    return video['url']

        # 3. Ищем "official video" или "official" (но только если нет audio версии)
        for priority_keyword in ['official video', 'official']:
            for video in suitable_videos:
                title_lower = video['title'].lower()
                if priority_keyword in title_lower and 'live' not in title_lower:
                    print(f"   ✓ Выбрано: {video['title']} ({video['duration']}s)")
                    return video['url']

        # 3. Если не нашли с приоритетными словами, берём первое подходящее
        video = suitable_videos[0]
        print(f"   ✓ Выбрано первое подходящее: {video['title']} ({video['duration']}s)")
        return video['url']

    except Exception as e:
        print(f"   ⚠️  Ошибка поиска: {e}")
        return None

def download_from_csv(csv_path, output_dir):
    """
    Скачивает музыку из CSV файла

    CSV должен содержать колонки:
    - №: номер трека
    - Песня: название песни
    - Артист: исполнитель
    - Альбом: (опционально)
    """

    # Создаём директорию если не существует
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Читаем CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Пропускаем первую строку если это метаданные плейлиста
        first_line = f.readline()
        if not first_line.startswith('# Playlist:'):
            # Если не метаданные, возвращаемся в начало
            f.seek(0)

        reader = csv.DictReader(f)
        songs = list(reader)

    print(f"📀 Найдено {len(songs)} треков для скачивания\n")

    # Скачиваем каждый трек
    for song in songs:
        num = song.get('№', '').zfill(2)
        track_name = song['Песня']
        artist = song['Артист']

        # Очищаем названия
        clean_artist = clean_filename(artist, max_length=100)  # Без ограничения пока
        clean_track = clean_filename(track_name, max_length=100)

        # Формируем название файла
        base_filename = f"{num}. {clean_artist} - {clean_track}"

        # Ограничиваем общую длину названия (без .mp3)
        max_base_length = 40
        if len(base_filename) > max_base_length:
            # Обрезаем, оставляя место для номера и разделителей
            # Формат: "01. Artist - Track"
            prefix_len = len(f"{num}. ")  # "01. " = 4 символа
            available = max_base_length - prefix_len

            # Делим доступное место 50/50 между артистом и треком
            artist_max = available // 2 - 3  # -3 для " - "
            track_max = available - artist_max - 3

            clean_artist = clean_filename(artist, max_length=artist_max)
            clean_track = clean_filename(track_name, max_length=track_max)

            base_filename = f"{num}. {clean_artist} - {clean_track}"

        output_filename = f"{base_filename}.mp3"
        search_query = f"{artist} {track_name}"
        output_path = Path(output_dir) / output_filename

        # Пропускаем если уже скачан
        if output_path.exists():
            print(f"⏭️  [{num}] Уже скачан: {clean_artist} - {clean_track}")
            continue

        print(f"⬇️  [{num}] Скачиваю: {clean_artist} - {clean_track}")

        try:
            # Ищем подходящее видео (не длиннее 7 минут)
            video_url = find_suitable_video(search_query, max_duration=420, max_results=5)

            # Формируем команду скачивания
            if video_url:
                # Скачиваем конкретное видео
                download_target = video_url
            else:
                # Fallback: используем первый результат поиска
                download_target = f'ytsearch1:{search_query}'

            cmd = [
                'yt-dlp',
                '-x',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', str(output_path),
                '--add-metadata',
                '--embed-thumbnail',
                '--quiet',
                '--no-warnings',
                download_target
            ]

            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ [{num}] Готово: {clean_artist} - {clean_track}\n")

        except subprocess.CalledProcessError as e:
            print(f"❌ [{num}] Ошибка: {clean_artist} - {clean_track}")
            if e.stderr:
                print(f"   {e.stderr}\n")
            continue
        except Exception as e:
            print(f"❌ [{num}] Ошибка: {e}\n")
            continue

    print(f"\n🎵 Все треки скачаны в: {output_dir}")

def main():
    """Главная функция"""

    # Проверяем аргументы
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python3 {sys.argv[0]} <путь_к_csv> [папка_для_сохранения]")
        print("\nПример:")
        print(f"  python3 {sys.argv[0]} ~/Downloads/songs.csv ~/Music/MyPlaylist")
        print("\nCSV файл должен содержать колонки: №, Песня, Артист")
        sys.exit(1)

    csv_path = sys.argv[1]

    # Проверяем существование CSV
    if not Path(csv_path).exists():
        print(f"❌ Файл не найден: {csv_path}")
        sys.exit(1)

    # Извлекаем название плейлиста из CSV
    playlist_name = extract_playlist_name(csv_path)

    # Папка для сохранения
    if len(sys.argv) > 2:
        # Если указана явно
        output_dir = sys.argv[2]
    elif playlist_name:
        # Используем название плейлиста
        safe_name = re.sub(r'[^\w\s-]', '', playlist_name).strip().replace(' ', '_')
        output_dir = str(Path(csv_path).parent / safe_name)
        print(f"📀 Плейлист: {playlist_name}")
    else:
        # По умолчанию
        output_dir = str(Path(csv_path).parent / "Downloaded_Music")

    print(f"📂 CSV файл: {csv_path}")
    print(f"📁 Папка для сохранения: {output_dir}\n")

    # Запускаем скачивание
    download_from_csv(csv_path, output_dir)

if __name__ == "__main__":
    main()
