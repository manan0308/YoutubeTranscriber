import React from 'react';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { ExternalLink, PlayCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '../components/ui/form';
import { extractVideoId } from '../utils/youtube';
import { useTranscriptionStore } from '../store/transcriptionStore';

// Validation schema
const formSchema = z.object({
  youtubeUrl: z.string().url('Please enter a valid URL')
    .refine(
      (url) => extractVideoId(url) !== null,
      {
        message: 'Please enter a valid YouTube URL',
      }
    ),
});

const HomePage = () => {
  const navigate = useNavigate();
  const startTranscription = useTranscriptionStore((state) => state.startTranscription);

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      youtubeUrl: '',
    },
  });

  const onSubmit = async (data) => {
    const videoId = extractVideoId(data.youtubeUrl);
    if (!videoId) {
      toast.error('Invalid YouTube URL');
      return;
    }
  
    try {
      toast.message('Starting transcription process...'); // Fixed toast.info
      await startTranscription(data.youtubeUrl, videoId);
      navigate(`/transcript/${videoId}`);
    } catch (error) {
      toast.error('Failed to start transcription: ' + error.message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-4xl font-bold text-center mb-8">YouTube Transcriber</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Transcribe YouTube Videos</CardTitle>
          <CardDescription>
            Enter a YouTube URL to extract and transcribe the audio.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="youtubeUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>YouTube URL</FormLabel>
                    <FormControl>
                      <Input placeholder="https://www.youtube.com/watch?v=..." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
                <PlayCircle className="mr-2 h-4 w-4" />
                Start Transcription
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            Powered by AssemblyAI{' '}
            <a
              href="https://www.assemblyai.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary inline-flex items-center"
            >
              Learn more <ExternalLink className="ml-1 h-3 w-3" />
            </a>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default HomePage;
