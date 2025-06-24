#lytes.py
import sys, os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSlider,
    QInputDialog, QTreeWidget, QTreeWidgetItem, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

#mwamburi
# genres to choose from
GENRES = ["Pop", "Hip Hop", "Afrobeat", "Amapiano", "Reggae", "Jazz", "Gospel", "RnB"]

# music dictionary to hold songs organized by genre and artist                    
music_library = {g: {} for g in GENRES}

# This keeps track of the currently selected song
current = {"genre": None, "artist": None, "song": None, "idx": None}
is_playing = False  # True if a song is playing

def update_tree(tree):
    # Show all songs in the library in the tree view
    tree.clear()
    for genre, artists in music_library.items():
        for artist, songs in artists.items():
            for song in songs:
                item = QTreeWidgetItem([song["title"], artist, genre])
                item.setData(0, Qt.ItemDataRole.UserRole, (genre, artist, song["path"]))
                tree.addTopLevelItem(item)

def update_now_playing(now_playing):
    # Update the label to show which song is playing
    if current["song"]:
        now_playing.setText(f"Playing: {current['song']} by {current['artist']} ({current['genre']})")
    else:
        now_playing.setText("No song selected")

def play_song(media_player, play_btn, now_playing, genre, artist, idx):
    # Play the selected song 
    global is_playing
    song = music_library[genre][artist][idx]
    current.update({"genre": genre, "artist": artist, "song": song["title"], "idx": idx})
    media_player.setSource(QUrl.fromLocalFile(song["path"]))
    media_player.play()
    is_playing = True
    play_btn.setIcon(QIcon.fromTheme("media-playback-pause"))
    update_now_playing(now_playing)

def toggle_play(media_player, play_btn, now_playing):
    # Play or pause the current song
    global is_playing
    if not current["song"]:
        # If nothing is selected, play the first song in the library
        for genre in GENRES:
            for artist in music_library[genre]:
                if music_library[genre][artist]:
                    play_song(media_player, play_btn, now_playing, genre, artist, 0)
                    return
        return
    if is_playing:
        media_player.pause()
        is_playing = False
        play_btn.setIcon(QIcon.fromTheme("media-playback-start"))
    else:
        media_player.play()
        is_playing = True
        play_btn.setIcon(QIcon.fromTheme("media-playback-pause"))

def stop(media_player, play_btn, now_playing):
    # Stop the music
    global is_playing
    media_player.stop()
    is_playing = False
    play_btn.setIcon(QIcon.fromTheme("media-playback-start"))
    update_now_playing(now_playing)

def prev_song(media_player, play_btn, now_playing):
    # Play the previous song in the list
    g, a, idx = current.get("genre"), current.get("artist"), current.get("idx", 0)
    if g and a and idx > 0:
        play_song(media_player, play_btn, now_playing, g, a, idx - 1)

def next_song(media_player, play_btn, now_playing):
    # Play the next song in the list
    g, a, idx = current.get("genre"), current.get("artist"), current.get("idx", 0)
    if g and a and idx is not None and idx < len(music_library[g][a]) - 1:
        play_song(media_player, play_btn, now_playing, g, a, idx + 1)

def import_file(win, tree):
    # Ask the user to pick a music file, artist, and genre, then add it to the library
    file_path, _ = QFileDialog.getOpenFileName(win, "Select Music File", "", "Audio Files (*.mp3 *.wav *.ogg)")
    if not file_path: return
    artist, ok = QInputDialog.getText(win, "Artist Name", "Enter artist name:")
    if not ok or not artist.strip(): return
    genre, ok = QInputDialog.getItem(win, "Genre", "Select genre:", GENRES, 0, False)
    if not ok or not genre.strip(): return
    title = os.path.basename(file_path)
    if artist not in music_library[genre]:
        music_library[genre][artist] = []
    music_library[genre][artist].append({"title": title, "path": file_path})
    update_tree(tree)

def set_volume(audio_output, val):
    # Change the playback volume
    audio_output.setVolume(val / 100)

def on_tree_double_clicked(media_player, play_btn, now_playing, item, _):
    # Play a song when the user double-clicks it in the library
    data = item.data(0, Qt.ItemDataRole.UserRole)
    if data:
        genre, artist, path = data
        idx = next((i for i, s in enumerate(music_library[genre][artist]) if s["path"] == path), 0)
        play_song(media_player, play_btn, now_playing, genre, artist, idx)

def search(tree, search_results, query):
    # Search for songs, artists, or genres and show the results
    query = query.strip().lower()
    if not query:
        search_results.hide()
        tree.show()
        return
    search_results.clear()
    for genre, artists in music_library.items():
        for artist, songs in artists.items():
            for song in songs:
                if (query in song["title"].lower() or
                    query in artist.lower() or
                    query in genre.lower()):
                    item = QTreeWidgetItem([song["title"], artist, genre])
                    item.setData(0, Qt.ItemDataRole.UserRole, (genre, artist, song["path"]))
                    search_results.addTopLevelItem(item)
    tree.hide()
    search_results.show()

def on_search_result_double_clicked(media_player, play_btn, now_playing, item, _):
    # Play a song when the user double-clicks it in the search results
    on_tree_double_clicked(media_player, play_btn, now_playing, item, None)

def main():
    global is_playing
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Lytes Music Library")
    win.setGeometry(100, 100, 800, 500)
    cw = QWidget()
    win.setCentralWidget(cw)
    layout = QVBoxLayout(cw)

    # Search bar at the top
    search_layout = QHBoxLayout()
    search_input = QLineEdit()
    search_input.setPlaceholderText("Search song, artist, or genre...")
    search_btn = QPushButton("Search")
    search_layout.addWidget(search_input)
    search_layout.addWidget(search_btn)
    layout.addLayout(search_layout)

    # Song library tree view
    tree = QTreeWidget()
    tree.setHeaderLabels(["Song", "Artist", "Genre"])
    layout.addWidget(tree)

    # Search results
    search_results = QTreeWidget()
    search_results.setHeaderLabels(["Song", "Artist", "Genre"])
    layout.addWidget(search_results)
    search_results.hide()

    # Label to show the currently playing song
    now_playing = QLabel("No song selected")
    layout.addWidget(now_playing)

    # Controls
    controls = QHBoxLayout()
    play_btn = QPushButton()
    play_btn.setIcon(QIcon.fromTheme("media-playback-start"))
    stop_btn = QPushButton()
    stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
    prev_btn = QPushButton()
    prev_btn.setIcon(QIcon.fromTheme("media-skip-backward"))
    next_btn = QPushButton()
    next_btn.setIcon(QIcon.fromTheme("media-skip-forward"))
    import_btn = QPushButton("Import File")
    controls.addWidget(prev_btn)
    controls.addWidget(play_btn)
    controls.addWidget(stop_btn)
    controls.addWidget(next_btn)
    controls.addWidget(import_btn)
    layout.addLayout(controls)

    # Volume
    vol_layout = QHBoxLayout()
    vol_label = QLabel("Volume:")
    vol_slider = QSlider(Qt.Orientation.Horizontal)
    vol_slider.setRange(0, 100)
    vol_slider.setValue(40)
    vol_layout.addWidget(vol_label)
    vol_layout.addWidget(vol_slider)
    layout.addLayout(vol_layout)

    # Set up the media player and audio output
    media_player = QMediaPlayer()
    audio_output = QAudioOutput()
    media_player.setAudioOutput(audio_output)
    audio_output.setVolume(0.4)

    # Connect buttons and widgets to their functions
    play_btn.clicked.connect(lambda: toggle_play(media_player, play_btn, now_playing))
    stop_btn.clicked.connect(lambda: stop(media_player, play_btn, now_playing))
    prev_btn.clicked.connect(lambda: prev_song(media_player, play_btn, now_playing))
    next_btn.clicked.connect(lambda: next_song(media_player, play_btn, now_playing))
    import_btn.clicked.connect(lambda: import_file(win, tree))
    vol_slider.valueChanged.connect(lambda val: set_volume(audio_output, val))
    tree.itemDoubleClicked.connect(lambda item, col: on_tree_double_clicked(media_player, play_btn, now_playing, item, col))
    search_btn.clicked.connect(lambda: search(tree, search_results, search_input.text()))
    search_input.returnPressed.connect(lambda: search(tree, search_results, search_input.text()))
    search_results.itemDoubleClicked.connect(lambda item, col: on_search_result_double_clicked(media_player, play_btn, now_playing, item, col))

    # Show the library when the app starts
    update_tree(tree)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

