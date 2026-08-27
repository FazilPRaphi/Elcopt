<div align="center">
  <img src="static/favicon.png" alt="Elcopt Favicon" width="120" />
  <h1>Elcopt</h1>
  <p><strong>A streamlined image upload and management dashboard</strong></p>

  <a href="https://elcopt-3.onrender.com/">
    <img src="https://img.shields.io/badge/Live_Demo-elcopt--3.onrender.com-brightgreen?style=for-the-badge" alt="Live Demo" />
  </a>
</div>

<br />

<div align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python" />
  <img src="https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/jinja-white.svg?style=for-the-badge&logo=jinja&logoColor=black" alt="Jinja" />
  <img src="https://img.shields.io/badge/firebase-%23039BE5.svg?style=for-the-badge&logo=firebase" alt="Firebase" />
  <img src="https://img.shields.io/badge/cloudinary-%233448C5.svg?style=for-the-badge&logo=cloudinary&logoColor=white" alt="Cloudinary" />
</div>

## 🚀 Overview

Elcopt is a modern web application built with Python and Flask. It provides a secure user authentication system (via Firebase) and a personal dashboard where users can upload, manage, and view their images (hosted on Cloudinary).

## 🛠️ Features

- **Secure Authentication:** User registration and login utilizing Firebase Authentication and Firestore.
- **Image Management:** Seamless image uploading and deletion via Cloudinary.
- **Personal Dashboard:** A minimal and intuitive user interface rendered with Jinja2.

## ⚙️ Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/elcopt.git
cd elcopt
```

### 2. Set up the virtual environment & install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and add your credentials:
```env
FLASK_SECRET_KEY=your_secret_key_here
FIREBASE_WEB_API_KEY=your_firebase_web_api_key

CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

### 4. Configure Firebase Admin SDK
Download your Firebase `serviceAccountKey.json` from the Firebase Console and place it in the root directory of the project.

### 5. Run the Application
```bash
python main.py
```
*The app will be available at `http://127.0.0.1:5000/`*
