from flask import Flask, request, render_template, send_from_directory, render_template_string, redirect, url_for
import yt_dlp
import os
import subprocess
import re
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/downloads/individuales'

DOWNLOAD_FOLDER = 'static/downloads'
INDIVIDUAL_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'individuales')
ACAPELLAS_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'acapellas')
INSTRUMENTALES_FOLDER = os.path.join(DOWNLOAD_FOLDER, 'instrumentales')
COOKIES_FILE = 'cookies.txt'

# Crear carpetas necesarias
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(INDIVIDUAL_FOLDER, exist_ok=True)
os.makedirs(ACAPELLAS_FOLDER, exist_ok=True)
os.makedirs(INSTRUMENTALES_FOLDER, exist_ok=True)

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

if not check_ffmpeg():
    print("FFmpeg no está instalado. Por favor, instalalo y asegurate de que esté en tu PATH.")
    exit(1)

@app.route('/')
def index():
    archivos = [f for f in os.listdir(INDIVIDUAL_FOLDER) if f.endswith('.mp3')]
    return render_template('index.html', archivos=archivos)

@app.route('/single_download', methods=['POST'])
def single_download():
    url = request.form['youtube_url']
    if not url:
        return "URL inválida", 400

    try:
        with yt_dlp.YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(INDIVIDUAL_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{info['title']}.mp3"
            return redirect(url_for('index'))
    except Exception as e:
        return f"Error al descargar: {str(e)}", 500

@app.route('/subir_y_separar', methods=['POST'])
def subir_y_separar():
    if 'archivo' not in request.files:
        return "No se envió archivo", 400

    archivo = request.files['archivo']
    if archivo.filename == '':
        return "Nombre de archivo vacío", 400

    if archivo and archivo.filename.endswith('.mp3'):
        filepath = os.path.join(INDIVIDUAL_FOLDER, archivo.filename)
        archivo.save(filepath)

        try:
            subprocess.run(['demucs', filepath], check=True)
            nombre_base = os.path.splitext(archivo.filename)[0]
            resultados_dir = os.path.join('separated', 'htdemucs', nombre_base)

            vocals = os.path.join(resultados_dir, 'vocals.wav')
            no_vocals = os.path.join(resultados_dir, 'no_vocals.wav')

            if os.path.exists(vocals):
                shutil.move(vocals, os.path.join(ACAPELLAS_FOLDER, f'{nombre_base}.wav'))

            if os.path.exists(no_vocals):
                shutil.move(no_vocals, os.path.join(INSTRUMENTALES_FOLDER, f'{nombre_base}.wav'))

            shutil.rmtree(resultados_dir, ignore_errors=True)

        except Exception as e:
            return f"Error procesando el archivo: {e}", 500

        return redirect(url_for('index'))

    return "Archivo inválido. Solo se permiten archivos .mp3", 400

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
