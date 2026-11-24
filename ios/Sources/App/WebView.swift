import SwiftUI
import WebKit

struct WebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
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
        webView.customUserAgent = "StudySense-iOS/1.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"

        // Load local bundle or fallback to production server
        if let localUrl = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "www") {
            webView.loadFileURL(localUrl, allowingReadAccessTo: localUrl.deletingLastPathComponent())
        } else if let fallbackUrl = URL(string: "https://studysense-eight.vercel.app") {
            webView.load(URLRequest(url: fallbackUrl))
        }

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    class Coordinator: NSObject, WKScriptMessageHandler {
        private let impactGenerator = UIImpactFeedbackGenerator(style: .medium)
        private let notificationGenerator = UINotificationFeedbackGenerator()

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == "haptic" else { return }
            impactGenerator.prepare()
            impactGenerator.impactOccurred()
        }
    }
}
