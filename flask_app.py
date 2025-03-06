import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from gtts import gTTS
import uuid
from threading import Timer

app = Flask(__name__, static_url_path='/static')

# Cấu hình cho phép tệp tải lên
ALLOWED_EXTENSIONS = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Giới hạn dung lượng tệp 5MB

# Kiểm tra và tạo thư mục audio nếu chưa tồn tại
audio_folder = "./static/audios"
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)

# Hàm kiểm tra tệp được tải lên có phải PDF không
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hàm chuyển đổi PDF thành âm thanh
def pdf_to_voice(file, lang_code):
    reader = PdfReader(file)
    number_of_pages = len(reader.pages)
    text = ""
    for i in range(number_of_pages):
        page = reader.pages[i]
        text += page.extract_text()

    # Sử dụng gTTS để chuyển đổi văn bản thành âm thanh
    tts = gTTS(text=text, lang=lang_code)
    audio_file = f'./static/audios/{uuid.uuid1()}.mp3'

    # Lưu tệp âm thanh
    tts.save(audio_file)
    return audio_file

# Hàm dọn dẹp thư mục audio
def clean_folder(folder_path):
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

# Lên lịch dọn dẹp thư mục mỗi 2 phút
def schedule_folder_clean():
    Timer(120, schedule_folder_clean).start()  # lên lịch dọn dẹp sau mỗi 2 phút
    clean_folder(audio_folder)

schedule_folder_clean()

# Route trang chủ
@app.route('/')
def home():
    return render_template("index.html")

# Route để xử lý chuyển đổi
@app.route('/convert', methods=['POST'])
def convert():
    if request.method == 'POST':
        # Kiểm tra nếu file có trong request
        if 'pdf' not in request.files:
            error_msg = "No file chosen. Please upload a file"
            return render_template("index.html", error_msg=error_msg)

        file = request.files['pdf']

        if file.filename == '':
            error_msg = "No file chosen. Please upload a file"
            return render_template("index.html", error_msg=error_msg)

        if file and allowed_file(file.filename):
            sfilename = secure_filename(file.filename)
            pdf_path = os.path.join('./static/uploadedPDF', sfilename)
            file.save(pdf_path)

            # Chuyển đổi file PDF thành audio
            chosen_voice = request.form.get('chosen_voice', 'en-us')
            audio_file = pdf_to_voice(pdf_path, chosen_voice)
            os.remove(pdf_path)

            # Render lại template và phát audio sau khi xử lý xong
            return render_template("audio.html", audio_file=audio_file)
        else:
            error_msg = "Only pdf files are allowed"
            return render_template("index.html", error_msg=error_msg)

    # Mặc định sẽ trả về trang chủ nếu không phải POST request
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
