from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import cv2
import pytesseract
import numpy as np
import os
from datetime import datetime
import base64
from models import db, Document
from PIL import Image
import io
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

app = Flask(__name__)
CORS(app)

# 보안 설정
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30분

# static 파일 서빙 설정
app.static_folder = 'static'
app.static_url_path = '/static'

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///documents.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 저장 디렉토리 설정
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'scanned_documents')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 문서 카테고리 정의
DOCUMENT_CATEGORIES = [
    '생산지',
    '품질',
    '원산지',
    '기타'
]

# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()

# 서버 설정
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', 8080))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(DOCUMENT_CATEGORIES)

@app.route('/documents', methods=['GET'])
def get_documents():
    try:
        category = request.args.get('category')
        filename = request.args.get('filename')
        
        query = Document.query
        
        if category:
            query = query.filter_by(category=category)
        if filename:
            query = query.filter_by(filename=filename)
            
        documents = query.order_by(Document.created_at.desc()).all()
        return jsonify([doc.to_dict() for doc in documents])
    except Exception as e:
        app.logger.error(f'문서 조회 중 오류 발생: {str(e)}')
        return jsonify({'error': '문서 조회 중 오류가 발생했습니다.'}), 500

def process_image(img):
    try:
        # 이미지 전처리
        # 1. 그레이스케일 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 3. 적응형 이진화
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # 4. 모폴로지 연산으로 텍스트 선명화
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 5. 윤곽선 찾기
        edges = cv2.Canny(morph, 75, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # 6. 가장 큰 사각형 찾기
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            
            if len(approx) == 4:  # 사각형인 경우
                points = np.float32([approx[0][0], approx[1][0], approx[2][0], approx[3][0]])
                width = max(np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3]))
                height = max(np.linalg.norm(points[0] - points[3]), np.linalg.norm(points[1] - points[2]))
                
                dst_points = np.float32([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
                matrix = cv2.getPerspectiveTransform(points, dst_points)
                result = cv2.warpPerspective(img, matrix, (int(width), int(height)))
                
                # 7. 최종 이미지 전처리
                result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
                result_denoised = cv2.fastNlMeansDenoising(result_gray)
                result_binary = cv2.adaptiveThreshold(
                    result_denoised,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,
                    2
                )
                
                return result_binary
        
        # 문서를 찾지 못한 경우 원본 이미지에 기본 전처리 적용
        return morph
    except Exception as e:
        app.logger.error(f'이미지 처리 중 오류 발생: {str(e)}')
        raise

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'image' not in request.files:
            return jsonify({'error': '이미지가 없습니다.'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '선택된 파일이 없습니다.'}), 400

        # 카테고리 확인
        category = request.form.get('category')
        if not category:
            return jsonify({'error': '카테고리를 선택해주세요.'}), 400

        # 이미지 데이터 읽기
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # 이미지를 numpy 배열로 변환
        img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 이미지 전처리
        processed_img = process_image(img_array)
        
        # OCR 처리
        app.logger.info('OCR 처리 시작...')
        custom_config = r'--oem 3 --psm 6 -l kor+eng'
        text = pytesseract.image_to_string(processed_img, config=custom_config)
        app.logger.info(f'OCR 처리 완료. 추출된 텍스트: {text}')
        
        # 현재 시간을 기반으로 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'document_{timestamp}.jpg'
        
        # 처리된 이미지 저장
        output_path = os.path.join(UPLOAD_FOLDER, filename)
        cv2.imwrite(output_path, processed_img)
        
        # 문서 정보를 데이터베이스에 저장
        document = Document(
            filename=filename,
            category=category,
            text_content=text,
            created_at=datetime.now()
        )
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': '파일이 성공적으로 업로드되었습니다.',
            'text': text,
            'filename': filename
        })
        
    except Exception as e:
        app.logger.error(f'파일 업로드 중 오류 발생: {str(e)}')
        return jsonify({'error': '파일 업로드 중 오류가 발생했습니다.'}), 500

@app.route('/images/<path:filename>')
def serve_image(filename):
    try:
        return send_file(os.path.join(UPLOAD_FOLDER, filename))
    except Exception as e:
        app.logger.error(f'이미지 서빙 중 오류 발생: {str(e)}')
        return jsonify({'error': '이미지를 불러오는 중 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("서버가 다음 주소에서 실행됩니다:")
    print(f"http://localhost:9000")
    
    try:
        app.run(
            host='0.0.0.0',
            port=9000,
            debug=True
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"포트 9000이 이미 사용 중입니다. 다른 포트를 사용하거나 이전 프로세스를 종료해주세요.")
        else:
            print(f"서버 실행 중 오류 발생: {e}")
    finally:
        print("리소스를 정리합니다...") 