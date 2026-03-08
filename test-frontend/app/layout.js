import "./globals.css";

export const metadata = {
  title: "Bigdata Log Dashboard",
  description: "Test frontend for triggering microservice log events to Kafka",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
