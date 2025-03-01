import React from 'react';

const Footer = () => {
  return (
    <footer className="border-t bg-background py-4">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <p>© {new Date().getFullYear()} YouTube Transcriber. All rights reserved.</p>
      </div>
    </footer>
  );
};

export default Footer;
