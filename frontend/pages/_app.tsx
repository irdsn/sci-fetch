import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";

import "../styles/globals.css";
import type { AppProps } from "next/app";

const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className={`${headingFont.variable} ${bodyFont.variable}`}>
      <Component {...pageProps} />
    </div>
  );
}
