package com.nihongoquest.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.util.Locale;

public class MainActivity extends Activity {

    private static final String SITE = "https://nihongo.13-61-25-153.sslip.io";

    private WebView web;
    private TextToSpeech tts;
    private volatile boolean ttsReady = false;

    // Exposed to the page as window.AndroidTTS — the site prefers this
    // bridge over speechSynthesis, which Android WebView doesn't support.
    public class TtsBridge {
        @JavascriptInterface
        public void speak(final String text, final float rate) {
            if (!ttsReady || text == null || text.isEmpty()) return;
            tts.setSpeechRate(rate);
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "nq-utterance");
        }

        @JavascriptInterface
        public boolean ready() {
            return ttsReady;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                if (status == TextToSpeech.SUCCESS) {
                    int r = tts.setLanguage(Locale.JAPANESE);
                    ttsReady = r != TextToSpeech.LANG_MISSING_DATA
                            && r != TextToSpeech.LANG_NOT_SUPPORTED;
                    tts.setPitch(1.05f);
                }
            }
        });

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#EEF2FF"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);   // keeps XP/streak progress (localStorage)
        s.setMediaPlaybackRequiresUserGesture(false);
        web.addJavascriptInterface(new TtsBridge(), "AndroidTTS");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri url = request.getUrl();
                String host = url.getHost();
                if (host != null && host.endsWith("sslip.io")) {
                    return false; // stay inside the app
                }
                startActivity(new Intent(Intent.ACTION_VIEW, url));
                return true;
            }
        });

        if (savedInstanceState == null) {
            web.loadUrl(SITE);
        } else {
            web.restoreState(savedInstanceState);
        }
        setContentView(web);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }
}
