import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { AlertCircle, ArrowLeft, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Button } from '../components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { useTranscriptionStore } from '../store/transcriptionStore';

const TranscriptPage = () => {
  const { videoId } = useParams();
  const {
    status,
    progress,
    transcript,
    error,
    fetchTranscriptionStatus,
    resetTranscription,
  } = useTranscriptionStore();

  useEffect(() => {
    if (!videoId) return;

    // Start polling only if transcription isn't completed
    if (status !== 'completed' && status !== 'error') {
      fetchTranscriptionStatus(videoId);
    }
  }, [videoId, status]);

  const getStatusText = () => {
    switch (status) {
      case 'queued':
        return 'Queued for processing';
      case 'processing':
        return 'Processing audio';
      case 'uploading':
        return 'Uploading audio to transcription service';
      case 'downloading':
        return 'Downloading audio from YouTube';
      case 'completed':
        return 'Transcription completed';
      case 'error':
        return 'Error occurred';
      default:
        return 'Initializing...';
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-4">
        <Button variant="ghost" asChild>
          <Link to="/" onClick={resetTranscription}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Transcript for Video ID: {videoId}</CardTitle>
          <CardDescription>
            {status === 'completed'
              ? 'Your transcript is ready'
              : "We're currently processing your video"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {status === 'error' ? (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error || 'An unknown error occurred'}</AlertDescription>
            </Alert>
          ) : status !== 'completed' ? (
            <div className="space-y-4">
              <p className="text-center text-muted-foreground">{getStatusText()}</p>
              <Progress value={progress} className="w-full" />
              <p className="text-center text-sm text-muted-foreground">{progress}% complete</p>
            </div>
          ) : (
            <div className="mb-4 p-4 bg-muted rounded-md">
              <h3 className="text-lg font-medium mb-2 flex items-center">
                <FileText className="mr-2 h-5 w-5" />
                Transcript
              </h3>
              <div className="max-h-[500px] overflow-y-auto whitespace-pre-wrap">
                {transcript ? transcript : 'No transcript available.'}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TranscriptPage;
