import os
import re
import json
import logging
import logging.config
from logging.handlers import RotatingFileHandler
import tempfile
import time
import requests
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import assemblyai as aai
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.dirname(__file__), 'app.log'),
            'maxBytes': 1024 * 1024,  # 1 MB
            'backupCount': 3,
            'formatter': 'standard',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'httpcore': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # suppress low-level HTTP logs
            'propagate': False,
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Setup Flask app and CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load API Keys securely
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    raise ValueError("❌ ERROR: AssemblyAI API key is missing. Set it in a `.env` file.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("⚠️ OpenAI API key is missing. Summary functionality will be unavailable.")
else:
    logger.info("✅ OpenAI API key loaded successfully.")

# Initialize OpenAI client (only if key is available)
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# Setup AssemblyAI client
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()

# Use a persistent HTTP session for all outbound requests
session = requests.Session()

def extract_video_id(youtube_url):
    """Extract YouTube video ID from URL."""
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, youtube_url)
    if match:
        video_id = match.group(1)
        logger.info(f"✅ Extracted video ID: {video_id}")
        return video_id
    else:
        logger.error(f"❌ Failed to extract video ID from URL: {youtube_url}")
        return None

def download_audio(youtube_url, video_id):
    """Download audio from YouTube using yt-dlp."""
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "outtmpl": os.path.join(TEMP_DIR, f"{video_id}.%(ext)s"),
        "quiet": True,
    }
    try:
        logger.info(f"📥 Downloading audio for video ID: {video_id}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        final_audio_path = os.path.join(TEMP_DIR, f"{video_id}.mp3")
        logger.info(f"✅ Audio downloaded successfully: {final_audio_path}")
        return final_audio_path
    except Exception as e:
        logger.error(f"❌ Failed to download audio: {str(e)}")
        raise Exception(f"Failed to download audio: {str(e)}")

def upload_and_transcribe(file_path):
    """Upload and transcribe the audio file using AssemblyAI."""
    logger.info(f"📤 Uploading file for transcription: {file_path}")
    try:
        transcript = transcriber.transcribe(file_path, config=aai.TranscriptionConfig(speaker_labels=True))
        logger.info(f"✅ Transcription job started. Transcript ID: {transcript.id}")
        return transcript
    except Exception as e:
        logger.error(f"❌ Failed to upload and transcribe: {str(e)}")
        raise Exception(f"Failed to upload and transcribe: {str(e)}")

def check_transcription_status(transcript_id):
    """Check the status of a transcription job using a persistent HTTP session."""
    logger.info(f"🔍 Checking transcription status for ID: {transcript_id}")
    try:
        headers = {"authorization": ASSEMBLYAI_API_KEY}
        url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        response = session.get(url, headers=headers)
        response.raise_for_status()
        transcript = response.json()
        status = transcript.get("status")
        if status == "completed":
            transcript_text = transcript.get("text")
            logger.info(f"✅ Transcription completed: {transcript_text[:50]}...")
            return {"status": "completed", "text": transcript_text}
        elif status == "error":
            error_message = transcript.get("error", "Transcription failed")
            logger.error(f"❌ Transcription failed for ID: {transcript_id} with error: {error_message}")
            return {"status": "error", "message": error_message}
        else:
            logger.info(f"⏳ Transcription still processing: {status}")
            return {"status": status}
    except Exception as e:
        logger.error(f"❌ Error checking transcription status: {str(e)}")
        return {"status": "error", "message": f"Error checking transcription status: {str(e)}"}

def poll_transcription(transcript_id, timeout=60, initial_delay=1, max_delay=8):
    """Poll AssemblyAI using exponential backoff until completion, error, or timeout."""
    start_time = time.time()
    delay = initial_delay
    while time.time() - start_time < timeout:
        transcript_data = check_transcription_status(transcript_id)
        if transcript_data["status"] in ["completed", "error"]:
            return transcript_data
        time.sleep(delay)
        delay = min(max_delay, delay * 2)
    return {"status": "error", "message": "Polling timed out"}

def summarise_transcript(transcript_text):
    """Generate a summary of the transcript using OpenAI's API."""
    if not transcript_text:
        return "No transcript available for summarization."
    prompt = (
        "Please provide a concise and comprehensive summary of the following transcript. "
        "Highlight the main points, key insights, and overall message. "
        "Format your summary in clear bullet points.\n\n"
        f"Transcript:\n{transcript_text}\n\nSummary:"
    )
    try:
        response = client.chat.completions.create(model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert summarizer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7)
        summary = response.choices[0].message.content.strip()
        logger.info("✅ Summary generated successfully")
        return summary
    except Exception as e:
        logger.error(f"❌ Failed to generate summary: {str(e)}")
        return "Summary unavailable due to an error."

@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """Start the transcription process for a given YouTube URL."""
    try:
        data = request.json
        youtube_url = data.get("youtubeUrl")
        if not youtube_url:
            raise BadRequest("YouTube URL is required")
        video_id = extract_video_id(youtube_url)
        if not video_id:
            raise BadRequest("Invalid YouTube URL")
        logger.info(f"📝 Received transcription request for Video ID: {video_id}")
        if video_id in transcription_jobs:
            job_info = transcription_jobs[video_id]
            logger.info(f"⚠️ Transcription already in progress for {video_id}")
            return jsonify({
                "videoId": video_id,
                "status": job_info["status"],
                "progress": job_info["progress"],
                "message": "Already in progress"
            })
        transcription_jobs[video_id] = {
            "status": "downloading",
            "progress": 10,
            "transcript_id": None,
            "transcript_text": None,
            "summary": None
        }
        audio_path = download_audio(youtube_url, video_id)
        transcription_jobs[video_id]["status"] = "uploading"
        transcription_jobs[video_id]["progress"] = 30
        transcript = upload_and_transcribe(audio_path)
        transcription_jobs[video_id]["transcript_id"] = transcript.id
        transcription_jobs[video_id]["status"] = "processing"
        transcription_jobs[video_id]["progress"] = 60
        try:
            os.remove(audio_path)
            logger.info(f"🗑️ Deleted temporary file: {audio_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete temporary file {audio_path}: {str(e)}")
        return jsonify({
            "videoId": video_id,
            "status": "processing",
            "progress": 60,
            "message": "Transcription started"
        })
    except BadRequest as e:
        logger.warning(f"⚠️ Bad request: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"❌ Server error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/transcription-status/<video_id>", methods=["GET"])
def transcription_status(video_id):
    """Return the current transcription status (and summary if available) without blocking."""
    try:
        if video_id not in transcription_jobs:
            logger.error(f"❌ Transcription job not found: {video_id}")
            return jsonify({"status": "error", "message": "Transcription job not found"}), 404
        job_info = transcription_jobs[video_id]
        if job_info["status"] in ["queued", "processing", "uploading"] and job_info["transcript_id"]:
            transcript_data = check_transcription_status(job_info["transcript_id"])
            if transcript_data["status"] == "completed":
                job_info["status"] = "completed"
                job_info["transcript_text"] = transcript_data["text"]
                job_info["progress"] = 100
                job_info["summary"] = summarise_transcript(job_info["transcript_text"])
            elif transcript_data["status"] == "error":
                job_info["status"] = "error"
                job_info["progress"] = 0
                job_info["error"] = transcript_data["message"]
            else:
                job_info["status"] = transcript_data["status"]
        return jsonify({
            "videoId": video_id,
            "status": job_info["status"],
            "progress": job_info["progress"],
            "transcript": job_info.get("transcript_text"),
            "summary": job_info.get("summary"),
            "error": job_info.get("error"),
        })
    except Exception as e:
        logger.error(f"❌ Error checking status: {str(e)}")
        return jsonify({"status": "error", "message": f"Error checking status: {str(e)}"}), 500

@app.route("/api/poll-transcription/<video_id>", methods=["GET"])
def poll_transcription_endpoint(video_id):
    """
    Poll the transcript status in a blocking manner using exponential backoff.
    Once completed, also generate a summary of the transcript.
    """
    try:
        if video_id not in transcription_jobs:
            logger.error(f"❌ Transcription job not found: {video_id}")
            return jsonify({"status": "error", "message": "Transcription job not found"}), 404
        job_info = transcription_jobs[video_id]
        transcript_id = job_info.get("transcript_id")
        if not transcript_id:
            return jsonify({"status": "error", "message": "Transcript ID not available"}), 400

        transcript_data = poll_transcription(transcript_id, timeout=60, initial_delay=1, max_delay=8)
        if transcript_data["status"] == "completed":
            job_info["status"] = "completed"
            job_info["transcript_text"] = transcript_data.get("text")
            job_info["progress"] = 100
            job_info["summary"] = summarise_transcript(job_info["transcript_text"])
        elif transcript_data["status"] == "error":
            job_info["status"] = "error"
            job_info["progress"] = 0
            job_info["error"] = transcript_data.get("message")

        return jsonify({
            "videoId": video_id,
            "status": job_info["status"],
            "progress": job_info["progress"],
            "transcript": job_info.get("transcript_text"),
            "summary": job_info.get("summary"),
            "error": job_info.get("error"),
        })
    except Exception as e:
        logger.error(f"❌ Error polling transcription status: {str(e)}")
        return jsonify({"status": "error", "message": f"Error polling transcription status: {str(e)}"}), 500

@app.errorhandler(400)
def handle_bad_request(error):
    return jsonify({"status": "error", "message": str(error)}), 400

@app.errorhandler(500)
def handle_server_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Flask backend is working"})

if __name__ == "__main__":
    app.run(debug=True, port=8888)
