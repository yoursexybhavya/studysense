import SwiftUI
import WebKit

struct WebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        // Clear all stale cache and website data from old Vercel URL
        WKWebsiteDataStore.default().removeData(
            ofTypes: WKWebsiteDataStore.allWebsiteDataTypes(),
            modifiedSince: Date.distantPast
        ) { }

        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []

        // Enable universal local file access for local storage & HTTP calls
        configuration.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
        configuration.setValue(true, forKey: "allowUniversalAccessFromFileURLs")

        // Bridge JS vibration to native iOS Taptic Engine
        let contentController = WKUserContentController()
        contentController.add(context.coordinator, name: "haptic")

        let hapticBridgeScript = WKUserScript(
            source: """
            if (!window._hapticBridgeInstalled) {
                window._hapticBridgeInstalled = true;
                const originalVibrate = navigator.vibrate;
                navigator.vibrate = function(pattern) {
                    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.haptic) {
                        window.webkit.messageHandlers.haptic.postMessage({ pattern: pattern });
                    }
                    if (originalVibrate) originalVibrate.call(navigator, pattern);
                    return true;
                };
            }
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        )
        contentController.addUserScript(hapticBridgeScript)
        configuration.userContentController = contentController

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.backgroundColor = UIColor(red: 11 / 255, green: 15 / 255, blue: 25 / 255, alpha: 1)
        webView.isOpaque = false
        webView.scrollView.backgroundColor = UIColor(red: 11 / 255, green: 15 / 255, blue: 25 / 255, alpha: 1)
        webView.scrollView.bounces = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.customUserAgent = "StudySense-iOS/1.2 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"

        // Strictly locate and load local bundled index.html
        let localUrl: URL? = Bundle.main.url(forResource: "index", withExtension: "html")
            ?? Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "www")

        if let url = localUrl {
            print("📱 StudySense: Loading local bundled app from \(url.path)")
            webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        } else {
            // Self-contained emergency fallback if bundle resource is missing
            let errorHtml = "<html><body style='background:#0b0f19;color:white;display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;'><h2>Error: index.html missing from bundle</h2></body></html>"
            webView.loadHTMLString(errorHtml, baseURL: nil)
        }

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    class Coordinator: NSObject, WKScriptMessageHandler {
        private let impactGenerator = UIImpactFeedbackGenerator(style: .medium)

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "haptic" else { return }
            impactGenerator.prepare()
            impactGenerator.impactOccurred()
        }
    }
}
