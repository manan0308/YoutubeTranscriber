# YouTube Transcriber & Transcript Viewer Web App

This project is a web application that allows users to transcribe YouTube videos and view the transcriptions. It consists of a Flask backend and a React frontend.

## Table of Contents

- [Project Structure](#project-structure)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Project Structure

- **frontend/**: Contains the React frontend code.
- **backend/**: Contains the Flask backend code.

## Features

- Extract audio from YouTube videos.
- Transcribe audio using AssemblyAI.
- View transcriptions with real-time progress updates.
- Modern UI with light/dark mode support.

## Installation

### Prerequisites

- Node.js and npm for the frontend.
- Python and pip for the backend.
- AssemblyAI API key for transcription services.

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd youtube-transcriber/backend
   ```

2. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Add your AssemblyAI API key to the `.env` file:
   ```plaintext
   ASSEMBLYAI_API_KEY=your_api_key_here
   ```

5. Run the backend server:
   ```bash
   flask run
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd youtube-transcriber/frontend
   ```

2. Install the dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

- Access the application at `http://localhost:5173`.
- Use the interface to upload YouTube video links and receive transcriptions.

## Configuration

- **Environment Variables**: Ensure your AssemblyAI API key is set in the `.env` file in the backend directory.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes.
4. Push to your fork and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
