export const extractVideoId = (url) => {
  try {
    // Handle multiple YouTube URL formats
    const urlObj = new URL(url);
    const hostname = urlObj.hostname;
    
    // Regular YouTube URLs
    if (hostname.includes('youtube.com')) {
      return urlObj.searchParams.get('v');
    }
    
    // Shortened youtu.be URLs
    if (hostname === 'youtu.be') {
      return urlObj.pathname.slice(1);
    }
    
    return null;
  } catch (error) {
    return null;
  }
};
