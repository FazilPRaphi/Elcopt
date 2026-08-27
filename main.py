import os
from functools import wraps

import requests
import firebase_admin

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import cloudinary
import cloudinary.uploader

from firebase_admin import credentials, firestore, auth

from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)



cred = credentials.Certificate("serviceAccountKey.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()



app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "elcopt_super_secret_key_2026"
)




FIREBASE_WEB_API_KEY = os.environ.get(
    "FIREBASE_WEB_API_KEY",
    ""
)

PORT = int(os.environ.get("PORT", "5000"))



def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Please login to access this page.",
                "warning"
            )

            return redirect(
                url_for(
                    "login",
                    next=request.url
                )
            )

        return f(*args, **kwargs)

    return decorated_function



@app.route("/")
def home():

    return render_template("home.html")



@app.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        

        if not username or not email or not password:

            flash(
                "All fields are required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )

       
        try:

            existing_users = (
                db.collection("users")
                .where(
                    "username",
                    "==",
                    username
                )
                .limit(1)
                .get()
            )

            if len(existing_users) > 0:

                flash(
                    "Username is already taken.",
                    "danger"
                )

                return render_template(
                    "register.html"
                )

        except Exception as e:

            app.logger.error(
                f"Firestore username check failed: {e}"
            )

            flash(
                "Could not connect to Firestore.",
                "danger"
            )

            return render_template(
                "register.html"
            )


        try:

            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=username
            )

        except auth.EmailAlreadyExistsError:

            flash(
                "An account with this email already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        except Exception as e:

            app.logger.error(
                f"Firebase Auth registration error: {e}"
            )

            flash(
                "Could not create your account.",
                "danger"
            )

            return render_template(
                "register.html"
            )

       

        try:

            db.collection("users").document(
                user_record.uid
            ).set({

                "uid": user_record.uid,

                "username": username,

                "email": email,

                "created_at": firestore.SERVER_TIMESTAMP

            })

        except Exception as e:

            app.logger.error(
                f"Firestore user creation failed: {e}"
            )

           

            flash(
                "Account created, but profile setup failed.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        flash(
            "Account created successfully! Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )




@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        identifier = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            raise ValueError("Username/email and password are required.")

       

        target_email = identifier.lower()

        # Username login
        if "@" not in identifier:

            users = (
                db.collection("users")
                .where(
                    "username",
                    "==",
                    identifier
                )
                .limit(1)
                .get()
            )

            if len(users) == 0:
                raise ValueError(
                    f"No user found with username: {identifier}"
                )

            user_data = users[0].to_dict()

            target_email = (user_data.get("email") or "").lower()

            if not target_email:
                raise ValueError(
                    f"User '{identifier}' has no email in Firestore."
                )

        print(f"\n[LOGIN DEBUG]")
        print(f"Identifier : {identifier}")
        print(f"Target email: {target_email}")

       

        if not FIREBASE_WEB_API_KEY:
            raise RuntimeError(
                "FIREBASE_WEB_API_KEY is not configured."
            )

        

        auth_url = (
            "https://identitytoolkit.googleapis.com/"
            "v1/accounts:signInWithPassword"
            f"?key={FIREBASE_WEB_API_KEY}"
        )

        payload = {
            "email": target_email,
            "password": password,
            "returnSecureToken": True
        }

        print("[LOGIN DEBUG] Sending request to Firebase...")

        response = requests.post(
            auth_url,
            json=payload,
            timeout=10
        )

        print(
            f"[LOGIN DEBUG] Firebase response status: "
            f"{response.status_code}"
        )

       

        if response.status_code != 200:

            print(
                "[LOGIN DEBUG] Firebase response:"
            )
            print(response.text)

            raise RuntimeError(
                f"Firebase authentication failed: "
                f"{response.status_code} - {response.text}"
            )

       

        auth_data = response.json()

        id_token = auth_data.get("idToken")
        uid = auth_data.get("localId")

        if not id_token:
            raise RuntimeError(
                "Firebase response did not contain idToken."
            )

        if not uid:
            raise RuntimeError(
                "Firebase response did not contain localId."
            )

        print(f"[LOGIN DEBUG] Firebase UID: {uid}")
        print("[LOGIN DEBUG] Firebase password authentication SUCCESS")

        
        print("[LOGIN DEBUG] Verifying Firebase ID token...")

        decoded_token = auth.verify_id_token(
            id_token,
            clock_skew_seconds=60
        )

        print("[LOGIN DEBUG] ID token verification SUCCESS")

        verified_uid = decoded_token["uid"]

        

        if verified_uid != uid:
            raise RuntimeError(
                f"Firebase UID mismatch! "
                f"Token UID={verified_uid}, "
                f"Login UID={uid}"
            )

        print(f"[LOGIN DEBUG] Verified UID: {verified_uid}")

        

        user_record = auth.get_user(verified_uid)

        print(
            f"[LOGIN DEBUG] Firebase user: "
            f"{user_record.email}"
        )

       
        session.clear()

        session["user_id"] = verified_uid
        session["email"] = user_record.email
        session["username"] = (
            user_record.display_name
            or identifier
        )

        print(
            f"[LOGIN DEBUG] Flask session created for "
            f"{session['username']}"
        )

        # ------------------------------------------
        # Redirect
        # ------------------------------------------

        next_page = request.args.get("next")

        if next_page:
            return redirect(next_page)

        return redirect(
            url_for("dashboard")
        )

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    user_doc = None

    try:

        document = (
            db.collection("users")
            .document(user_id)
            .get()
        )

        if document.exists:

            user_doc = document.to_dict()

    except Exception as e:

        app.logger.error(
            f"Firestore dashboard lookup failed: {e}"
        )

        flash(
            "Could not load your profile.",
            "warning"
        )

   

    images = []

    try:

        image_docs = (
            db.collection("users")
            .document(user_id)
            .collection("images")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .get()
        )

        for doc in image_docs:
            img = doc.to_dict()
            img["doc_id"] = doc.id
            images.append(img)

    except Exception as e:

        app.logger.error(
            f"Firestore images lookup failed: {e}"
        )

    return render_template(

        "dashboard.html",

        user_id=user_id,

        email=session.get("email"),

        username=session.get("username"),

        user_doc=user_doc,

        images=images

    )

@app.route("/upload", methods=["POST"])
@login_required
def upload():

    if "image" not in request.files:
        flash("No image selected.", "danger")
        return redirect(url_for("dashboard"))

    image = request.files["image"]

    if image.filename == "":
        flash("No image selected.", "danger")
        return redirect(url_for("dashboard"))

    try:

        # -----------------------------
        # Upload image to Cloudinary
        # -----------------------------

        result = cloudinary.uploader.upload(
            image,
            folder=f"elcopt/{session['user_id']}"
        )

        # -----------------------------
        # Get Cloudinary information
        # -----------------------------

        image_url = result["secure_url"]
        public_id = result["public_id"]

        # -----------------------------
        # Save metadata in Firestore
        # -----------------------------

        image_ref = (
            db.collection("users")
            .document(session["user_id"])
            .collection("images")
            .document()
        )

        image_ref.set({

            "url": image_url,

            "public_id": public_id,

            "original_filename": image.filename,

            "format": result.get("format"),

            "width": result.get("width"),

            "height": result.get("height"),

            "bytes": result.get("bytes"),

            "created_at": firestore.SERVER_TIMESTAMP

        })

        flash(
            "Image uploaded successfully!",
            "success"
        )

    except Exception as e:

        app.logger.error(
            f"Image upload failed: {e}"
        )

        flash(
            "Image upload failed.",
            "danger"
        )

    return redirect(url_for("dashboard"))
@app.route("/delete_image/<image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    if user_id := session.get("user_id"):
        try:
        
            image_doc = (
                db.collection("users")
                .document(user_id)
                .collection("images")
                .document(image_id)
                .get()
            )

            if not image_doc.exists:
                flash("Image not found.", "danger") 
                return redirect(url_for("dashboard"))

            image_data = image_doc.to_dict()
            public_id = image_data.get("public_id")

            # Delete from Cloudinary
            cloudinary.uploader.destroy(public_id)

            # Delete from Firestore
            (
                db.collection("users")
                .document(user_id)
                .collection("images")
                .document(image_id)
                .delete()
            )

            flash("Image deleted successfully.", "success")

        except Exception as e:
            app.logger.error(f"Image deletion failed: {e}")
            flash("Image deletion failed.", "danger")

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(
        url_for("login")
    )


# --------------------------------------------------
# Run Flask
# --------------------------------------------------


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )