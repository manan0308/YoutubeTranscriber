import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8888/api';

export const useTranscriptionStore = create(
  persist(
    (set, get) => ({
      currentVideoId: null,
      status: 'idle',
      progress: 0,
      transcript: null,
      error: null,

      // Start the transcription process
      startTranscription: async (youtubeUrl, videoId) => {
        set({
          currentVideoId: videoId,
          status: 'downloading',
          progress: 10,
          transcript: null,
          error: null,
        });
        try {
          console.log("Sending transcription request...");
          const response = await axios.post(`${API_BASE_URL}/transcribe`, { youtubeUrl, videoId });
          set({
            status: response.data.status || 'queued',
            progress: response.data.progress || 20,
          });
          // Instead of continuously polling from the frontend, we call the blocking poll endpoint.
          get().fetchTranscriptionStatus(videoId);
          return response.data;
        } catch (error) {
          set({
            status: 'error',
            error: error.response?.data?.message || error.message,
            progress: 0,
          });
          throw error;
        }
      },

      // Poll transcription status using the blocking endpoint
      fetchTranscriptionStatus: async (videoId) => {
        try {
          console.log(`🔄 Polling transcription status for: ${videoId}`);
          const response = await axios.get(`${API_BASE_URL}/poll-transcription/${videoId}`);
          console.log("📡 Poll response:", response.data);
          const data = response.data;
          if (data.status === 'completed') {
            console.log("✅ Transcription completed! Transcript:", data.transcript);
            set({
              status: 'completed',
              progress: 100,
              transcript: data.transcript,
            });
          } else if (data.status === 'error') {
            console.error("🚨 Error fetching transcription:", data.error);
            set({
              status: 'error',
              error: data.error || "Unknown error",
            });
          } else {
            // Fallback (should not occur with blocking poll)
            set({
              status: data.status,
              progress: data.progress || 50,
            });
          }
        } catch (error) {
          console.error("🚨 API Fetch Error:", error);
          set({
            status: 'error',
            error: error.response?.data?.message || error.message,
          });
        }
      },

      resetTranscription: () => set({
        currentVideoId: null,
        status: 'idle',
        progress: 0,
        transcript: null,
        error: null,
      }),
    }),
    {
      name: 'transcription-storage',
      partialize: (state) => ({
        currentVideoId: state.currentVideoId,
        status: state.status,
        progress: state.progress,
        transcript: state.transcript,
      }),
    }
  )
);
