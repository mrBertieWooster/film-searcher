from flask import Flask, render_template, request, send_from_directory
import os  # Импортируем основной модуль os
from os import path as os_path  # Импортируем os.path как os_path
import configparser

app = Flask(__name__)

# Загрузка конфигурации
config = configparser.ConfigParser()
config.read('config.ini')
disks = config['DEFAULT']['Disks'].split(',')
allowed_extensions = config['DEFAULT']['AllowedExtensions'].split(',')

# Функция для проверки расширения файла
def is_allowed_file(file_name):
    return any(file_name.lower().endswith(ext) for ext in allowed_extensions)

@app.route('/')
def index():
    return render_template('index.html', disks=disks)

@app.route('/browse/<path:file_path>', methods=['GET', 'POST'])
def browse(file_path='C:\\'):
    full_path = os_path.abspath(file_path)
    
    # Проверяем, что запрошенный путь находится на разрешённых дисках
    if not any(full_path.startswith(disk.strip()) for disk in disks):
        return "Access denied", 403
    
    try:
        items = os.listdir(full_path)
    except PermissionError:
        return "Permission denied", 403
    except FileNotFoundError:
        return "Directory not found", 404
    
    # Разделяем файлы и папки
    folders = [item for item in items if os_path.isdir(os_path.join(full_path, item))]
    files = [item for item in items if os_path.isfile(os_path.join(full_path, item)) and is_allowed_file(item)]
    
    # Формируем ссылку на родительскую директорию
    parent_dir = os_path.dirname(full_path) if full_path != file_path else None
    
    # Передаём os_path.join в шаблон
    return render_template('browse.html', 
                           path=full_path, 
                           folders=folders, 
                           files=files, 
                           parent_dir=parent_dir,
                           join=os_path.join)

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
        for root, dirs, files in os.walk(disk):  # Используем os.walk
            for file in files:
                if query.lower() in file.lower():
                    results.append(os_path.join(root, file))
    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)