#!/usr/bin/env python3
"""
Spotify Playlist Parser
Парсит публичный плейлист Spotify и создаёт CSV для скачивания
"""

import csv
import sys
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

def parse_spotify_playlist(playlist_url, output_csv=None):
    """
    Парсит Spotify плейлист через HTML и сохраняет в CSV

    Args:
        playlist_url: URL плейлиста Spotify
        output_csv: Путь для сохранения CSV (опционально)
    """

    print(f"🔍 Открываю плейлист: {playlist_url}")

    with sync_playwright() as p:
        # Запускаем браузер (headless для скорости)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Устанавливаем viewport побольше чтобы влезло больше треков
        page.set_viewport_size({"width": 1920, "height": 5000})

        # Открываем страницу плейлиста
        page.goto(playlist_url, wait_until='domcontentloaded')

        # Ждём загрузки первых треков
        page.wait_for_selector('[data-testid="tracklist-row"]', timeout=10000)
        time.sleep(3)

        # Получаем название плейлиста (пробуем разные селекторы)
        playlist_name = "playlist"
        try:
            # Пробуем основной h1
            h1_elements = page.locator('h1').all()
            for h1 in h1_elements:
                text = h1.inner_text().strip()
                # Пропускаем системные заголовки
                if text and text != "Your Library" and len(text) > 0:
                    playlist_name = text
                    break
            print(f"📀 Плейлист: {playlist_name}")
        except Exception as e:
            print(f"⚠️  Не удалось получить название: {e}")
            playlist_name = "playlist"

        # Скроллим страницу чтобы загрузить все треки плейлиста
        print("📜 Загружаю все треки плейлиста...")
        previous_count = 0
        no_change_count = 0
        max_scrolls = 100  # Максимум скроллов для защиты от бесконечного цикла

        for scroll_attempt in range(max_scrolls):
            # Получаем текущее количество треков
            current_tracks = page.locator('[data-testid="tracklist-row"]').count()

            if scroll_attempt % 10 == 0:
                print(f"  Загружено треков: {current_tracks}...")

            # Проверяем появилась ли секция Recommended
            has_recommended = page.locator('h2:has-text("Recommended")').count() > 0

            if has_recommended:
                print(f"📌 Обнаружена секция 'Recommended', остановка загрузки")
                break

            # Если треков не прибавилось несколько раз подряд, значит всё загружено
            if current_tracks == previous_count:
                no_change_count += 1
                if no_change_count >= 10:  # 10 попыток без изменений
                    print(f"✓ Загружено всех треков: {current_tracks}")
                    break
            else:
                no_change_count = 0

            previous_count = current_tracks

            # Скроллим вниз агрессивнее
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(0.5)

        # Парсим треки
        songs = []

        # Находим позицию заголовка "Recommended" если он есть
        recommended_y = None
        try:
            recommended_elem = page.locator('h2:has-text("Recommended")').first
            if recommended_elem.count() > 0:
                bbox = recommended_elem.bounding_box()
                if bbox:
                    recommended_y = bbox['y']
                    print(f"📌 Секция 'Recommended' на позиции Y={recommended_y}")
        except:
            pass

        # Получаем все треки
        all_track_rows = page.locator('[data-testid="tracklist-row"]').all()

        print(f"🎵 Парсинг {len(all_track_rows)} треков...")

        # Парсим треки
        last_track_number = 0
        for idx, row in enumerate(all_track_rows):
            try:
                # Если есть секция Recommended, проверяем позицию трека
                if recommended_y is not None:
                    bbox = row.bounding_box()
                    if bbox and bbox['y'] >= recommended_y:
                        # Трек находится ниже заголовка Recommended - пропускаем
                        print(f"  ⏭️  Остановка: достигнута секция Recommended")
                        break

                # Проверяем номер трека в плейлисте
                # В основном плейлисте треки идут с номерами 1, 2, 3...
                # В рекомендациях номеров нет или они не последовательные
                try:
                    # Ищем номер трека в первой колонке
                    track_number_elem = row.locator('[aria-colindex="1"]').first
                    track_number_text = track_number_elem.inner_text().strip()

                    # Пробуем преобразовать в число
                    if track_number_text.isdigit():
                        current_number = int(track_number_text)
                        # Если номер не последовательный (разрыв больше 1), останавливаемся
                        if last_track_number > 0 and current_number != last_track_number + 1:
                            print(f"  ⏭️  Остановка: обнаружен разрыв нумерации ({last_track_number} -> {current_number})")
                            break
                        last_track_number = current_number
                    else:
                        # Нет номера - вероятно рекомендации
                        if len(songs) > 0:  # Если уже что-то нашли, останавливаемся
                            print(f"  ⏭️  Остановка: трек без номера (рекомендации)")
                            break
                except:
                    # Если не удалось получить номер и уже есть треки, останавливаемся
                    if len(songs) > 0:
                        print(f"  ⏭️  Остановка: не удалось получить номер трека")
                        break

                # Название трека
                track_name_elem = row.locator('[data-testid="internal-track-link"]').first
                track_name = track_name_elem.inner_text() if track_name_elem.count() > 0 else ""

                # Артист (может быть несколько)
                artist_links = row.locator('a[href*="/artist/"]').all()
                artists = []
                for artist_link in artist_links:
                    artist_text = artist_link.inner_text()
                    if artist_text and artist_text not in artists:
                        artists.append(artist_text)

                artist_name = ', '.join(artists) if artists else ""

                # Альбом
                album_elem = row.locator('a[href*="/album/"]').first
                album_name = album_elem.inner_text() if album_elem.count() > 0 else ""

                if track_name:
                    songs.append({
                        '№': str(len(songs) + 1),
                        'Песня': track_name,
                        'Артист': artist_name,
                        'Альбом': album_name
                    })
                    print(f"  {len(songs)}. {artist_name} - {track_name}")

            except Exception as e:
                print(f"  ⚠️  Ошибка: {e}")
                if len(songs) > 0:  # Если уже есть треки, останавливаемся при ошибке
                    break
                continue

        browser.close()

    if not songs:
        print("❌ Не удалось извлечь треки")
        return None

    # Определяем путь для сохранения
    if output_csv is None:
        safe_name = re.sub(r'[^\w\s-]', '', playlist_name).strip().replace(' ', '_')
        output_csv = f"Spotify playlist {safe_name}.csv"

    # Сохраняем в CSV с метаданными плейлиста
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        # Первая строка - метаданные (название плейлиста)
        f.write(f"# Playlist: {playlist_name}\n")

        # Записываем треки
        writer = csv.DictWriter(f, fieldnames=['№', 'Песня', 'Артист', 'Альбом'])
        writer.writeheader()
        writer.writerows(songs)

    print(f"\n✅ CSV файл создан: {output_csv}")
    print(f"📊 Сохранено треков: {len(songs)}")
    print(f"📁 Название плейлиста: {playlist_name}")

    return output_csv

def main():
    """Главная функция"""

    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python3 {sys.argv[0]} <spotify_playlist_url> [output.csv]")
        print("\nПример:")
        print(f"  python3 {sys.argv[0]} https://open.spotify.com/playlist/7EFhwhbPhOhKjuwIJseVwT")
        print(f"  python3 {sys.argv[0]} https://open.spotify.com/playlist/ABC123 my_playlist.csv")
        sys.exit(1)

    playlist_url = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None

    # Парсим плейлист
    result = parse_spotify_playlist(playlist_url, output_csv)

    if result:
        print(f"\n🎵 Готово! Теперь можно скачать треки:")
        print(f"   python3 download_music.py {result}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
