import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
    title: "Topup CXO Assistant",
    description: "Conversational CXO marketing assistant",
}

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode
}>) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className}>
                <ThemeProvider
                    defaultTheme="system"
                    storageKey="topup-ui-theme"
                >
                    {children}
                </ThemeProvider>
            </body>
        </html>
    )
}
