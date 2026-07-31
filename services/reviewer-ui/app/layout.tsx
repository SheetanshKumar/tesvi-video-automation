export const metadata = {
  title: "TesVi Reviewer",
  description: "Review and approve LLM-extracted questions before publish.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
