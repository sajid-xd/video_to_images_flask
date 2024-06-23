from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
import os
import cv2

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'output'

def list_videos(folder):
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]

def list_folders(folder):
    return [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]

def video_to_images(video_path, output_folder, fps):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return

    frame_rate = video_capture.get(cv2.CAP_PROP_FPS)
    frame_interval = int(frame_rate / fps)
    frame_number = 0
    saved_frame_number = 0

    while True:
        success, frame = video_capture.read()
        if not success:
            break
        
        if frame_number % frame_interval == 0:
            image_file_path = os.path.join(output_folder, f"frame_{saved_frame_number:05d}.jpg")
            cv2.imwrite(image_file_path, frame)
            saved_frame_number += 1

        frame_number += 1

    video_capture.release()
    print(f"Extracted {saved_frame_number} frames from {video_path} to {output_folder}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
            elif file and file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
                flash('File uploaded successfully')
            else:
                flash('Invalid file type')

        # Handle video processing
        selected_videos = request.form.getlist('videos')
        if 'fps' in request.form:
            fps = int(request.form.get('fps', 1))

            for video in selected_videos:
                video_path = os.path.join(app.config['UPLOAD_FOLDER'], video)
                video_output_folder = os.path.join(app.config['OUTPUT_FOLDER'], os.path.splitext(video)[0])
                video_to_images(video_path, video_output_folder, fps)

            flash(f'Processed {len(selected_videos)} videos at {fps} frames per second')

    uploaded_videos = list_videos(app.config['UPLOAD_FOLDER'])
    output_folders = list_folders(app.config['OUTPUT_FOLDER'])
    return render_template('index.html', uploaded_videos=uploaded_videos, output_folders=output_folders)

@app.route('/gallery/<folder_name>')
def gallery(folder_name):
    folder_path = os.path.join(app.config['OUTPUT_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Folder does not exist')
        return redirect(url_for('index'))

    images = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return render_template('gallery.html', folder_name=folder_name, images=images)

@app.route('/output/<folder_name>/<filename>')
def send_image(folder_name, filename):
    return send_from_directory(os.path.join(app.config['OUTPUT_FOLDER'], folder_name), filename)

if __name__ == '__main__':
    app.run(debug=True)
