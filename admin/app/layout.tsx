import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FinPilot Admin",
  description: "FinPilot administration console by Hastron Ventures",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
