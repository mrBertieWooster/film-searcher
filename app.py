# app.py

from flask import Flask, render_template, request, send_from_directory
import os
import configparser

app = Flask(__name__)

# Загрузка конфигурации
config = configparser.ConfigParser()
config.read('config.ini')
disks = config['DEFAULT']['Disks'].split(',')

@app.route('/')
def index():
    directories = []
    for disk in disks:
        if os.path.exists(disk):
            directories.append({'disk': disk, 'folders': os.listdir(disk)})
    return render_template('index.html', directories=directories)

@app.route('/browse/<path:file_path>')
def browse(file_path):
    full_path = os.path.join(file_path)
    if os.path.isdir(full_path):
        files = os.listdir(full_path)
        return render_template('browse.html', files=files, path=file_path)
    else:
        # Если это файл, можно предложить скачать
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    selected_files = request.form.getlist('files')
    playlist_content = '\n'.join(selected_files)
    
    # Сохраняем плейлист
    with open('playlist.m3u', 'w') as f:
        f.write(playlist_content)
    
    return send_from_directory('.', 'playlist.m3u', as_attachment=True)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = []
    for disk in disks:
        for root, dirs, files in os.walk(disk):
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)