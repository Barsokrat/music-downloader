#!/usr/bin/env python3
"""
Translations / i18n
Поддержка нескольких языков: English, Español, Français
"""

TRANSLATIONS = {
    'en': {
        # Window
        'window_title': 'Music Downloader',
        'app_title': '🎵 Music Downloader',
        'app_subtitle': 'Download music from public Spotify playlists',

        # URL Section
        'url_group_title': '🔗 Spotify Playlist URL',
        'url_placeholder': 'Paste a public playlist link (e.g., https://open.spotify.com/playlist/...)',
        'btn_paste': 'Paste',
        'url_example': '💡 Example: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
        'url_valid': '✅ Valid playlist link! Click "Download"',
        'url_invalid': 'Paste a valid playlist URL above',

        # Settings
        'settings_group_title': '⚡ Download Settings',
        'output_folder_label': 'Output folder:',
        'btn_browse': 'Browse',
        'normalize_checkbox': '♪ Volume normalization (equalize audio levels)',

        # Progress
        'progress_group_title': '▶ Progress',
        'status_ready': 'Ready to download',
        'status_parsing': 'Parsing playlist...',
        'status_downloading': 'Downloaded {current} of {total} tracks',
        'status_done': '✅ Done!',

        # Log
        'log_group_title': '✎ Operation Log',

        # Buttons
        'btn_download': 'Download Playlist',
        'btn_cancel': 'Stop',

        # Messages
        'error_title': 'Error',
        'error_no_url': 'Please paste a valid playlist URL',
        'error_no_folder': 'Please select an output folder',
        'error_parse_failed': 'Failed to parse playlist',
        'success_title': 'Success!',
        'success_message': '{message}\n\nFolder: {folder}',

        # Log messages
        'log_starting_parse': 'Starting Spotify playlist parsing...',
        'log_opening_playlist': 'Opening playlist: {url}',
        'log_loading_page': 'Loading page...',
        'log_playlist_name': 'Playlist: {name}',
        'log_loading_tracks': 'Loading all tracks...',
        'log_tracks_loaded': 'Loaded tracks: {count}...',
        'log_recommended_found': 'Found "Recommended" section, stopping',
        'log_all_tracks_loaded': 'All tracks loaded: {count}',
        'log_parsing_tracks': 'Parsing {count} tracks...',
        'log_processed_tracks': 'Processed {count} tracks...',
        'log_tracks_found': 'Tracks found: {count}',
        'log_parse_error': 'Parsing error: {error}',
        'log_parse_failed': 'Failed to parse playlist',
        'log_playlist_recognized': 'Playlist recognized: {name}',
        'log_tracks_to_download': 'Tracks to download: {count}',
        'log_found_tracks': 'Found {count} tracks. Starting download...',
        'log_starting_download': 'Starting download of {count} tracks',
        'log_saving_to': 'Saving to: {folder}',
        'log_download_error': 'Error: {error}',
        'log_stopping_parse': 'Stopping parsing...',
        'log_stopping_download': 'Stopping download...',

        # Language selector
        'language': 'Language:',
    },

    'es': {
        # Window
        'window_title': 'Descargador de Música',
        'app_title': 'Descargador de Música',
        'app_subtitle': 'Descarga música de listas públicas de Spotify',

        # URL Section
        'url_group_title': 'URL de Lista de Spotify',
        'url_placeholder': 'Pega un enlace de lista pública (ej: https://open.spotify.com/playlist/...)',
        'btn_paste': 'Pegar',
        'url_example': 'Ejemplo: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
        'url_valid': '¡Enlace válido! Haz clic en "Descargar"',
        'url_invalid': 'Pega una URL de lista válida arriba',

        # Settings
        'settings_group_title': 'Configuración de Descarga',
        'output_folder_label': 'Carpeta de salida:',
        'btn_browse': 'Examinar',
        'normalize_checkbox': 'Normalización de volumen (igualar niveles de audio)',

        # Progress
        'progress_group_title': 'Progreso',
        'status_ready': 'Listo para descargar',
        'status_parsing': 'Analizando lista...',
        'status_downloading': 'Descargadas {current} de {total} pistas',
        'status_done': '¡Completado!',

        # Log
        'log_group_title': 'Registro de Operaciones',

        # Buttons
        'btn_download': 'Descargar Lista',
        'btn_cancel': 'Detener',

        # Messages
        'error_title': 'Error',
        'error_no_url': 'Por favor pega una URL de lista válida',
        'error_no_folder': 'Por favor selecciona una carpeta de salida',
        'error_parse_failed': 'No se pudo analizar la lista',
        'success_title': '¡Éxito!',
        'success_message': '{message}\n\nCarpeta: {folder}',

        # Log messages
        'log_starting_parse': 'Iniciando análisis de lista de Spotify...',
        'log_opening_playlist': 'Abriendo lista: {url}',
        'log_loading_page': 'Cargando página...',
        'log_playlist_name': 'Lista: {name}',
        'log_loading_tracks': 'Cargando todas las pistas...',
        'log_tracks_loaded': 'Pistas cargadas: {count}...',
        'log_recommended_found': 'Encontrada sección "Recomendadas", deteniendo',
        'log_all_tracks_loaded': 'Todas las pistas cargadas: {count}',
        'log_parsing_tracks': 'Analizando {count} pistas...',
        'log_processed_tracks': 'Procesadas {count} pistas...',
        'log_tracks_found': 'Pistas encontradas: {count}',
        'log_parse_error': 'Error de análisis: {error}',
        'log_parse_failed': 'No se pudo analizar la lista',
        'log_playlist_recognized': 'Lista reconocida: {name}',
        'log_tracks_to_download': 'Pistas para descargar: {count}',
        'log_found_tracks': '{count} pistas encontradas. Iniciando descarga...',
        'log_starting_download': 'Iniciando descarga de {count} pistas',
        'log_saving_to': 'Guardando en: {folder}',
        'log_download_error': 'Error: {error}',
        'log_stopping_parse': 'Deteniendo análisis...',
        'log_stopping_download': 'Deteniendo descarga...',

        # Language selector
        'language': 'Idioma:',
    },

    'fr': {
        # Window
        'window_title': 'Téléchargeur de Musique',
        'app_title': 'Téléchargeur de Musique',
        'app_subtitle': 'Téléchargez de la musique depuis les playlists publiques Spotify',

        # URL Section
        'url_group_title': 'URL de Playlist Spotify',
        'url_placeholder': 'Collez un lien de playlist publique (ex: https://open.spotify.com/playlist/...)',
        'btn_paste': 'Coller',
        'url_example': 'Exemple: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
        'url_valid': 'Lien valide! Cliquez sur "Télécharger"',
        'url_invalid': 'Collez une URL de playlist valide ci-dessus',

        # Settings
        'settings_group_title': 'Paramètres de Téléchargement',
        'output_folder_label': 'Dossier de sortie:',
        'btn_browse': 'Parcourir',
        'normalize_checkbox': 'Normalisation du volume (égaliser les niveaux audio)',

        # Progress
        'progress_group_title': 'Progression',
        'status_ready': 'Prêt à télécharger',
        'status_parsing': 'Analyse de la playlist...',
        'status_downloading': 'Téléchargé {current} sur {total} pistes',
        'status_done': 'Terminé!',

        # Log
        'log_group_title': 'Journal des Opérations',

        # Buttons
        'btn_download': 'Télécharger la Playlist',
        'btn_cancel': 'Arrêter',

        # Messages
        'error_title': 'Erreur',
        'error_no_url': 'Veuillez coller une URL de playlist valide',
        'error_no_folder': 'Veuillez sélectionner un dossier de sortie',
        'error_parse_failed': 'Échec de l\'analyse de la playlist',
        'success_title': 'Succès!',
        'success_message': '{message}\n\nDossier: {folder}',

        # Log messages
        'log_starting_parse': 'Démarrage de l\'analyse de la playlist Spotify...',
        'log_opening_playlist': 'Ouverture de la playlist: {url}',
        'log_loading_page': 'Chargement de la page...',
        'log_playlist_name': 'Playlist: {name}',
        'log_loading_tracks': 'Chargement de toutes les pistes...',
        'log_tracks_loaded': 'Pistes chargées: {count}...',
        'log_recommended_found': 'Section "Recommandées" trouvée, arrêt',
        'log_all_tracks_loaded': 'Toutes les pistes chargées: {count}',
        'log_parsing_tracks': 'Analyse de {count} pistes...',
        'log_processed_tracks': '{count} pistes traitées...',
        'log_tracks_found': 'Pistes trouvées: {count}',
        'log_parse_error': 'Erreur d\'analyse: {error}',
        'log_parse_failed': 'Échec de l\'analyse de la playlist',
        'log_playlist_recognized': 'Playlist reconnue: {name}',
        'log_tracks_to_download': 'Pistes à télécharger: {count}',
        'log_found_tracks': '{count} pistes trouvées. Démarrage du téléchargement...',
        'log_starting_download': 'Démarrage du téléchargement de {count} pistes',
        'log_saving_to': 'Sauvegarde dans: {folder}',
        'log_download_error': 'Erreur: {error}',
        'log_stopping_parse': 'Arrêt de l\'analyse...',
        'log_stopping_download': 'Arrêt du téléchargement...',

        # Language selector
        'language': 'Langue:',
    }
}


def get_translation(lang_code, key, **kwargs):
    """
    Получить перевод по ключу

    Args:
        lang_code: код языка ('en', 'es', 'fr')
        key: ключ перевода
        **kwargs: параметры для форматирования строки

    Returns:
        Переведенная строка
    """
    # Fallback на английский если язык не найден
    if lang_code not in TRANSLATIONS:
        lang_code = 'en'

    translation = TRANSLATIONS[lang_code].get(key, TRANSLATIONS['en'].get(key, key))

    # Форматирование если есть параметры
    if kwargs:
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError):
            return translation

    return translation


class Translator:
    """Класс для удобной работы с переводами"""

    def __init__(self, lang_code='en'):
        self.lang_code = lang_code

    def tr(self, key, **kwargs):
        """Сокращенный метод для получения перевода"""
        return get_translation(self.lang_code, key, **kwargs)

    def set_language(self, lang_code):
        """Сменить язык"""
        if lang_code in TRANSLATIONS:
            self.lang_code = lang_code
            return True
        return False

    def get_available_languages(self):
        """Получить список доступных языков"""
        return {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français'
        }
