import './globals.css';
import { ReactNode } from 'react';

export const metadata = {
  title: 'FastAPI Aviation Map',
  description: 'Map of Aviation Data',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap" rel="stylesheet"/>
      </head>
      <body>{children}</body>
    </html>
  );
}
