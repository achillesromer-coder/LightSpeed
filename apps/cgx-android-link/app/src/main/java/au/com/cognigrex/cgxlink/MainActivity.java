package au.com.cognigrex.cgxlink;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.database.Cursor;
import android.graphics.Typeface;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.text.InputType;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Android file/deep-link association only. It is NOT an LS executor or auth provider. */
public final class MainActivity extends Activity {
    private static final int PICK_CGX = 3001;
    private static final int MAX_BYTES = 65536;
    private static final String ROOT = "cgx://cgx.cgx";
    private static final String SITE_UI = "https://lightspeed-go.nathaniel-b.chatgpt.site/";
    private static final String PUBLIC_UI = "https://lightspeed-go.nathaniel-b.chatgpt.site/";
    private TextView status;
    private EditText origin;
    private boolean verifiedContract;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        render();
        handleIntent(getIntent());
    }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }
    private void render() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        int margin = (int)(18f * getResources().getDisplayMetrics().density);
        body.setPadding(margin, margin, margin, margin);
        scroll.addView(body);
        TextView title = new TextView(this);
        title.setText("CGX · Mobile Link"); title.setTextSize(24); title.setTypeface(null, Typeface.BOLD);
        body.addView(title);
        TextView description = new TextView(this);
        description.setText("Opens an existing CGX carrier and routes this phone to the existing LightSpeed GO runtime. No mobile executor, embedded keys or new desktop service.");
        description.setTextSize(16); body.addView(description);
        status = new TextView(this);
        status.setText("No CGX carrier loaded. Not connected to BouwerBase.");
        status.setPadding(0, margin, 0, margin); status.setTextIsSelectable(true);
        body.addView(status);
        addButton(body, "Choose a .cgx file", () -> {
            Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            pick.setType("*/*"); pick.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(pick, PICK_CGX);
        });
        TextView urlLabel = new TextView(this);
        addButton(body, "Open LS GO and sign in with ChatGPT", () -> browse(SITE_UI));
        urlLabel.setText("Optional legacy direct-host HTTPS origin (not required for the LS GO Site):");
        body.addView(urlLabel);
        origin = new EditText(this);
        origin.setSingleLine(true);
        origin.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        origin.setHint("https://your-private-host.example");
        origin.setText(getPreferences(MODE_PRIVATE).getString("origin", ""));
        body.addView(origin);
        addButton(body, "Save private origin", () -> {
            try { String v = validatedOrigin();
                getPreferences(MODE_PRIVATE).edit().putString("origin", v).apply();
                show("Private origin saved. Endpoint and authentication NOT verified.");
            } catch (Exception e) { show("Origin rejected: " + e.getMessage()); }
        });
        addButton(body, "Open private LightSpeed GO", () -> openPrivate("/"));
        addButton(body, "Open connection status in LS GO", () -> openPrivate("/"));
        addButton(body, "Open owner sign-in and DBR results in LS GO", () -> openPrivate("/"));
        addButton(body, "Open existing LightSpeed GO web interface", () -> browse(PUBLIC_UI));
        TextView note = new TextView(this);
        note.setText("Use the existing owner-private LS GO Site over mobile data and sign in with ChatGPT. The PC exchanges bounded reports outbound to that same Site. A recognized carrier or host report does not prove device enrollment or execution. 127.0.0.1 refers to this phone.");
        note.setPadding(0, margin, 0, 0); body.addView(note);
        setContentView(scroll);
    }
    private void addButton(LinearLayout body, String label, Runnable action) {
        Button button = new Button(this); button.setAllCaps(false); button.setText(label);
        button.setOnClickListener(v -> action.run()); body.addView(button);
    }
    private void show(String msg) { status.setText(msg); }
    private String validatedOrigin() {
        try { return MobileCarrier.validateOrigin(origin.getText().toString()); }
        catch (Exception error) { throw new IllegalArgumentException(error.getMessage()); }
    }
    private void openPrivate(String path) {
        if (!verifiedContract) {
            show("Load and validate your CGX carrier first. Host remains unverified."); return;
        }
        try { browse(validatedOrigin() + path); }
        catch (Exception ex) { show("Private route not ready: " + ex.getMessage()); }
    }
    private void browse(String url) {
        try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
            show("Opened browser navigation: " + url + "\nVerify host identity, sign-in and receipts there. This does not prove connectivity.");
        } catch (Exception ex) { show("No browser/navigation: " + ex.getMessage()); }
    }
    private void handleIntent(Intent intent) {
        verifiedContract = false;
        if (intent == null) return;
        String action = intent.getAction();
        if (Intent.ACTION_VIEW.equals(action) && intent.getData() != null) {
            Uri incoming = intent.getData();
            if ("cgx".equals(incoming.getScheme())) {
                show(ROOT.equals(incoming.toString()) ?
                     "CGX URI recognized. Load a carrier to validate host binding." :
                     "Unknown CGX URI. Expected " + ROOT);
            } else if ("content".equals(incoming.getScheme()) || "file".equals(incoming.getScheme())) {
                loadCarrier(incoming);
            }
        } else if (Intent.ACTION_SEND.equals(action)) {
            Uri shared = intent.getParcelableExtra(Intent.EXTRA_STREAM);
            if (shared != null && ("content".equals(shared.getScheme()) || "file".equals(shared.getScheme()))) loadCarrier(shared);
        }
    }
    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_CGX && resultCode == RESULT_OK && data != null && data.getData() != null) {
            loadCarrier(data.getData());
        }
    }
    private void loadCarrier(Uri uri) {
        verifiedContract = false;
        try {
            String filename = displayName(uri);
            if (filename != null && !filename.toLowerCase(java.util.Locale.ROOT).endsWith(".cgx")) {
                throw new IllegalArgumentException("Not a .cgx file: " + filename);
            }
            byte[] bytes;
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                if (in == null) throw new IllegalArgumentException("File cannot be opened");
                ByteArrayOutputStream out = new ByteArrayOutputStream(); byte[] buffer = new byte[4096];
                int n;
                while ((n = in.read(buffer)) != -1) {
                    if (out.size() + n > MAX_BYTES) throw new IllegalArgumentException("CGX file exceeds 64 KiB");
                    out.write(buffer, 0, n);
                }
                bytes = out.toByteArray();
            }
            MobileCarrier.validate(bytes);
            verifiedContract = true;
            show("Mobile CGX schema recognized locally: CGX-MOBILE-BOOTSTRAP/0.1" +
                 "\nRoot: " + ROOT + "\nHost: BouwerBase" +
                 "\nConnection: NOT verified. Open the existing LS GO Site and sign in. Legacy direct-host origin is optional.");
        } catch (Exception ex) {
            show("CGX file rejected: " + ex.getMessage());
        }
    }
    private String displayName(Uri uri) {
        try (Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
            if (cursor == null || !cursor.moveToFirst()) return null;
            int i = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
            return i >= 0 ? cursor.getString(i) : null;
        } catch (Exception ex) { return null; }
    }
}
