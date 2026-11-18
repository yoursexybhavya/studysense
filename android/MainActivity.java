package com.studysense.app;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

/**
 * Drop-in Android Studio WebView wrapper for StudySense.
 *
 * Setup:
 * 1. Copy index.html into app/src/main/assets/index.html
 * 2. In AndroidManifest.xml add:
 *      <uses-permission android:name="android.permission.INTERNET" />
 *    and on <application>:
 *      android:usesCleartextTraffic="true"  (allows HTTP LAN sync with ESP32 IP)
 */
public class MainActivity extends AppCompatActivity {
    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true); // Persists multi-user profiles on Android
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        webView.loadUrl("file:///android_asset/index.html");
    }
}
