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
    drive, tail = os_path.splitdrive(full_path)  # Разделяем путь на диск и оставшуюся часть
    if tail == os_path.sep:  # Если оставшаяся часть — только разделитель (например, '\'), это корень диска
        parent_dir = None
    else:
        parent_dir = os_path.dirname(full_path)
        
    print(f"Full path: {full_path}, Parent dir: {parent_dir}")
    
    # Генерация хлебных крошек
    breadcrumbs = []
    path_parts = full_path.split(os_path.sep)
    cumulative_path = ""
    for part in path_parts:
        if part:
            cumulative_path = os_path.join(cumulative_path, part)
            breadcrumbs.append({'name': part, 'path': cumulative_path})
    
    # Обработка POST-запроса для создания плейлиста
    if request.method == 'POST':
        selected_files = request.form.getlist('files')
        playlist_content = '\n'.join([os_path.join(full_path, f) for f in selected_files])
        
        # Сохраняем плейлист
        with open('playlist.m3u', 'w') as f:
            f.write(playlist_content)
        
        # Возвращаем файл плейлиста для скачивания
        return send_from_directory('.', 'playlist.m3u', as_attachment=True)
    
    # Передаём os_path.join в шаблон
    return render_template('browse.html', 
                           path=full_path, 
                           folders=folders, 
                           files=files, 
                           parent_dir=parent_dir,
                           join=os_path.join,
                           breadcrumbs=breadcrumbs)

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
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('search.html', results=[], query=query)
    
    results = []
    for disk in disks:
        for root, dirs, files in os.walk(disk.strip()):
            for file in files:
                if query.lower() in file.lower() and is_allowed_file(file):
                    results.append(os_path.join(root, file))
    
    return render_template('search.html', results=results, query=query)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)